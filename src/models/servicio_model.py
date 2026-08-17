"""
Modelo de Servicio para la Barbería
Define los servicios que pueden ser solicitados por los clientes
"""

import enum
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.config.database import Base


class EstadoServicio(str, enum.Enum):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"


class TipoServicio(str, enum.Enum):
    PRINCIPAL = "PRINCIPAL"
    ADICIONAL = "ADICIONAL"
    COMBO = "COMBO"


class Servicio(Base):
    """
    Modelo que representa un servicio ofrecido por la barbería.
    Ejemplos: Corte de pelo, Afeitado, Baño, Coloración, etc.
    """

    __tablename__ = "servicio"

    id_servicio = Column(Integer, primary_key=True, index=True)
    nombre_servicio = Column(String(100), nullable=False)
    tipo_servicio = Column(
        SAEnum(
            TipoServicio,
            values_callable=lambda enum_class: [e.value for e in enum_class]
        ),
        nullable=False
    )
    descripcion_servicio = Column(Text, nullable=True)

    estado_servicio = Column(
        SAEnum(
            EstadoServicio,
            values_callable=lambda enum_class: [e.value for e in enum_class]
        ),
        default=EstadoServicio.ACTIVO,
        nullable=False
    )


    tiempo_estimado = Column(Integer, nullable=False, comment="Tiempo en minutos")

    precio_servicio = Column(DECIMAL(10, 2), nullable=False)
    
    
    ############################################################################################################################################

    # --- Relaciones ---
   # Relación muchos a muchos: barbería ↔ servicio
    # Relación 1:N con ServicioBarberia
    servicio_barberia = relationship(
        "ServicioBarberia",
        back_populates="servicio",
        cascade="all, delete-orphan",
    )
    
    # Relación muchos a muchos: barbero ↔ servicio
    # Relación 1:N con BarberoServicio
    barbero_servicios = relationship(
        "BarberoServicio", back_populates="servicio", cascade="all, delete-orphan"
    )

    # Relación muchos a muchos: cita ↔ servicio
    # Relación 1:N con CitaServicio
    cita_servicios = relationship(
        "CitaServicio", back_populates="servicio", cascade="all, delete-orphan"
    )

    # Relación 1:N: servicios adicionales permitidos para este servicio principal
    adicionales = relationship(
        "ServicioAdicional",
        foreign_keys="ServicioAdicional.id_servicio",
        back_populates="servicio",
        cascade="all, delete-orphan",
    )

    # Relación 1:N: servicios que permiten a este servicio como adicional
    es_adicional_de = relationship(
        "ServicioAdicional",
        foreign_keys="ServicioAdicional.id_adicional",
        back_populates="adicional",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Servicio(id={self.id_servicio}, "
            f"nombre='{self.nombre_servicio}', "
            f"precio={self.precio_servicio})>"
        )

    @property
    def es_activo(self) -> bool:
        return self.estado_servicio == EstadoServicio.ACTIVO
