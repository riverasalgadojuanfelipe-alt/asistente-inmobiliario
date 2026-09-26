"""
Búsqueda inteligente sobre la BD de propiedades — UN solo llamado a Gemini.

Flujo (optimizado para cuota gratuita de Gemini):
  1) `query_parser.parse_query(query)` — extrae filtros estructurados
     (ciudad, tipo_operacion, rangos, mínimos) con REGLAS EN PYTHON, sin LLM.
  2) `property_service.list_properties(filtros)` — trae hasta 15 candidatos.
  3) `recomendar(query, candidatos)` — UNA sola llamada a Gemini con la
     consulta original + los candidatos ya filtrados. El modelo decide
     3-5 y explica cada una en español natural, leyendo directamente los
     matices de estilo de vida del texto libre del usuario.

Cambio vs. versión anterior:
  Antes: 2 llamadas a Gemini por búsqueda (extractor + advisor).
  Ahora: 1 llamada. Reduce a la mitad el consumo del free tier.
"""

from __future__ import annotations

import json
import logging
import time
from decimal import Decimal
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.property import Ciudad, Property, TipoOperacion
from app.schemas.property import PropertyFilter, PropertyRead
from app.services import property_service
from app.services.query_parser import ParsedFilters, parse_query

logger = logging.getLogger(__name__)

MAX_CANDIDATOS = 15
MIN_RECOMENDACIONES = 3
MAX_RECOMENDACIONES = 5


class ExtractedFilters(BaseModel):
    """Filtros extraídos (por reglas) — se devuelve al cliente para UI/debug."""

    ciudad: Ciudad | None = None
    tipo_operacion: TipoOperacion | None = None
    precio_min: float | None = Field(default=None, ge=0)
    precio_max: float | None = Field(default=None, ge=0)
    habitaciones_min: int | None = Field(default=None, ge=0)
    area_min: float | None = Field(default=None, ge=0)


class Recomendacion(BaseModel):
    property_id: int
    razon: str


class RecomendacionesResponse(BaseModel):
    recomendaciones: list[Recomendacion]


class PropiedadRecomendada(BaseModel):
    propiedad: PropertyRead
    razon: str


class BuscarResponse(BaseModel):
    query: str
    filtros_extraidos: ExtractedFilters
    total_candidatos: int
    recomendaciones: list[PropiedadRecomendada]
    mensaje: str | None = None


class AISearchError(RuntimeError):
    """Error irrecuperable de la capa de búsqueda inteligente."""


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise AISearchError("GEMINI_API_KEY no configurada. Añádela al .env del backend.")
    return genai.Client(api_key=settings.gemini_api_key)


def _generate_with_retry(
    *,
    contents: str,
    config: genai_types.GenerateContentConfig,
    max_attempts: int = 3,
) -> Any:
    """generate_content con backoff frente a 5xx / UNAVAILABLE."""
    client = _get_client()
    model = get_settings().gemini_model
    last: Exception | None = None
    for intento in range(1, max_attempts + 1):
        try:
            return client.models.generate_content(
                model=model, contents=contents, config=config
            )
        except genai_errors.ServerError as exc:
            last = exc
            wait = 1.5 * intento
            logger.warning(
                "Gemini 5xx (%s), intento %s/%s — espero %.1fs",
                getattr(exc, "code", "?"), intento, max_attempts, wait,
            )
            time.sleep(wait)
    assert last is not None
    raise last


def _extract_json_from_response(resp: Any) -> dict:
    parsed = getattr(resp, "parsed", None)
    if parsed is not None:
        if isinstance(parsed, BaseModel):
            return parsed.model_dump()
        if isinstance(parsed, dict):
            return parsed
    text = (resp.text or "").strip()
    if not text:
        raise ValueError("Respuesta vacía de Gemini")
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def _property_to_prompt_dict(p: Property) -> dict:
    return {
        "id": p.id,
        "ciudad": p.ciudad.value if hasattr(p.ciudad, "value") else str(p.ciudad),
        "tipo_operacion": p.tipo_operacion.value
        if hasattr(p.tipo_operacion, "value")
        else str(p.tipo_operacion),
        "property_type": p.property_type,
        "barrio": p.barrio,
        "precio_cop": float(p.precio) if isinstance(p.precio, Decimal) else p.precio,
        "habitaciones": p.habitaciones,
        "banos": p.banos,
        "area_m2": float(p.area_m2) if isinstance(p.area_m2, Decimal) else p.area_m2,
        "descripcion": (p.descripcion or "")[:600],
    }


