"""
Servicio de autenticación: login de usuarios, emisión de tokens JWT y restablecimiento de contraseña.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.config.security import crear_token_acceso
from src.models.usuario_model import Usuario
from src.repositories.usuario_repository import UsuarioRepository
from src.schemas.auth_schema import TokenResponse
from src.messaging.email import send_notification, send_template_email

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Lógica de negocio para autenticación con JWT."""

    def __init__(self, db: Session):
        self._db = db
        self._repo = UsuarioRepository(db)

    def autenticar_usuario(self, correo: str, contraseña: str) -> Optional[Usuario]:
        """Verifica las credenciales por correo y devuelve el Usuario si son correctas."""
        user = self._repo.get_by_correo(correo)
        if not user:
            return None
        if not pwd_context.verify(contraseña, user.contraseña):
            return None
        return user

    def login(self, correo: str, contraseña: str) -> Optional[TokenResponse]:
        """
        Autentica al usuario y, si las credenciales son válidas,
        genera y devuelve un token JWT junto con sus datos.
        """
        user = self.autenticar_usuario(correo, contraseña)
        if not user:
            return None

        token = crear_token_acceso({"sub": str(user.id_usuario)})
        return TokenResponse(
            access_token=token,
            id_usuario=int(user.id_usuario),
            nombres=user.nombres,
            apellidos=user.apellidos,
            usuario=user.usuario,
            correo=user.correo,
            telefono=user.telefono,
            tipo_usuario=user.tipo_usuario,
        )

    def _generar_reset_token(self) -> str:
        """Genera un token seguro para restablecimiento de contraseña."""
        return secrets.token_urlsafe(32)

    async def solicitar_reset_contrasena(self, correo: str) -> bool:
        """
        Genera un token de restablecimiento y lo envía por correo.
        Siempre retorna True para no revelar si el correo existe (seguridad).
        """
        user = self._repo.get_by_correo(correo)
        if not user:
            return True

        # Generar token y expiración (1 hora)
        token = self._generar_reset_token()
        expiracion = datetime.now(timezone.utc) + timedelta(hours=1)

        user.reset_token = token
        user.reset_token_expiry = expiracion
        self._db.commit()

        # Enviar correo con el token (plantilla HTML)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5500").rstrip("/")
        reset_link = f"{frontend_url}/pages/reset-password.html?token={token}"
        print(f"[RECUPERAR] Enlace de restablecimiento para {correo}: {reset_link}")
        await send_template_email(
            subject="Restablece tu contraseña - Barbería",
            recipients=[correo],
            template_name="reset_password.html",
            context={
                "nombres": user.nombres,
                "apellidos": user.apellidos,
                "reset_link": reset_link,
            }
        )
        return True

    def reset_contrasena(self, token: str, nueva_contraseña: str) -> bool:
        """
        Valida el token y actualiza la contraseña.
        Retorna True si fue exitoso, False si token inválido/expirado.
        """
        user = self._db.query(Usuario).filter(Usuario.reset_token == token).first()
        if not user:
            return False

        # Verificar expiración (reset_token_expiry es naive UTC)
        if user.reset_token_expiry and user.reset_token_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return False

        # Actualizar contraseña y limpiar token
        user.contraseña = pwd_context.hash(nueva_contraseña)
        user.reset_token = None
        user.reset_token_expiry = None
        self._db.commit()
        return True

    def cambiar_contrasena(self, user_id: int, contraseña_actual: str, nueva_contraseña: str) -> bool:
        """
        Cambia la contraseña de un usuario autenticado verificando la actual.
        Retorna True si exitoso, False si contraseña actual incorrecta.
        """
        user = self._repo.get_by_id(user_id)
        if not user:
            return False

        if not pwd_context.verify(contraseña_actual, user.contraseña):
            return False

        user.contraseña = pwd_context.hash(nueva_contraseña)
        self._db.commit()
        return True

    def admin_reset_contrasena(self, user_id: int, nueva_contraseña: str) -> bool:
        """
        Administrador cambia la contraseña de cualquier usuario sin restricciones.
        Retorna True si exitoso, False si usuario no existe.
        """
        user = self._repo.get_by_id(user_id)
        if not user:
            return False

        user.contraseña = pwd_context.hash(nueva_contraseña)
        # Limpiar tokens de reset si existieran
        user.reset_token = None
        user.reset_token_expiry = None
        self._db.commit()
        return True
