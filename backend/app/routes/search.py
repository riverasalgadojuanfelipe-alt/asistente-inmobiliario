import re
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from google.genai import errors as genai_errors
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.services.ai_search import (
    AISearchError,
    BuscarResponse,
    buscar_inteligente,
)

router = APIRouter(prefix="/buscar", tags=["buscar"])

MAX_QUERY_LENGTH = 500

_RETRY_DELAY_RE = re.compile(r"retry in ([\d.]+)s", re.IGNORECASE)


class BuscarRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=MAX_QUERY_LENGTH,
        description="Consulta en lenguaje natural (máx. 500 chars).",
    )
    idioma: Literal["es", "en"] = Field(
        default="es",
        description="Idioma de la respuesta del asesor: 'es' o 'en'.",
    )


def _friendly_client_error(exc: genai_errors.ClientError) -> tuple[int, str]:
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    raw = str(exc)
    if code == 429 or "RESOURCE_EXHAUSTED" in raw:
        m = _RETRY_DELAY_RE.search(raw)
        wait_txt = f"Intenta de nuevo en ~{int(float(m.group(1)))}s." if m else (
            "La cuota se resetea al final del día (hora del Pacífico)."
        )
        return (
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Se agotó la cuota gratuita diaria del asesor. {wait_txt}",
        )
    if code == 404:
        return (
            status.HTTP_502_BAD_GATEWAY,
            "El modelo configurado no está disponible. Revisa GEMINI_MODEL.",
        )
    return (status.HTTP_502_BAD_GATEWAY, f"Error del asesor: {raw[:200]}")


@router.post(
    "",
    response_model=BuscarResponse,
    summary="Búsqueda inteligente en lenguaje natural",
)
@limiter.limit("10/minute")
def buscar(
    request: Request,  # requerido por slowapi para obtener la IP del cliente
    body: BuscarRequest,
    db: Session = Depends(get_db),
) -> BuscarResponse:
    q = body.query.strip()
    if not q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La consulta está vacía. Escribe algo como 'apartamento tranquilo en Cali'.",
        )

    try:
        return buscar_inteligente(db, q, idioma=body.idioma)
    except AISearchError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    except genai_errors.ClientError as exc:
        code, msg = _friendly_client_error(exc)
        raise HTTPException(status_code=code, detail=msg)
    except genai_errors.ServerError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gemini no disponible: {exc}",
        )
