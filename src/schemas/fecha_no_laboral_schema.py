"""
Modelos Pydantic para la tabla de FECHA_NO_LABORAL.
Define los esquemas de validación y serialización para la API.
"""

from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class FechaNoLaboralBase(BaseModel):
    """Modelo base con campos comunes para operaciones CRUD."""

    id_barberia: int = Field(..., description="ID de la barbería")
    fecha: date = Field(..., description="Fecha en la que no se atiende (YYYY-MM-DD)")
    motivo: Optional[str] = Field(None, description="Motivo del cierre (opcional)")


class FechaNoLaboralCreate(FechaNoLaboralBase):
    """Modelo para crear una nueva fecha no laboral."""

    pass


class FechaNoLaboralUpdate(BaseModel):
    """Modelo para actualizar una fecha no laboral (todos los campos opcionales)."""

    fecha: Optional[date] = Field(None, description="Nueva fecha de cierre")
    motivo: Optional[str] = Field(None, description="Nuevo motivo del cierre")


class FechaNoLaboralResponse(FechaNoLaboralBase):
    """Modelo para la respuesta de la API (incluye el ID)."""

    id_fecha_no_laboral: int = Field(..., description="ID único del registro")

    model_config = ConfigDict(
        from_attributes=True  # Permite la creación desde objetos SQLAlchemy
    )