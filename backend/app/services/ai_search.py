"""
Búsqueda inteligente sobre la BD de propiedades usando Gemini.

Flujo:
  1) `extraer_filtros(query)` — Gemini convierte texto libre en filtros
     estructurados + keywords de estilo de vida.
  2) `list_properties(filtros)` — trae hasta 15 candidatos desde Postgres.
  3) `recomendar(query, candidatos, keywords)` — Gemini elige 3-5 y explica
     por qué encajan, en español natural.

Diseño:
  - Se usa `response_schema` de la SDK para forzar salida JSON parseable en
    ambas llamadas. Además, se hace un reintento si el modelo devuelve algo
    que no encaja con el schema.
  - Los IDs de propiedad se validan contra los candidatos que le enviamos, por
    si el modelo inventa un id.
  - Sin `GEMINI_API_KEY` en el entorno, el módulo falla explícitamente al
    construir el cliente.
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

logger = logging.getLogger(__name__)

MAX_CANDIDATOS = 15
MIN_RECOMENDACIONES = 3
MAX_RECOMENDACIONES = 5


class ExtractedFilters(BaseModel):
    """Salida estructurada del primer paso (extracción de filtros)."""

    ciudad: Ciudad | None = None
    tipo_operacion: TipoOperacion | None = None
    precio_min: float | None = Field(default=None, ge=0)
    precio_max: float | None = Field(default=None, ge=0)
    habitaciones_min: int | None = Field(default=None, ge=0)
    area_min: float | None = Field(default=None, ge=0)
    lifestyle_keywords: list[str] = Field(default_factory=list)


class Recomendacion(BaseModel):
    """Salida estructurada del segundo paso (recomendación por propiedad)."""

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
        raise AISearchError(
            "GEMINI_API_KEY no configurada. Añádela al .env del backend."
        )
    return genai.Client(api_key=settings.gemini_api_key)


_EXTRACTION_PROMPT = """\
Eres un asistente inmobiliario para Colombia. Tu tarea es analizar la consulta \
del usuario y extraer filtros de búsqueda estructurados.

Reglas:
- ciudad: solo una de {"cali","medellin","bogota","tulua"} o null si no se \
menciona ciudad soportada.
- tipo_operacion: "venta" si el usuario quiere comprar; "arriendo" si quiere \
alquilar/arrendar/rentar; null si no queda claro.
- precio_min / precio_max: en pesos colombianos (COP). Convierte expresiones \
como "800 millones" -> 800000000, "2 mil millones" -> 2000000000, "1.5M" -> \
1500000. Si dice "máximo X" usa precio_max=X; "mínimo X" usa precio_min=X. \
Si no hay presupuesto, deja ambos en null.
- habitaciones_min: número mínimo de habitaciones si el usuario lo especifica.
- area_min: metros cuadrados mínimos si se especifica.
- lifestyle_keywords: lista corta (máx 8) de palabras/frases del usuario que \
describen ESTILO DE VIDA o CARACTERÍSTICAS deseadas (ej: "tranquilo", \
"cerca de parques", "buena luz", "amoblado", "seguro", "con vista"). \
No incluyas cifras, ciudad ni tipo de operación aquí.

Consulta del usuario:
\"\"\"{query}\"\"\"

Devuelve SOLO un objeto JSON con esos campos. Si un campo no aplica, usa null \
(o lista vacía para lifestyle_keywords).
"""


_ADVISOR_SYSTEM_PROMPT = """\
Eres un asesor inmobiliario colombiano, honesto y con criterio. Recibes:
  1) La consulta original del usuario.
  2) Palabras clave de estilo de vida que priorizó.
  3) Una lista de propiedades candidatas con sus datos (id, ciudad, barrio, \
precio, habitaciones, baños, área, descripción).

Tu tarea:
- Elegir entre {min_reco} y {max_reco} propiedades que MEJOR encajen con lo \
que el usuario pidió.
- Para cada una, escribir en 1-2 frases en español natural POR QUÉ encaja, \
citando pistas concretas de la descripción o el barrio (no inventes datos).
- Si una descripción no soporta un keyword del usuario (ej: piden "cerca de \
parques" y la descripción no lo menciona), no lo afirmes; sé honesto y \
mencionalo como algo a verificar.
- No repitas la propiedad. No inventes ids. Usa solo los ids que se te dan.

