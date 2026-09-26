from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.property import Ciudad, TipoOperacion


class PropertyBase(BaseModel):
    ciudad: Ciudad
    tipo_operacion: TipoOperacion
    precio: float = Field(gt=0)
    habitaciones: int = Field(ge=0)
    banos: int = Field(ge=0)
    area_m2: float = Field(gt=0)
    barrio: str | None = None
    descripcion: str | None = None
    fuente: str = Field(min_length=1, max_length=120)
    property_type: str | None = Field(default=None, max_length=64)
    url_original: str | None = Field(default=None, max_length=1024)
    image_url: str | None = Field(default=None, max_length=1024)


class PropertyCreate(PropertyBase):
    pass


class PropertyRead(PropertyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha_extraccion: datetime


class PropertyFilter(BaseModel):
    ciudad: Ciudad | None = None
    tipo_operacion: TipoOperacion | None = None
    precio_min: float | None = Field(default=None, ge=0)
    precio_max: float | None = Field(default=None, ge=0)
    habitaciones_min: int | None = Field(default=None, ge=0)
    banos_min: int | None = Field(default=None, ge=0)
    area_min: float | None = Field(default=None, ge=0)
    barrio: str | None = None
