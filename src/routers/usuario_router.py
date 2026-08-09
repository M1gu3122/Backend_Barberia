"""
Router para la gestión de usuarios en la barbería.
Este archivo contiene las rutas HTTP para crear, listar, obtener, actualizar y eliminar usuarios.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.services.usuario_service import UsuarioService
from src.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate, UsuarioResponse

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
    responses={404: {"description": "No encontrado"}}
)

def get_usuario_service(db: Session = Depends(get_db)):
    return UsuarioService(db)

# =========================================================
# Rutas GET
# =========================================================

@router.get("/obtener_usuarios", response_model=List[UsuarioResponse])
async def listar_usuarios(skip: int = 0, limit: int = 100, service: UsuarioService = Depends(get_usuario_service)
):
    """
    Listar todos los usuarios con paginación.

    Args:
        skip (int): Número de registros a saltar
        limit (int): Límite de registros a mostrar
        service: Servicio de usuario

    Returns:
        List[UsuarioResponse]: Lista de usuarios
    """
    return service.listar_usuarios(skip, limit)

@router.get("/obtener_usuario/{id}", response_model=UsuarioResponse)
async def obtener_usuario(id: int, service: UsuarioService = Depends(get_usuario_service)):
    """
    Obtener un usuario específico por su ID.

    Args:
        id (int): ID del usuario a buscar
        service: Servicio de usuario

    Returns:
        UsuarioResponse: Datos del usuario encontrado

    Raises:
        HTTPException: Si no se encuentra el usuario
    """
    usuario = service.obtener_usuario_por_id(id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.get("/buscar_usuario/{nombre_usuario}", response_model=UsuarioResponse)
async def obtener_por_usuario(nombre_usuario: str, service: UsuarioService = Depends(get_usuario_service)):
    """
    Buscar un usuario por su nombre de usuario.

    Args:
        nombre_usuario (str): Nombre de usuario a buscar
        service: Servicio de usuario

    Returns:
        UsuarioResponse: Datos del usuario encontrado

    Raises:
        HTTPException: Si no se encuentra el usuario
    """
    usuario = service.obtener_por_usuario(nombre_usuario)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# =========================================================
# Rutas POST
# =========================================================

@router.post("/crear_usuario", response_model=UsuarioResponse)
async def crear_usuario(usuario: UsuarioCreate, service: UsuarioService = Depends(get_usuario_service)):
    """
    Crear un nuevo usuario.

    Args:
        usuario (UsuarioCreate): Datos para crear el usuario
        service: Servicio de usuario

    Returns:
        UsuarioResponse: El usuario creado

    Raises:
        HTTPException: Si hay errores de validación
    """
    try:
        return service.crear_usuario(usuario)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# =========================================================
# Rutas PUT
# =========================================================

@router.put("/actualizar_usuario/{id}", response_model=UsuarioResponse)
async def actualizar_usuario(id: int, usuario: UsuarioUpdate, service: UsuarioService = Depends(get_usuario_service)):
    """
    Actualizar un usuario existente.

    Args:
        id (int): ID del usuario a actualizar
        usuario (UsuarioUpdate): Datos para actualizar el usuario
        service: Servicio de usuario

    Returns:
        UsuarioResponse: El usuario actualizado

    Raises:
        HTTPException: Si no se encuentra el usuario o hay errores de validación
    """
    try:
        updated_usuario = service.actualizar_usuario(id, usuario)
        if not updated_usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return updated_usuario
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# =========================================================
# Rutas DELETE
# =========================================================

@router.delete("/eliminar_usuario/{id}")
async def eliminar_usuario(id: int, service: UsuarioService = Depends(get_usuario_service)):
    """
    Eliminar un usuario por su ID.

    Args:
        id (int): ID del usuario a eliminar
        service: Servicio de usuario

    Returns:
        dict: Mensaje de confirmación

    Raises:
        HTTPException: Si no se encuentra el usuario
    """
    deleted = service.eliminar_usuario(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"message": "Usuario eliminado correctamente"}

# =========================================================
# Rutas adicionales
# =========================================================

@router.get("/buscar/{termino}", response_model=List[UsuarioResponse])
async def buscar_usuarios(termino: str, service: UsuarioService = Depends(get_usuario_service)):
    """
    Buscar usuarios por nombre, apellido, usuario o correo.

    Args:
        termino (str): Término de búsqueda
        service: Servicio de usuario

    Returns:
        List[UsuarioResponse]: Lista de usuarios que coinciden con el término
    """
    return service.buscar_usuarios(termino)

@router.get("/obtener_clientes", response_model=List[UsuarioResponse])
async def obtener_clientes(service: UsuarioService = Depends(get_usuario_service)):
    """
    Obtener todos los clientes (usuarios que no son empleados).

    Args:
        service: Servicio de usuario

    Returns:
        List[UsuarioResponse]: Lista de clientes
    """
    return service.obtener_clientes()

# =========================================================
# Rutas de autenticación (opcional)
# =========================================================

@router.post("/login", response_model=UsuarioResponse)
async def login(
    nombre_usuario: str, 
    contraseña: str, 
    service: UsuarioService = Depends(get_usuario_service)
):
    """
    Autenticar un usuario.

    Args:
        nombre_usuario (str): Nombre de usuario
        contraseña (str): Contraseña
        service: Servicio de usuario

    Returns:
        UsuarioResponse: Datos del usuario autenticado

    Raises:
        HTTPException: Si las credenciales son incorrectas
    """
    try:
        usuario = service.verificar_credenciales(nombre_usuario, contraseña)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )
        return usuario
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
