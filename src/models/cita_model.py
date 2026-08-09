"""
Modelo de Cita para la Barbería
Representa la reserva de un cliente con un barbero en una fecha/hora.
"""

from enum import Enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.config.database import Base


# Definición del Enum para estado de cita
class EstadoCita(str, Enum):
    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    CANCELADA = "Cancelada"
    COMPLETADA = "Completada"


class Cita(Base):
    """
    Modelo que representa una cita (reserva) de un cliente
    con un barbero en una barbería específica.
    """

    __tablename__ = "cita"

    id_cita = Column(Integer, primary_key=True, index=True)
    fecha_hora = Column(DateTime, nullable=False)

    estado_cita = Column(
        SAEnum(
            EstadoCita,
            values_callable=lambda enum: [e.value for e in enum]
        ),
        nullable=False,
        default=EstadoCita.PENDIENTE
    )

    # --- Claves foráneas ---
    id_cliente = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_barbero = Column(Integer, ForeignKey("empleado.id_usuario"), nullable=False)
    id_barberia = Column(Integer, ForeignKey("barberia.id_barberia"), nullable=False)

    ######################################################################################################################

    # --- Relaciones ---
    # Relación 1:N con Usuario (cliente)
    cliente = relationship("Usuario", back_populates="citas")
    # Relación 1:N con Empleado (barbero)
    barbero = relationship("Empleado", back_populates="citas")
    # Relación 1:N con Barberia
    barberia = relationship("Barberia", back_populates="citas")
    # Relación muchos a muchos con Servicio a través de CitaServicio
    servicios = relationship(
        "CitaServicio", back_populates="cita", cascade="all, delete-orphan"
    )
    # Relación 1:N con Notificacion
    notificaciones = relationship(
        "Notificacion", back_populates="cita", cascade="all, delete-orphan"
    )
    # ✅ Métodos de negocio
    @property
    def esta_pendiente(self) -> bool:
        return self.estado_cita == EstadoCita.PENDIENTE

    @property
    def esta_confirmada(self) -> bool:
        return self.estado_cita == EstadoCita.CONFIRMADA

    def confirmar(self) -> None:
        """Cambia el estado a Confirmada"""
        self.estado_cita = EstadoCita.CONFIRMADA

    def cancelar(self) -> None:
        """Cambia el estado a Cancelada"""
        self.estado_cita = EstadoCita.CANCELADA

    def completar(self) -> None:
        """Cambia el estado a Completada"""
        self.estado_cita = EstadoCita.COMPLETADA


    def __repr__(self) -> str:
        return (
            f"<Cita(id={self.id_cita}, "
            f"fecha={self.fecha_hora}, "
            f"estado='{self.estado_cita.value}', "
            f"barbero_id={self.id_barbero})>"
        )
