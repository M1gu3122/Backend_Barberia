"""
Router de autenticación JWT.
Endpoints para iniciar sesión, restablecer contraseña y obtener el usuario autenticado.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.config.security import obtener_usuario_actual, require_admin
from src.models.usuario_model import Usuario
from src.schemas.auth_schema import (
    LoginRequest,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    AdminResetPasswordRequest,
    PasswordResetResponse,
)
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
    """
    token = service.login(datos.correo, datos.contraseña)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    datos: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
):
    """
    Solicita el restablecimiento de contraseña.
    Envía un correo con token de restablecimiento (si el usuario existe).
    Siempre retorna éxito para no revelar si el correo está registrado.
    """
    await service.solicitar_reset_contrasena(datos.correo)
    return PasswordResetResponse(
        mensaje="Si el correo existe, recibirás instrucciones para restablecer tu contraseña."
    )


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    datos: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
):
    """
    Restablece la contraseña usando el token recibido por correo.
    """
    ok = service.reset_contrasena(datos.token, datos.nueva_contraseña)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado"
        )
    return PasswordResetResponse(mensaje="Contraseña actualizada correctamente.")


@router.post("/change-password", response_model=PasswordResetResponse)
async def change_password(
    datos: ChangePasswordRequest,
    usuario: Usuario = Depends(obtener_usuario_actual),
    service: AuthService = Depends(get_auth_service),
):
    """
    Cambia la contraseña del usuario autenticado (requiere token JWT).
    """
    ok = service.cambiar_contrasena(usuario.id_usuario, datos.contraseña_actual, datos.nueva_contraseña)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta"
        )
    return PasswordResetResponse(mensaje="Contraseña cambiada correctamente.")


@router.post("/admin/reset-password", response_model=PasswordResetResponse)
async def admin_reset_password(
    datos: AdminResetPasswordRequest,
    _admin: Usuario = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
):
    """
    Administrador cambia la contraseña de cualquier usuario sin restricciones.
    No requiere contraseña actual ni token.
    """
    ok = service.admin_reset_contrasena(datos.id_usuario, datos.nueva_contraseña)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return PasswordResetResponse(mensaje="Contraseña restablecida por administrador.")


@router.get("/me", response_model=UsuarioResponse)
async def obtener_me(
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    """
    Devuelve la información del usuario autenticado con el token JWT.
    """
    return usuario
