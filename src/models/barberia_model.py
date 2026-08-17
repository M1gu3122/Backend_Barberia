from sqlalchemy.orm import declarative_base
from enum import Enum
from sqlalchemy import Column, Integer, String, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.config.database import Base


class EstadoBarberia(str, Enum):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"


class Barberia(Base):
    __tablename__ = "barberia"

    id_barberia = Column(Integer, primary_key=True, index=True)
    nombre_barberia = Column(String(100), nullable=False)
    direccion = Column(String(200), nullable=False)
    telefono = Column(String(20))
    estado = Column(
        SAEnum(
            EstadoBarberia,
            values_callable=lambda enum_cls: [e.value for e in enum_cls]
        ),
        default=EstadoBarberia.ACTIVO,
        nullable=False,
    )
    #check

    
  # Relación 1:N con ServicioBarberia
    servicio_barberia = relationship(
        "ServicioBarberia", 
        back_populates="barberia",
        cascade="all, delete-orphan"
    )

    # Relación 1:N con HorarioBarberia
    horarios = relationship(
        "HorarioBarberia",
        back_populates="barberia",
        cascade="all, delete-orphan",
    )

    # Relación 1:N con FechaNoLaboral
    fechas_no_laborales = relationship(
        "FechaNoLaboral",
        back_populates="barberia",
        cascade="all, delete-orphan",
    )

    # Relación 1:N con Cita
    citas = relationship("Cita", back_populates="barberia")
    
    # Relación 1:N con Empleado
    empleados = relationship("Empleado", back_populates="barberia")
     