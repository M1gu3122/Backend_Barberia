"""
Modelos Pydantic para la autenticación JWT.
"""

from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    """Cuerpo de la petición de login (correo + contraseña)."""
    correo: str
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
