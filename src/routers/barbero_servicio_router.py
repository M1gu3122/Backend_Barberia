# src/routers/barbero_servicio.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.services.barbero_servicio_service import BarberoServicioService
from src.schemas.barbero_servicio_schema import BarberoServicioCreate, BarberoServicioUpdate, BarberoServicioResponse

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

@router.get("/{id_usuario}/{id_servicio}", response_model=BarberoServicioResponse)
async def obtener_relacion(id_usuario: int, id_servicio: int, service: BarberoServicioService = Depends(get_barbero_servicio_service)):
    relacion = service.obtener_relacion(id_usuario, id_servicio)
    if not relacion:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    return relacion

@router.get("/barbero/{id_usuario}", response_model=List[BarberoServicioResponse])
async def obtener_servicios_por_barbero(id_usuario: int, service: BarberoServicioService = Depends(get_barbero_servicio_service)):
    return service.obtener_servicios_por_barbero(id_usuario)

@router.get("/servicio/{id_servicio}", response_model=List[BarberoServicioResponse])
async def obtener_barberos_por_servicio(id_servicio: int, service: BarberoServicioService = Depends(get_barbero_servicio_service)):
    return service.obtener_barberos_por_servicio(id_servicio)

@router.delete("/{id_usuario}/{id_servicio}")
async def eliminar_relacion(id_usuario: int, id_servicio: int, service: BarberoServicioService = Depends(get_barbero_servicio_service)):
    deleted = service.eliminar_relacion(id_usuario, id_servicio)
    if not deleted:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    return {"message": "Relación eliminada correctamente"}
