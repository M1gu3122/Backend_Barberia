"""
Modelos Pydantic para la tabla CITA
Define esquemas para creación, Actualización y Respuesta de Citas
"""

# src/schemas/cita_schema.py
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from typing import Optional, List
from datetime import datetime
from enum import Enum

from src.core.timezone import serializar_bogota
from src.models.cita_model import EstadoCita

class CitaBase(BaseModel):
    id_cita: Optional[int] = None
    fecha_hora: datetime
    estado_cita: EstadoCita
    id_cliente: int
    id_barbero: int
    id_barberia: int

    model_config = ConfigDict(
        from_attributes=True,
    )

class CitaCreate(CitaBase):
    ids_servicios: List[int] = Field(
        ...,
        min_length=1,
        description="IDs de los servicios de la cita (mínimo uno)",
    )

class CitaUpdate(BaseModel):
    fecha_hora: Optional[datetime] = None
    estado_cita: Optional[EstadoCita] = None
    id_cliente: Optional[int] = None
    id_barbero: Optional[int] = None
    id_barberia: Optional[int] = None
    ids_servicios: Optional[List[int]] = None

class CitaResponse(CitaBase):
    nombres: str
    apellidos: str
    correo: str

    model_config = ConfigDict(
        from_attributes=True,
    )

    @field_serializer("fecha_hora")
    def serializar_fecha_hora(self, valor: datetime) -> datetime:
        return serializar_bogota(valor)

class CitaInDB(CitaResponse):
    estado_temporal: Optional[str] = None


class CitaDetalleResponse(BaseModel):
    """Modelo para la respuesta con detalle de cita (servicios agrupados y datos del cliente y barbero)."""
    id_cita: int
    id_usuario: int
    id_barbero: int
    nombres: str
    apellidos: str
    telefono: Optional[str] = None
    correo: Optional[str] = None
    servicios: str
    tiempo_total: Optional[int] = None
    nombres_barbero: str
    apellidos_barbero: str
    fecha_hora: datetime
    estado_cita: EstadoCita

    @field_serializer("fecha_hora")
    def serializar_fecha_hora(self, valor: datetime) -> datetime:
        return serializar_bogota(valor)
