from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.services.servicio_service import ServicioService
from src.schemas.servicio_schema import ServicioCreate, ServicioUpdate, ServicioResponse
from src.models.servicio_model import Servicio

router = APIRouter(
    prefix="/servicios",
    tags=["Servicios"],
    responses={404: {"description": "No encontrado"}}
)

def get_servicio_service(db: Session = Depends(get_db)):
    return ServicioService(db)

@router.get("/obtener_servicios/", response_model=List[ServicioResponse])
async def listar_servicios(skip: int = 0, limit: int = 100, service: ServicioService = Depends(get_servicio_service)):
    servicios = service.listar_servicios()
    return servicios

@router.get("/obtener_servicio/{id}", response_model=ServicioResponse)
async def obtener_servicio(
    id: int,
    service: ServicioService = Depends(get_servicio_service)
):
    servicio = service.obtener_servicio_por_id(id)

    if not servicio:
        raise HTTPException(
            status_code=404,
            detail="Servicio no encontrado"
        )

    return servicio



@router.post("/crear_servicio/", response_model=ServicioResponse)
async def crear_servicio(servicio: ServicioCreate, service: ServicioService = Depends(get_servicio_service)):
    return service.crear_servicio(servicio)


@router.put("/actualizar_servicio/{id}", response_model=ServicioResponse)
async def actualizar_servicio(id: int, servicio: ServicioUpdate, service: ServicioService = Depends(get_servicio_service)):
    updated_servicio = service.actualizar_servicio(id, servicio)
    if not updated_servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return updated_servicio

@router.delete("/eliminar_servicio/{id}")
async def eliminar_servicio(id: int, service: ServicioService = Depends(get_servicio_service)):
    deleted = service.eliminar_servicio(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return {"message": "Servicio eliminado correctamente"}