from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.services.notificacion_service import NotificacionService
from src.schemas.notificacion_schema import NotificacionCreate, NotificacionUpdate, NotificacionResponse

router = APIRouter(
    prefix="/notificaciones",
    tags=["Notificaciones"],
    responses={404: {"description": "No encontrado"}}
)

def get_notificacion_service(db: Session = Depends(get_db)):
    return NotificacionService(db)

@router.get("/", response_model=List[NotificacionResponse])
async def listar_notificaciones(skip: int = 0, limit: int = 100, service: NotificacionService = Depends(get_notificacion_service)):
    """
    Listar todas las notificaciones con paginación.

    Args:
        skip (int): Número de registros a saltar
        limit (int): Límite de registros a mostrar
        service: Servicio de notificación

    Returns:
        List[NotificacionResponse]: Lista de notificaciones
    """
    notificaciones = service.listar(skip=skip, limit=limit)
    return notificaciones

@router.get("/{id}", response_model=NotificacionResponse)
async def obtener_notificacion(id: int, service: NotificacionService = Depends(get_notificacion_service)):
    """
    Obtener una notificación específica por su ID.

    Args:
        id (int): ID de la notificación a buscar
        service: Servicio de notificación

    Returns:
        NotificacionResponse: Datos de la notificación encontrada

    Raises:
        HTTPException: Si no se encuentra la notificación
    """
    notificacion = service.obtener_por_id(id)
    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return notificacion

@router.post("/", response_model=NotificacionResponse)
async def crear_notificacion(notificacion: NotificacionCreate, service: NotificacionService = Depends(get_notificacion_service)):
    """
    Crear una nueva notificación.

    Args:
        notificacion (NotificacionCreate): Datos para crear la notificación
        service: Servicio de notificación

    Returns:
        NotificacionResponse: La notificación creada
    """
    return service.crear(notificacion)

@router.put("/{id}", response_model=NotificacionResponse)
async def actualizar_notificacion(id: int, notificacion: NotificacionUpdate, service: NotificacionService = Depends(get_notificacion_service)):
    """
    Actualizar una notificación existente.

    Args:
        id (int): ID de la notificación a actualizar
        notificacion (NotificacionUpdate): Datos para actualizar la notificación
        service: Servicio de notificación

    Returns:
        NotificacionResponse: La notificación actualizada

    Raises:
        HTTPException: Si no se encuentra la notificación
    """
    updated_notificacion = service.actualizar(id, notificacion)
    if not updated_notificacion:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return updated_notificacion

@router.delete("/{id}")
async def eliminar_notificacion(id: int, service: NotificacionService = Depends(get_notificacion_service)):
    """
    Eliminar una notificación por su ID.

    Args:
        id (int): ID de la notificación a eliminar
        service: Servicio de notificación

    Returns:
        dict: Mensaje de confirmación

    Raises:
        HTTPException: Si no se encuentra la notificación
    """
    deleted = service.eliminar(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return {"message": "Notificación eliminada correctamente"}
