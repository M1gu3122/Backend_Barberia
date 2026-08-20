import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from src.config.database import Base
from src.core.timezone import a_bd, ahora_bogota


class TipoNotificacion(str, enum.Enum):
    RECORDATORIO = "Recordatorio"
    CONFIRMACION = "Confirmacion"
    CANCELACION = "Cancelacion"
    REPROGRAMACION = "Reprogramacion"


class EstadoNotificacion(str, enum.Enum):
    LEIDA = "Leida"
    NO_LEIDA = "No Leida"


class Notificacion(Base):
    __tablename__ = "notificacion"

    id_notificacion = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), nullable=False)
    mensaje = Column(Text, nullable=False)
    fecha_envio = Column(
        DateTime,
        default=lambda: a_bd(ahora_bogota()),
        nullable=False,
        comment="Fecha y hora en que se envió (hora local de Colombia)",
    )

    estado = Column(
        SAEnum(EstadoNotificacion), default=EstadoNotificacion.NO_LEIDA, nullable=False
    )

    tipo = Column(
        SAEnum(TipoNotificacion), nullable=False, comment="Tipo de notificación"
    )

    # --- Claves foráneas ---
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_cita = Column(
        Integer,
        ForeignKey("cita.id_cita"),
        nullable=True,
        comment="Opcional: notificación vinculada a una cita",
    )

    # --- Relaciones ---
    # Relación 1:N con Usuario
    usuario = relationship(
        "Usuario", back_populates="notificaciones", foreign_keys=[id_usuario]
    )
    # Relación 1:N con Cita (opcional)
    cita = relationship(
        "Cita", back_populates="notificaciones", foreign_keys=[id_cita]
    )

    def __repr__(self) -> str:
        return (
            f"<Notificacion(id={self.id_notificacion}, "
            f"titulo='{self.titulo}', "
            f"tipo='{self.tipo.value}', "
            f"estado='{self.estado.value}')>"
        )

    @property
    def es_nueva(self) -> bool:
        """Retorna True si la notificación no ha sido leída"""
        return self.estado == EstadoNotificacion.NO_LEIDA

    def marcar_como_leida(self) -> None:
        """Cambia el estado a Leida"""
        self.estado = EstadoNotificacion.LEIDA

    def marcar_como_no_leida(self) -> None:
        """Cambia el estado a No Leida"""
        self.estado = EstadoNotificacion.NO_LEIDA
