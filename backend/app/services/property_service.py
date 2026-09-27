from sqlalchemy import func, select
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


def count_properties(db: Session, filters: PropertyFilter) -> int:
    """Cuenta total de propiedades que matchean los filtros (sin limit)."""
    stmt = select(func.count()).select_from(Property)

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

    return int(db.execute(stmt).scalar_one() or 0)


def list_properties(
    db: Session,
    filters: PropertyFilter,
    limit: int = 50,
    offset: int = 0,
    random_order: bool = False,
) -> list[Property]:
    """
    Lista propiedades filtradas.

    `random_order=True` selecciona una muestra aleatoria del set filtrado (usa
    RANDOM() del motor). Se usa desde la busqueda inteligente para no darle
    siempre los mismos candidatos a Gemini en consultas similares y para mezclar
    fuentes (Fincaraiz / Metrocuadrado) de forma pareja. En el listado publico
    /propiedades se deja el default (fecha_extraccion desc + offset paginable).
    """
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

    if random_order:
        stmt = stmt.order_by(func.random()).limit(limit)
    else:
        stmt = stmt.order_by(Property.fecha_extraccion.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())
