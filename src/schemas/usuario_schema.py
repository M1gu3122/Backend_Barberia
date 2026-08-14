"""
Modelos Pydantic V2 para la tabla de USUARIOS
Define esquemas para clientes y personal del sistema
"""

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

from src.models.cita_model import EstadoCita


class UsuarioBase(BaseModel):
    """Modelo base para usuarios (clientes y empleados)"""
    id_usuario: str
    nombres: str
    apellidos: str
    usuario: str
    contraseña: str
    correo: str
    telefono: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class UsuarioCreate(UsuarioBase):
    """Modelo para crear nuevos usuarios"""
    # La contraseña es opcional: si la crea un admin/recepcionista,
    # se asigna automáticamente el número de identificación (id_usuario)
    contraseña: Optional[str] = None


class UsuarioUpdate(BaseModel):
    """Modelo para actualizar usuarios (solo campos opcionales)"""
    id_usuario: Optional[int] = None
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    usuario: Optional[str] = None
    contraseña: Optional[str] = None
    correo: Optional[EmailStr] = None
    telefono: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UsuarioResponse(UsuarioBase):
    """Modelo para respuestas API con ID"""
    id_usuario: int



class UsuarioInDB(UsuarioResponse):
    """Versión interna con datos adicionales"""
    ultima_actualizacion: Optional[datetime] = None  # Añadido valor por defecto


class UsuarioConCantidadCitas(UsuarioResponse):
    """Modelo para respuestas con la cantidad de citas de cada usuario"""
    cantidad_citas: int


class PerfilUsuarioResponse(BaseModel):
    """Modelo para el perfil de un usuario: datos personales + sus citas con servicios."""
    id_usuario: int
    nombres: str
    apellidos: str
    telefono: Optional[str] = None
    correo: str
    id_cita: Optional[int] = None
    id_barbero: Optional[int] = None
    nombre_barbero: Optional[str] = None
    apellido_barbero: Optional[str] = None
    fecha_hora: Optional[datetime] = None
    estado_cita: Optional[EstadoCita] = None
    id_servicio: Optional[int] = None
    tipo_servicio: Optional[str] = None


# ✅ Añadido para evitar exponer contraseñas
class UsuarioPublic(UsuarioResponse):
    """Modelo para respuestas públicas (sin contraseña)"""
    contraseña: Optional[str] = None  # Aunque sea None, lo dejamos por claridad
