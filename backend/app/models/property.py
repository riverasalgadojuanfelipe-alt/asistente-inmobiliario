from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Ciudad(str, Enum):
    CALI = "cali"
    MEDELLIN = "medellin"
    BOGOTA = "bogota"
    TULUA = "tulua"


class TipoOperacion(str, Enum):
    VENTA = "venta"
    ARRIENDO = "arriendo"


class Property(Base):
    __tablename__ = "propiedades"
    __table_args__ = (
        UniqueConstraint("url_original", name="uq_propiedades_url_original"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ciudad: Mapped[Ciudad] = mapped_column(
        SAEnum(Ciudad, name="ciudad_enum", native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    tipo_operacion: Mapped[TipoOperacion] = mapped_column(
        SAEnum(TipoOperacion, name="tipo_operacion_enum", native_enum=False, length=16),
        nullable=False,
        index=True,
    )

    precio: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, index=True)
    habitaciones: Mapped[int] = mapped_column(Integer, nullable=False)
    banos: Mapped[int] = mapped_column(Integer, nullable=False)
    area_m2: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    barrio: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    fuente: Mapped[str] = mapped_column(String(120), nullable=False)
    property_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    url_original: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    fecha_extraccion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
