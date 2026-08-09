# src/schemas/servicio_barberia_schema.py
from pydantic import BaseModel, ConfigDict
from typing import Optional


class ServicioBarberiaBase(BaseModel):
    id_barberia: int
    id_servicio: int


class ServicioBarberiaCreate(ServicioBarberiaBase):
    pass


class ServicioBarberiaUpdate(BaseModel):
    id_barberia: Optional[int] = None
    id_servicio: Optional[int] = None


class ServicioBarberiaResponse(ServicioBarberiaBase):
    model_config = ConfigDict(
        from_attributes=True
    )
