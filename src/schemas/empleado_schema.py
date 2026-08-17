"""
Modelos Pydantic para la tabla EMPLEADO
Extiende la información del usuario con datos laborales.
"""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from src.schemas.usuario_schema import UsuarioResponse
from src.models.empleado_model import TipoEmpleado
from src.models.empleado_model import EstadoEmpleado



class EmpleadoBase(BaseModel):
    id_usuario: int
    tipo_empleado: TipoEmpleado
    estado: EstadoEmpleado
    fecha_contratacion: date

    model_config = ConfigDict(from_attributes=True)


class EmpleadoCreate(BaseModel):
    """Modelo para crear empleados"""
    id_usuario: int
    tipo_empleado: TipoEmpleado
    fecha_contratacion: date
    id_barberia: int

    model_config = ConfigDict(from_attributes=True)


class EmpleadoUpdate(BaseModel):
    """Modelo para actualizar empleados"""
    id_usuario: Optional[int] = None
    estado: Optional[Literal["Activo", "Inactivo"]] = None
    fecha_contratacion: Optional[date] = None
    tipo_empleado: Optional[TipoEmpleado] = None
    model_config = ConfigDict(from_attributes=True)


class EmpleadoResponse(EmpleadoBase):
    """Modelo para respuestas API"""
    usuario: UsuarioResponse  # ✅ Corregido: nombre más claro


class EmpleadoInDB(EmpleadoResponse):
    """Modelo interno con datos adicionales"""
    # Puedes añadir campos adicionales que solo se usan internamente
    ultima_actualizacion: Optional[date] = None
    # otros campos internos


# ✅ Añadido para evitar exponer contraseñas
class EmpleadoPublic(BaseModel):
    """Modelo para respuestas públicas (sin contraseña)"""
    id_usuario: int
    tipo_empleado: Literal["Barbero","Recepcionista","Administrador"]
    estado: Literal["Activo","Inactivo"]
    fecha_contratacion: date
    usuario: UsuarioResponse

    model_config = ConfigDict(from_attributes=True)



