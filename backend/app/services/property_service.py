from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.property import Property
from app.schemas.property import PropertyCreate, PropertyFilter


def create_property(db: Session, payload: PropertyCreate) -> Property:
    prop = Property(**payload.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


def get_property(db: Session, property_id: int) -> Property | None:
    return db.get(Property, property_id)


def list_properties(
    db: Session,
    filters: PropertyFilter,
    limit: int = 50,
    offset: int = 0,
) -> list[Property]:
    stmt = select(Property)

    if filters.ciudad is not None:
        stmt = stmt.where(Property.ciudad == filters.ciudad)
    if filters.tipo_operacion is not None:
        stmt = stmt.where(Property.tipo_operacion == filters.tipo_operacion)
    if filters.precio_min is not None:
        stmt = stmt.where(Property.precio >= filters.precio_min)
    if filters.precio_max is not None:
        stmt = stmt.where(Property.precio <= filters.precio_max)
    if filters.habitaciones_min is not None:
        stmt = stmt.where(Property.habitaciones >= filters.habitaciones_min)
    if filters.banos_min is not None:
        stmt = stmt.where(Property.banos >= filters.banos_min)
    if filters.area_min is not None:
        stmt = stmt.where(Property.area_m2 >= filters.area_min)
    if filters.barrio:
        stmt = stmt.where(Property.barrio.ilike(f"%{filters.barrio}%"))

    stmt = stmt.order_by(Property.fecha_extraccion.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())
