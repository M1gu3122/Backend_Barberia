"""
Modelo de la relación muchos a muchos:
Cita ↔ Servicios
Cada cita puede incluir varios servicios, y cada servicio puede estar en varias citas.
"""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.config.database import Base


class CitaServicio(Base):
    """
    Tabla intermedia 'citas_servicios'
    Vincula una cita con los servicios incluidos en ella.
    """
    __tablename__ = "cita_servicio"

    # Claves foráneas (composite primary key)
    id_cita = Column(
        Integer,
        ForeignKey("cita.id_cita"),
        primary_key=True
    )
    id_servicio = Column(
        Integer,
        ForeignKey("servicio.id_servicio"),
        primary_key=True
    )

    # --- Relaciones ---
    # Relación 1:N con Cita
    cita = relationship(
        "Cita",
        back_populates="servicios"
    )
    
    # Relación 1:N con Servicio
    servicio = relationship(
        "Servicio",
        back_populates="cita_servicios"
    )

    def __repr__(self) -> str:
        return (
            f"<CitaServicio(cita_id={self.id_cita}, "
            f"servicio_id={self.id_servicio})>"
        )