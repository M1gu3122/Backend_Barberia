"""
Modelos Pydantic para la autenticación JWT.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """Cuerpo de la petición de login (correo + contraseña)."""
    correo: EmailStr
    contraseña: str


class TokenResponse(BaseModel):
    """Respuesta del login: token JWT + datos básicos del usuario."""
    access_token: str
    token_type: str = "bearer"
    id_usuario: int
    nombres: str
    apellidos: str
    usuario: str
    correo: str
    telefono: Optional[str] = None
    tipo_usuario: str


class ForgotPasswordRequest(BaseModel):
    """Solicitud de restablecimiento de contraseña."""
    correo: EmailStr


class ResetPasswordRequest(BaseModel):
    """Restablecimiento de contraseña con token."""
    token: str = Field(..., min_length=10)
    nueva_contraseña: str = Field(..., min_length=6)


class ChangePasswordRequest(BaseModel):
    """Cambio de contraseña para usuario autenticado."""
    contraseña_actual: str = Field(..., min_length=6)
    nueva_contraseña: str = Field(..., min_length=6)


class PasswordResetResponse(BaseModel):
    """Respuesta genérica para operaciones de contraseña."""
    mensaje: str


class AdminResetPasswordRequest(BaseModel):
    """Restablecimiento de contraseña por administrador (sin token, sin contraseña actual)."""
    id_usuario: int
    nueva_contraseña: str = Field(..., min_length=6)
