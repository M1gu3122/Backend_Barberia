"""
Modelos Pydantic V2 para la tabla de USUARIOS
Define esquemas para clientes y personal del sistema
"""

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class UsuarioBase(BaseModel):
    """Modelo base para usuarios (clientes y empleados)"""
    id_usuario: int
    nombres: str
    apellidos: str
    usuario: str
    contraseña: str
    correo: EmailStr
    telefono: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class UsuarioCreate(UsuarioBase):
    """Modelo para crear nuevos usuarios"""
    # Campos requeridos para crear un usuario
    # todos los campos son obligatorios para la creación


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


# ✅ Añadido para evitar exponer contraseñas
class UsuarioPublic(UsuarioResponse):
    """Modelo para respuestas públicas (sin contraseña)"""
    contraseña: Optional[str] = None  # Aunque sea None, lo dejamos por claridad