Devuelve un JSON con la forma:
{{ "recomendaciones": [{{"property_id": <int>, "razon": "<texto>"}}] }}
"""


def _generate_with_retry(
    *,
    contents: str,
    config: genai_types.GenerateContentConfig,
    max_attempts: int = 3,
) -> Any:
    """Llama a generate_content con backoff frente a 5xx/UNAVAILABLE."""
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
            logger.warning("Gemini 5xx (%s), intento %s/%s — espero %.1fs",
                           getattr(exc, "code", "?"), intento, max_attempts, wait)
            time.sleep(wait)
    assert last is not None
    raise last


def _extract_json_from_response(resp: Any) -> dict:
    """Extrae el dict del response de Gemini, tolerando texto con ruido."""
    parsed = getattr(resp, "parsed", None)
    if parsed is not None:
        if isinstance(parsed, BaseModel):
            return parsed.model_dump()
        if isinstance(parsed, dict):
            return parsed
    text = (resp.text or "").strip()
    if not text:
        raise ValueError("Respuesta vacía de Gemini")
    # Los modelos a veces envuelven en ```json ... ```
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def extraer_filtros(query: str) -> ExtractedFilters:
    """Llama a Gemini para convertir texto libre en filtros estructurados."""
    prompt = _EXTRACTION_PROMPT.replace("{query}", query)
    config = genai_types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ExtractedFilters,
        temperature=0.0,
    )

    ultimo_error: Exception | None = None
    for intento in (1, 2):
        try:
            resp = _generate_with_retry(contents=prompt, config=config)
            data = _extract_json_from_response(resp)
            return ExtractedFilters.model_validate(data)
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            ultimo_error = exc
            logger.warning("Gemini extract_filtros intento %s falló: %s", intento, exc)

    raise AISearchError(
        f"Gemini no devolvió filtros parseables tras 2 intentos: {ultimo_error}"
    )


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


def recomendar(
    query: str,
    candidatos: list[Property],
    keywords: list[str],
) -> list[Recomendacion]:
    """Llama a Gemini para elegir 3-5 propiedades y explicar el por qué."""
    if not candidatos:
        return []

    payload = {
        "consulta_original": query,
        "estilo_de_vida_deseado": keywords,
        "candidatos": [_property_to_prompt_dict(p) for p in candidatos],
    }

    system = _ADVISOR_SYSTEM_PROMPT.format(
        min_reco=MIN_RECOMENDACIONES, max_reco=MAX_RECOMENDACIONES
    )
    contents = (
        "DATOS_DE_ENTRADA:\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )

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


def _filters_desde_extraidos(f: ExtractedFilters) -> PropertyFilter:
    return PropertyFilter(
        ciudad=f.ciudad,
        tipo_operacion=f.tipo_operacion,
        precio_min=f.precio_min,
        precio_max=f.precio_max,
        habitaciones_min=f.habitaciones_min,
        area_min=f.area_min,
    )


def buscar_inteligente(db: Session, query: str) -> BuscarResponse:
    """Punto de entrada del endpoint POST /buscar."""
    query = query.strip()
    if not query:
        raise AISearchError("La consulta está vacía.")

    filtros = extraer_filtros(query)
    db_filter = _filters_desde_extraidos(filtros)
    candidatos = property_service.list_properties(
        db, db_filter, limit=MAX_CANDIDATOS, offset=0
    )

    if not candidatos:
        return BuscarResponse(
            query=query,
            filtros_extraidos=filtros,
            total_candidatos=0,
            recomendaciones=[],
            mensaje=(
                "No se encontraron propiedades que cumplan con los criterios "
                "de tu consulta. Prueba ampliando el presupuesto, cambiando la "
                "ciudad o relajando el mínimo de habitaciones/área."
            ),
        )

    recos = recomendar(query, candidatos, filtros.lifestyle_keywords)
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
        filtros_extraidos=filtros,
        total_candidatos=len(candidatos),
        recomendaciones=salida,
    )
