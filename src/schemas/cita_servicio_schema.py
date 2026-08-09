# src/schemas/cita_servicio_schema.py
from pydantic import BaseModel, ConfigDict
from typing import Optional


class CitaServicioBase(BaseModel):
    id_cita: int
    id_servicio: int


class CitaServicioCreate(CitaServicioBase):
    pass


class CitaServicioUpdate(BaseModel):
    id_cita: Optional[int] = None
    id_servicio: Optional[int] = None


class CitaServicioResponse(CitaServicioBase):
    model_config = ConfigDict(
        from_attributes=True
    )
