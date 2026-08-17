"""
Modelos Pydantic para la tabla de BARBERÍA.
Define los esquemas de validación y serialización para la API.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

from src.models.barberia_model import EstadoBarberia


class BarberiaBase(BaseModel):
    """Modelo base con campos comunes para operaciones CRUD."""

    nombre_barberia: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre de la barbería"
    )

    direccion: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Dirección completa de la barbería"
    )

    telefono: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Teléfono de contacto (opcional)"
    )

    estado: EstadoBarberia = EstadoBarberia.ACTIVO


class BarberiaCreate(BarberiaBase):
    """Modelo para crear una nueva barbería."""

    pass


class BarberiaUpdate(BaseModel):
    """Modelo para actualizar una barbería existente (todos los campos opcionales)."""

    nombre_barberia: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Nuevo nombre de la barbería"
    )

    direccion: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Nueva dirección"
    )

    telefono: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Nuevo teléfono"
    )

    estado: Optional[EstadoBarberia] = Field(
        None,
        description="Nuevo estado (Activo/Inactivo)"
    )


class BarberiaResponse(BarberiaBase):
    """Modelo para la respuesta de la API (incluye el ID)."""

    id_barberia: int = Field(..., description="ID único de la barbería")

    model_config = ConfigDict(
        from_attributes=True  # Permite la creación desde objetos SQLAlchemy
        # orm_mode = True  # Eliminado porque ya no es necesario en Pydantic v2
    )


class BarberiaInDB(BarberiaResponse):
    """Modelo interno (misma que la respuesta pero para uso interno)."""

    pass
