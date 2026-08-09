from src.config.database import Base
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship


class ServicioBarberia(Base):
    __tablename__ = "servicios_barberia"

    id_barberia = Column(Integer, ForeignKey("barberia.id_barberia"), primary_key=True)
    id_servicio = Column(Integer, ForeignKey("servicio.id_servicio"), primary_key=True)
#Relaciones
  # ✅ Corregido
    barberia = relationship(
        "Barberia", back_populates="servicio_barberia"
    )
    
    # ✅ Corregido
    servicio = relationship(
        "Servicio", back_populates="servicio_barberia")