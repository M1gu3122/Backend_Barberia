"""
Modelos Pydantic para la tabla de SERVICIOS
Define los esquemas de validación y serialización para la API.
"""

from pydantic import BaseModel, ConfigDict, Field
from enum import Enum
from decimal import Decimal
from typing import Optional

from src.models.servicio_model import EstadoServicio





class ServicioBase(BaseModel):
    """Modelo base con campos comunes para operaciones CRUD."""

    id_servicio: Optional[int] = Field(None, description="ID del servicio")
    tipo_servicio: str = Field(..., min_length=1, max_length=100, description="Nombre del servicio")
    descripcion_servicio: Optional[str] = None
    estado_servicio: EstadoServicio = Field(..., description="Estado del servicio")
    tiempo_estimado: int = Field(..., gt=0, description="Tiempo estimado en minutos")
    precio_servicio: Decimal = Field(..., gt=0, description="Precio del servicio")

    model_config = ConfigDict(
        from_attributes=True,
        # orm_mode = True  # Eliminado porque ya no es necesario en Pydantic v2
    )


class ServicioCreate(ServicioBase):
    """Modelo para crear un nuevo servicio (sin ID)."""
    pass


class ServicioUpdate(BaseModel):
    """Modelo para actualizar un servicio existente (todos los campos opcionales)."""

    tipo_servicio: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion_servicio: Optional[str] = None
    estado_servicio: Optional[EstadoServicio] = None
    tiempo_estimado: Optional[int] = Field(None, gt=0)
    precio_servicio: Optional[Decimal] = Field(None, gt=0)


class ServicioResponse(ServicioBase):
    """Modelo para la respuesta de la API."""
    pass
