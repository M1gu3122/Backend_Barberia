"""
Modelos Pydantic para la tabla de SERVICIO_ADICIONAL.
Define los esquemas de validación y serialización para la API.
"""

from pydantic import BaseModel, ConfigDict, Field


class ServicioAdicionalBase(BaseModel):
    """Modelo base con campos comunes para operaciones CRUD."""

    id_servicio: int = Field(..., description="ID del servicio principal")
    id_adicional: int = Field(..., description="ID del servicio adicional permitido")


class ServicioAdicionalCreate(ServicioAdicionalBase):
    """Modelo para crear una nueva relación principal-adicional."""

    pass


class ServicioAdicionalResponse(ServicioAdicionalBase):
    """Modelo para la respuesta de la API."""

    model_config = ConfigDict(
        from_attributes=True  # Permite la creación desde objetos SQLAlchemy
    )