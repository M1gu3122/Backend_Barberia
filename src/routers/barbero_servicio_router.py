# src/routers/barbero_servicio.py
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.services.barbero_servicio_service import BarberoServicioService
from src.schemas.barbero_servicio_schema import BarberoServicioCreate, BarberoServicioUpdate, BarberoServicioResponse, BarberoDisponibleResponse

router = APIRouter(
    prefix="/barberos-servicios",
    tags=["Barberos-Servicios"],
    responses={404: {"description": "No encontrado"}}
)

def get_barbero_servicio_service(db: Session = Depends(get_db)):
    return BarberoServicioService(db)

@router.post("/", response_model=BarberoServicioResponse)
async def crear_relacion(relacion: BarberoServicioCreate, service: BarberoServicioService = Depends(get_barbero_servicio_service)):
    return service.crear_relacion(relacion)

@router.get("/obtener_servicios_por_barbero/{id_usuario}", response_model=List[BarberoServicioResponse])
async def obtener_servicios_por_barbero(id_usuario: int, service: BarberoServicioService = Depends(get_barbero_servicio_service)):
    return service.obtener_servicios_por_barbero(id_usuario)

@router.get("/{id_usuario}/{id_servicio}", response_model=BarberoServicioResponse)
async def obtener_relacion(id_usuario: int, id_servicio: int, service: BarberoServicioService = Depends(get_barbero_servicio_service)):
    relacion = service.obtener_relacion(id_usuario, id_servicio)
    if not relacion:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    return relacion

@router.get("/servicio/{id_servicio}", response_model=List[BarberoServicioResponse])
async def obtener_barberos_por_servicio(id_servicio: int, service: BarberoServicioService = Depends(get_barbero_servicio_service)):
    return service.obtener_barberos_por_servicio(id_servicio)

@router.get("/barberos-disponibles", response_model=List[BarberoDisponibleResponse])
async def obtener_barberos_disponibles(
    ids_servicio: List[int] = Query(...),
    service: BarberoServicioService = Depends(get_barbero_servicio_service),
):
    """Barberos activos que pueden realizar todos los servicios indicados."""
    return service.obtener_barberos_con_todos_los_servicios(ids_servicio)

@router.delete("/eliminarServicioBarbero/{id_usuario}/{id_servicio}")
async def eliminar_relacion(id_usuario: int, id_servicio: int, service: BarberoServicioService = Depends(get_barbero_servicio_service)):
    deleted = service.eliminar_relacion(id_usuario, id_servicio)
    if not deleted:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    return {"message": "Relación eliminada correctamente"}

@router.post("/asignar_servicio/{id_barbero}/{id_servicio}", response_model=BarberoServicioResponse)
async def asignar_servicio(id_barbero: int, id_servicio: int, service: BarberoServicioService = Depends(get_barbero_servicio_service)):
    return service.asignar_servicio(id_barbero, id_servicio)