"""
Modelo de la relación muchos a muchos:
Barbero ↔ Servicios
Cada barbero puede ofrecer varios servicios, y cada servicio puede estar asociado a varios barberos.
"""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.config.database import Base


class BarberoServicio(Base):
    """
    Tabla intermedia 'barbero_servicio'
    Vincula un empleado (barbero) con los servicios que puede realizar.
    """
    __tablename__ = "barbero_servicio"

    # Claves foráneas (composite primary key)
    id_usuario = Column(
        Integer,
        ForeignKey("empleado.id_usuario"),
        primary_key=True
    )
    id_servicio = Column(
        Integer,
        ForeignKey("servicio.id_servicio"),
        primary_key=True
    )
#################################################################################################
    # --- Relaciones ---
    # Relación 1:N con Empleado (barbero)
    barbero = relationship(
        "Empleado",
        back_populates="barbero_servicios"
    )
    
    # Relación 1:N con Servicio
    servicio = relationship(
        "Servicio",
        back_populates="barbero_servicios"
    )
    

    def __repr__(self) -> str:
        return (
            f"<BarberoServicio(barbero_id={self.id_usuario}, "
            f"servicio_id={self.id_servicio})>"
        )