"""
Servicio de autenticación: login de usuarios y emisión de tokens JWT.
"""

from typing import Optional

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.config.security import crear_token_acceso
from src.models.usuario_model import Usuario
from src.repositories.usuario_repository import UsuarioRepository
from src.schemas.auth_schema import TokenResponse

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
