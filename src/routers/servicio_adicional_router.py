# src/routers/servicio_adicional_router.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.services.servicio_adicional_service import ServicioAdicionalService
from src.schemas.servicio_adicional_schema import (
    ServicioAdicionalCreate,
    ServicioAdicionalResponse,
)

router = APIRouter(
    prefix="/servicios-adicionales",
    tags=["Servicios Adicionales"],
    responses={404: {"description": "No encontrado"}}
)


def get_servicio_adicional_service(db: Session = Depends(get_db)):
    return ServicioAdicionalService(db)


@router.get("/", response_model=List[ServicioAdicionalResponse])
async def listar_relaciones(
    service: ServicioAdicionalService = Depends(get_servicio_adicional_service),
):
    return service.listar_relaciones()


@router.get("/servicio/{id_servicio}", response_model=List[ServicioAdicionalResponse])
async def obtener_adicionales_por_servicio(
    id_servicio: int,
    service: ServicioAdicionalService = Depends(get_servicio_adicional_service),
):
    return service.obtener_adicionales_por_servicio(id_servicio)


@router.get("/servicio/{id_servicio}/ids", response_model=List[int])
async def obtener_ids_adicionales_por_servicio(
    id_servicio: int,
    service: ServicioAdicionalService = Depends(get_servicio_adicional_service),
):
    return service.obtener_ids_adicionales_por_servicio(id_servicio)


@router.get("/{id_servicio}/{id_adicional}", response_model=ServicioAdicionalResponse)
async def obtener_relacion(
    id_servicio: int,
    id_adicional: int,
    service: ServicioAdicionalService = Depends(get_servicio_adicional_service),
):
    relacion = service.obtener_relacion(id_servicio, id_adicional)
    if not relacion:
        raise HTTPException(
            status_code=404,
            detail=f"La relación {id_servicio}->{id_adicional} no existe",
        )
    return relacion


@router.post("/", response_model=ServicioAdicionalResponse)
async def crear_relacion(
    relacion: ServicioAdicionalCreate,
    service: ServicioAdicionalService = Depends(get_servicio_adicional_service),
):
    return service.crear_relacion(relacion)


@router.delete("/{id_servicio}/{id_adicional}")
async def eliminar_relacion(
    id_servicio: int,
    id_adicional: int,
    service: ServicioAdicionalService = Depends(get_servicio_adicional_service),
):
    deleted = service.eliminar_relacion(id_servicio, id_adicional)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"La relación {id_servicio}->{id_adicional} no existe",
        )
    return {"message": "Relación eliminada correctamente"}