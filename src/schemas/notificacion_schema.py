"""
Modelos Pydantic para la tabla NOTIFICACIONES.
Define esquemas para crear, actualizar y responder notificaciones.
"""

from pydantic import BaseModel, ConfigDict, Field, field_serializer
from typing import Optional, List
from datetime import datetime
from enum import Enum

from src.core.timezone import serializar_bogota


class TipoNotificacion(str, Enum):
    RECORDATORIO = "Recordatorio"
    CONFIRMACION = "Confirmacion"
    CANCELACION = "Cancelacion"
    REPROGRAMACION = "Reprogramacion"


class EstadoNotificacion(str, Enum):
    LEIDA = "Leida"
    NO_LEIDA = "No Leida"


class NotificacionBase(BaseModel):
    """Modelo base con campos comunes para notificaciones."""

    id_notificacion: int
    titulo: str = Field(..., min_length=1, max_length=100)
    mensaje: str = Field(..., min_length=1)
    fecha_envio: datetime
    estado: EstadoNotificacion
    tipo: TipoNotificacion
    id_usuario: int
    id_cita: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True,
        # orm_mode = True  # Eliminado porque ya no es necesario en Pydantic v2
    )


class NotificacionCreate(BaseModel):
    """Modelo para crear nuevas notificaciones."""

    titulo: str = Field(..., min_length=1, max_length=100)
    mensaje: str = Field(..., min_length=1)
    tipo: TipoNotificacion
    id_usuario: int
    id_cita: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True,
        # orm_mode = True  # Eliminado porque ya no es necesario en Pydantic v2
    )


class NotificacionUpdate(BaseModel):
    """Modelo para actualizar notificaciones (campos opcionales)."""

    titulo: Optional[str] = Field(None, min_length=1, max_length=100)
    mensaje: Optional[str] = None
    estado: Optional[EstadoNotificacion] = None
    id_cita: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True,
        # orm_mode = True  # Eliminado porque ya no es necesario en Pydantic v2
    )


class NotificacionResponse(NotificacionBase):
    """Modelo para respuestas API."""

    @field_serializer("fecha_envio")
    def serializar_fecha_envio(self, valor: datetime) -> datetime:
        return serializar_bogota(valor)


class NotificacionInDB(NotificacionResponse):
    """Modelo interno con estado temporal."""

    revisada_por: Optional[str] = None
