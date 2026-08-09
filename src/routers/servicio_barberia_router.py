# src/routers/servicio_barberia.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.services.servicio_barberia_service import ServicioBarberiaService
from src.schemas.servicio_barberia_schema import ServicioBarberiaCreate, ServicioBarberiaUpdate, ServicioBarberiaResponse

router = APIRouter(
    prefix="/servicios-barberias",
    tags=["Servicios-Barberías"],
    responses={404: {"description": "No encontrado"}}
)

def get_servicio_barberia_service(db: Session = Depends(get_db)):
    return ServicioBarberiaService(db)

@router.post("/", response_model=ServicioBarberiaResponse)
async def crear_relacion(relacion: ServicioBarberiaCreate, service: ServicioBarberiaService = Depends(get_servicio_barberia_service)):
    return service.crear_relacion(relacion)

@router.put("/{id_barberia}/{id_servicio}", response_model=ServicioBarberiaResponse)
async def actualizar_relacion(id_barberia: int, id_servicio: int, relacion: ServicioBarberiaUpdate, service: ServicioBarberiaService = Depends(get_servicio_barberia_service)):
    actualizado = service.actualizar_relacion(id_barberia, id_servicio, relacion)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    return actualizado

@router.get("/{id_barberia}/{id_servicio}", response_model=ServicioBarberiaResponse)
async def obtener_relacion(id_barberia: int, id_servicio: int, service: ServicioBarberiaService = Depends(get_servicio_barberia_service)):
    relacion = service.obtener_relacion(id_barberia, id_servicio)
    if not relacion:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    return relacion

@router.get("/barberia/{id_barberia}", response_model=List[ServicioBarberiaResponse])
async def obtener_servicios_por_barberia(id_barberia: int, service: ServicioBarberiaService = Depends(get_servicio_barberia_service)):
    return service.obtener_servicios_por_barberia(id_barberia)

@router.get("/servicio/{id_servicio}", response_model=List[ServicioBarberiaResponse])
async def obtener_barberias_por_servicio(id_servicio: int, service: ServicioBarberiaService = Depends(get_servicio_barberia_service)):
    return service.obtener_barberias_por_servicio(id_servicio)

@router.delete("/{id_barberia}/{id_servicio}")
async def eliminar_relacion(id_barberia: int, id_servicio: int, service: ServicioBarberiaService = Depends(get_servicio_barberia_service)):
    deleted = service.eliminar_relacion(id_barberia, id_servicio)
    if not deleted:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    return {"message": "Relación eliminada correctamente"}
