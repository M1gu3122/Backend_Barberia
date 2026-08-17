"""
Modelo de la relación de compatibilidad:
Servicio principal ↔ Servicios adicionales permitidos.
Cada servicio principal puede tener varios adicionales permitidos.
"""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.config.database import Base


class ServicioAdicional(Base):
    """
    Tabla 'servicio_adicional'
    Relaciona un servicio principal (id_servicio) con un servicio
    adicional que puede combinarse con él (id_adicional).
    """

    __tablename__ = "servicio_adicional"

    # Claves foráneas (composite primary key)
    id_servicio = Column(
        Integer,
        ForeignKey("servicio.id_servicio"),
        primary_key=True,
        index=True,
    )
    id_adicional = Column(
        Integer,
        ForeignKey("servicio.id_servicio"),
        primary_key=True,
        index=True,
    )

    # --- Relaciones ---
    servicio = relationship(
        "Servicio",
        foreign_keys=[id_servicio],
        back_populates="adicionales",
    )
    adicional = relationship(
        "Servicio",
        foreign_keys=[id_adicional],
        back_populates="es_adicional_de",
    )

    def __repr__(self) -> str:
        return f"<ServicioAdicional(servicio={self.id_servicio}, adicional={self.id_adicional})>"