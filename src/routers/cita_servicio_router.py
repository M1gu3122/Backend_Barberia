# src/routers/cita_servicio.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.services.cita_servicio_service import CitaServicioService
from src.schemas.cita_servicio_schema import CitaServicioCreate, CitaServicioUpdate, CitaServicioResponse

router = APIRouter(
    prefix="/citas-servicios",
    tags=["Citas-Servicios"],
    responses={404: {"description": "No encontrado"}}
)

def get_cita_servicio_service(db: Session = Depends(get_db)):
    return CitaServicioService(db)

@router.post("/", response_model=CitaServicioResponse)
async def crear_relacion(relacion: CitaServicioCreate, service: CitaServicioService = Depends(get_cita_servicio_service)):
    return service.crear_relacion(relacion)

@router.get("/{id_cita}/{id_servicio}", response_model=CitaServicioResponse)
async def obtener_relacion(id_cita: int, id_servicio: int, service: CitaServicioService = Depends(get_cita_servicio_service)):
    relacion = service.obtener_relacion(id_cita, id_servicio)
    if not relacion:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    return relacion

@router.get("/cita/{id_cita}", response_model=List[CitaServicioResponse])
async def obtener_servicios_por_cita(id_cita: int, service: CitaServicioService = Depends(get_cita_servicio_service)):
    return service.obtener_servicios_por_cita(id_cita)

@router.get("/servicio/{id_servicio}", response_model=List[CitaServicioResponse])
async def obtener_citas_por_servicio(id_servicio: int, service: CitaServicioService = Depends(get_cita_servicio_service)):
    return service.obtener_citas_por_servicio(id_servicio)

@router.delete("/{id_cita}/{id_servicio}")
async def eliminar_relacion(id_cita: int, id_servicio: int, service: CitaServicioService = Depends(get_cita_servicio_service)):
    deleted = service.eliminar_relacion(id_cita, id_servicio)
    if not deleted:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    return {"message": "Relación eliminada correctamente"}
