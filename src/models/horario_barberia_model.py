"""
Modelo de HorarioBarberia para la Barbería
Representa los horarios de atención de una barbería por día de la semana.
"""

from sqlalchemy import Column, Integer, String, Time, ForeignKey
from sqlalchemy.orm import relationship
from src.config.database import Base


class HorarioBarberia(Base):
    """
    Tabla 'horario_barberia'
    Define los horarios de atención por día (apertura y cierre).
    """

    __tablename__ = "horario_barberia"

    id_horario = Column(Integer, primary_key=True, index=True)
    id_barberia = Column(
        Integer,
        ForeignKey("barberia.id_barberia"),
        nullable=False,
        index=True,
    )
    dia_semana = Column(String(20), nullable=False)
    hora_apertura = Column(Time, nullable=False)
    hora_cierre = Column(Time, nullable=False)

    # --- Relaciones ---
    barberia = relationship("Barberia", back_populates="horarios")

    def __repr__(self) -> str:
        return (
            f"<HorarioBarberia(id={self.id_horario}, "
            f"dia='{self.dia_semana}', "
            f"{self.hora_apertura}-{self.hora_cierre})>"
        )