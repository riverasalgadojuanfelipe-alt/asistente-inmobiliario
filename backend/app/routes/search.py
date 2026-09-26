import re

from fastapi import APIRouter, Body, Depends, HTTPException, status
from google.genai import errors as genai_errors
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.ai_search import (
    AISearchError,
    BuscarResponse,
    buscar_inteligente,
)

router = APIRouter(prefix="/buscar", tags=["buscar"])


_RETRY_DELAY_RE = re.compile(r"retry in ([\d.]+)s", re.IGNORECASE)


def _friendly_client_error(exc: genai_errors.ClientError) -> tuple[int, str]:
    """
    Traduce un ClientError de Gemini a (status_code, mensaje humano).
    Se enfoca en el caso 429 (quota exhausted) del tier gratuito.
    """
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
def buscar(
    query: str = Body(
        ...,
        media_type="text/plain",
        examples=[
            "Quiero un apartamento tranquilo en Cali, cerca de parques, "
            "con buena luz, máximo 800 millones."
        ],
    ),
    db: Session = Depends(get_db),
) -> BuscarResponse:
    try:
        return buscar_inteligente(db, query)
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
