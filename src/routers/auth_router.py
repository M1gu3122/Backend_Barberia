"""
Router de autenticación JWT.
Endpoints para iniciar sesión y obtener el usuario autenticado.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.config.security import obtener_usuario_actual
from src.models.usuario_model import Usuario
from src.schemas.auth_schema import LoginRequest, TokenResponse
from src.schemas.usuario_schema import UsuarioResponse
from src.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
    responses={401: {"description": "No autorizado"}},
)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/login", response_model=TokenResponse)
async def login(
    datos: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    """
    Autentica un usuario y devuelve un token JWT.

    Args:
        datos (LoginRequest): Credenciales (usuario y contraseña)

    Returns:
        TokenResponse: Token JWT y datos básicos del usuario

    Raises:
        HTTPException 401: Si las credenciales son incorrectas
    """
    token = service.login(datos.correo, datos.contraseña)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@router.get("/me", response_model=UsuarioResponse)
async def obtener_me(
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    """
    Devuelve la información del usuario autenticado con el token JWT.

    Args:
        usuario (Usuario): Usuario actual (inyectado por el token)

    Returns:
        UsuarioResponse: Datos del usuario autenticado
    """
    return usuario
