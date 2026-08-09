# src/schemas/barbero_servicio_schema.py
from pydantic import BaseModel, ConfigDict
from typing import Optional


class BarberoServicioBase(BaseModel):
    id_usuario: int
    id_servicio: int


class BarberoServicioCreate(BarberoServicioBase):
    pass


class BarberoServicioUpdate(BaseModel):
    id_usuario: Optional[int] = None
    id_servicio: Optional[int] = None


class BarberoServicioResponse(BarberoServicioBase):
    model_config = ConfigDict(
        from_attributes=True
    )
