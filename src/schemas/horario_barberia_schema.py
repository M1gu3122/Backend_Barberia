"""
Modelos Pydantic para la tabla de HORARIO_BARBERIA.
Define los esquemas de validación y serialización para la API.
"""

from datetime import time
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

DIAS_SEMANA = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]


class HorarioBarberiaBase(BaseModel):
    """Modelo base con campos comunes para operaciones CRUD."""

    id_barberia: int = Field(..., description="ID de la barbería")
    dia_semana: str = Field(..., description="Día de la semana (Lunes a Domingo)")
    hora_apertura: time = Field(..., description="Hora de apertura (HH:MM)")
    hora_cierre: time = Field(..., description="Hora de cierre (HH:MM)")


class HorarioBarberiaCreate(HorarioBarberiaBase):
    """Modelo para crear un nuevo horario."""

    pass


class HorarioBarberiaUpdate(BaseModel):
    """Modelo para actualizar un horario existente (todos los campos opcionales)."""

    dia_semana: Optional[str] = Field(None, description="Nuevo día de la semana")
    hora_apertura: Optional[time] = Field(None, description="Nueva hora de apertura")
    hora_cierre: Optional[time] = Field(None, description="Nueva hora de cierre")


class HorarioBarberiaResponse(HorarioBarberiaBase):
    """Modelo para la respuesta de la API (incluye el ID)."""

    id_horario: int = Field(..., description="ID único del horario")

    model_config = ConfigDict(
        from_attributes=True  # Permite la creación desde objetos SQLAlchemy
    )