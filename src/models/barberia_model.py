from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.config.database import Base
class Barberia(Base):
    __tablename__ = "barberia"

    id_barberia = Column(Integer, primary_key=True, index=True)
    nombre_barberia = Column(String(100), nullable=False)
    direccion = Column(String(200), nullable=False)
    telefono = Column(String(20))
    horarios_atencion = Column(String(100))
    #check

    
  # Relación 1:N con ServicioBarberia
    servicio_barberia = relationship(
        "ServicioBarberia", 
        back_populates="barberia",
        cascade="all, delete-orphan"
    )

    # Relación 1:N con Cita
    citas = relationship("Cita", back_populates="barberia")
    
    # Relación 1:N con Empleado
    empleados = relationship("Empleado", back_populates="barberia")
     