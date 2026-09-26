from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.property import Ciudad, TipoOperacion
from app.schemas.property import PropertyCreate, PropertyFilter, PropertyRead
from app.services import property_service

router = APIRouter(prefix="/propiedades", tags=["propiedades"])


@router.post("", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(payload: PropertyCreate, db: Session = Depends(get_db)) -> PropertyRead:
    prop = property_service.create_property(db, payload)
    return PropertyRead.model_validate(prop)


@router.get("", response_model=list[PropertyRead])
def list_properties(
    ciudad: Ciudad | None = None,
    tipo_operacion: TipoOperacion | None = None,
    precio_min: float | None = Query(default=None, ge=0),
    precio_max: float | None = Query(default=None, ge=0),
    habitaciones_min: int | None = Query(default=None, ge=0),
    banos_min: int | None = Query(default=None, ge=0),
    area_min: float | None = Query(default=None, ge=0),
    barrio: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[PropertyRead]:
    filters = PropertyFilter(
        ciudad=ciudad,
        tipo_operacion=tipo_operacion,
        precio_min=precio_min,
        precio_max=precio_max,
        habitaciones_min=habitaciones_min,
        banos_min=banos_min,
        area_min=area_min,
        barrio=barrio,
    )
    props = property_service.list_properties(db, filters, limit=limit, offset=offset)
    return [PropertyRead.model_validate(p) for p in props]


@router.get("/{property_id}", response_model=PropertyRead)
def get_property(property_id: int, db: Session = Depends(get_db)) -> PropertyRead:
    prop = property_service.get_property(db, property_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    return PropertyRead.model_validate(prop)