_ADVISOR_SYSTEM_PROMPT = """\
Eres un asesor inmobiliario colombiano, honesto y con criterio. Recibes:
  1) La consulta ORIGINAL del usuario (léela completa: incluye pistas de
     estilo de vida, preferencias, contexto).
  2) Una lista de propiedades candidatas ya filtradas por criterios básicos
     (ciudad, precio, habitaciones, área) con sus datos.

Tu tarea:
- Elegir entre {min_reco} y {max_reco} propiedades que MEJOR encajen con lo
  que el usuario pidió, prestando atención especial a los matices de estilo
  de vida que menciona (tranquilidad, luz, cercanía a algo, moderno, familiar,
  vista, seguridad, amoblado, etc.).
- Para cada una, escribir en 1-2 frases en español natural POR QUÉ encaja,
  citando pistas concretas de la descripción o el barrio (no inventes datos).
- Si una descripción no soporta un matiz del usuario (p.ej. piden "cerca de
  parques" y la descripción no lo menciona), sé honesto: menciónalo como
  algo a verificar en la visita, no lo afirmes.
- No repitas propiedades. No inventes ids. Usa SOLO los ids que se te dan.

Devuelve un JSON con la forma exacta:
{{ "recomendaciones": [{{"property_id": <int>, "razon": "<texto>"}}] }}
"""


def _filters_from_parsed(p: ParsedFilters) -> PropertyFilter:
    return PropertyFilter(
        ciudad=p.ciudad,
        tipo_operacion=p.tipo_operacion,
        precio_min=p.precio_min,
        precio_max=p.precio_max,
        habitaciones_min=p.habitaciones_min,
        area_min=p.area_min,
    )


def _parsed_to_public(p: ParsedFilters) -> ExtractedFilters:
    return ExtractedFilters(
        ciudad=p.ciudad,
        tipo_operacion=p.tipo_operacion,
        precio_min=p.precio_min,
        precio_max=p.precio_max,
        habitaciones_min=p.habitaciones_min,
        area_min=p.area_min,
    )


def recomendar(query: str, candidatos: list[Property]) -> list[Recomendacion]:
    """Única llamada a Gemini: recibe consulta original + candidatos → recos."""
    if not candidatos:
        return []

    payload = {
        "consulta_original": query,
        "candidatos": [_property_to_prompt_dict(p) for p in candidatos],
    }
    system = _ADVISOR_SYSTEM_PROMPT.format(
        min_reco=MIN_RECOMENDACIONES, max_reco=MAX_RECOMENDACIONES
    )
    contents = "DATOS_DE_ENTRADA:\n" + json.dumps(payload, ensure_ascii=False, indent=2)

    config = genai_types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        response_schema=RecomendacionesResponse,
        temperature=0.3,
    )

    valid_ids = {p.id for p in candidatos}
    ultimo_error: Exception | None = None
    for intento in (1, 2):
        try:
            resp = _generate_with_retry(contents=contents, config=config)
            data = _extract_json_from_response(resp)
            parsed = RecomendacionesResponse.model_validate(data)
            filtradas = [r for r in parsed.recomendaciones if r.property_id in valid_ids]
            if not filtradas:
                raise ValueError("Gemini devolvió recomendaciones con ids no válidos")
            return filtradas[:MAX_RECOMENDACIONES]
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            ultimo_error = exc
            logger.warning("Gemini recomendar intento %s falló: %s", intento, exc)

    raise AISearchError(
        f"Gemini no devolvió recomendaciones parseables tras 2 intentos: {ultimo_error}"
    )


def buscar_inteligente(db: Session, query: str) -> BuscarResponse:
    """Punto de entrada del endpoint POST /buscar."""
    query = query.strip()
    if not query:
        raise AISearchError("La consulta está vacía.")

    # Paso 1: extracción por reglas (Python puro, sin cuota de Gemini)
    parsed = parse_query(query)
    filtros_pub = _parsed_to_public(parsed)

    # Paso 2: consulta a la BD
    candidatos = property_service.list_properties(
        db, _filters_from_parsed(parsed), limit=MAX_CANDIDATOS, offset=0
    )

    if not candidatos:
        return BuscarResponse(
            query=query,
            filtros_extraidos=filtros_pub,
            total_candidatos=0,
            recomendaciones=[],
            mensaje=(
                "No se encontraron propiedades que cumplan con los criterios "
                "de tu consulta. Prueba ampliando el presupuesto, cambiando la "
                "ciudad o relajando el mínimo de habitaciones/área."
            ),
        )

    # Paso 3: UNA llamada a Gemini con el texto original + candidatos
    recos = recomendar(query, candidatos)
    by_id = {p.id: p for p in candidatos}
    salida = [
        PropiedadRecomendada(
            propiedad=PropertyRead.model_validate(by_id[r.property_id]),
            razon=r.razon,
        )
        for r in recos
        if r.property_id in by_id
    ]

    return BuscarResponse(
        query=query,
        filtros_extraidos=filtros_pub,
        total_candidatos=len(candidatos),
        recomendaciones=salida,
    )
