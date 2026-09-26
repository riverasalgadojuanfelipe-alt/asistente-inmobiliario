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
    except genai_errors.ServerError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gemini no disponible: {exc}",
        )
