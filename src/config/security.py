"""
Configuración de seguridad para autenticación JWT.
Incluye creación/decodificación de tokens y dependencia para proteger rutas.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.models.usuario_model import Usuario
from src.models.empleado_model import TipoEmpleado

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "clave_secreta_super_segura")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def crear_token_acceso(datos: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT a partir de los datos (claims) dados.
    Por defecto expira en ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    to_encode = datos.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Decodifica un token JWT validando firma y expiración."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Dependencia para proteger rutas: valida el token Bearer
    y devuelve el Usuario autenticado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decodificar_token(token)
    id_usuario = payload.get("sub")
    if id_usuario is None:
        raise credentials_exception

    usuario = (
        db.query(Usuario).filter(Usuario.id_usuario == int(id_usuario)).first()
    )
    if usuario is None:
        raise credentials_exception
    return usuario


def es_admin_o_recepcionista(usuario: Usuario) -> bool:
    """Verifica que el usuario sea Administrador o Recepcionista."""
    return (
        usuario.empleado is not None
        and usuario.empleado.tipo_empleado
        in (TipoEmpleado.ADMINISTRADOR, TipoEmpleado.RECEPCIONISTA)
    )


def require_admin_o_recepcionista(
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> Usuario:
    """
    Dependencia para proteger rutas que solo pueden usar
    administradores o recepcionistas.
    """
    if not es_admin_o_recepcionista(usuario):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores o recepcionistas pueden realizar esta acción",
        )
    return usuario


def es_admin(usuario: Usuario) -> bool:
    """Verifica que el usuario sea Administrador."""
    return (
        usuario.empleado is not None
        and usuario.empleado.tipo_empleado == TipoEmpleado.ADMINISTRADOR
    )


def require_admin(
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> Usuario:
    """
    Dependencia para proteger rutas que solo pueden usar
    administradores.
    """
    if not es_admin(usuario):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden realizar esta acción",
        )
    return usuario
