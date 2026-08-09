"""
Modelos Pydantic para la tabla CITA
Define esquemas para creación, Actualización y Respuesta de Citas
"""

# src/schemas/cita_schema.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

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
    pass

class CitaUpdate(BaseModel):
    fecha_hora: Optional[datetime] = None
    estado_cita: Optional[EstadoCita] = None
    id_cliente: Optional[int] = None
    id_barbero: Optional[int] = None
    id_barberia: Optional[int] = None

class CitaResponse(CitaBase):
    

    model_config = ConfigDict(
        from_attributes=True,
    )

class CitaInDB(CitaResponse):
    estado_temporal: Optional[str] = None
