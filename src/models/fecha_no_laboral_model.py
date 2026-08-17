"""
Modelo de FechaNoLaboral para la Barbería
Representa los días concretos en los que una barbería NO atiende
(festivos, cierres, mantenimiento, etc.).
"""

from datetime import date
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from src.config.database import Base


class FechaNoLaboral(Base):
    """
    Tabla 'fecha_no_laboral'
    Cada registro indica que una barbería cierra una fecha concreta.
    """

    __tablename__ = "fecha_no_laboral"

    id_fecha_no_laboral = Column(Integer, primary_key=True, index=True)
    id_barberia = Column(
        Integer,
        ForeignKey("barberia.id_barberia"),
        nullable=False,
        index=True,
    )
    fecha = Column(Date, nullable=False)
    motivo = Column(String(200), nullable=True)

    # --- Relaciones ---
    barberia = relationship("Barberia", back_populates="fechas_no_laborales")

    def __repr__(self) -> str:
        return (
            f"<FechaNoLaboral(id={self.id_fecha_no_laboral}, "
            f"barberia={self.id_barberia}, "
            f"fecha={self.fecha})>"
        )