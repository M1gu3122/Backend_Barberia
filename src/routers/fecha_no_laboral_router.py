# src/routers/fecha_no_laboral_router.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.services.fecha_no_laboral_service import FechaNoLaboralService
from src.schemas.fecha_no_laboral_schema import (
    FechaNoLaboralCreate,
    FechaNoLaboralUpdate,
    FechaNoLaboralResponse,
)

router = APIRouter(
    prefix="/fechas-no-laborales",
    tags=["Fechas No Laborales"],
    responses={404: {"description": "No encontrado"}}
)


def get_fecha_no_laboral_service(db: Session = Depends(get_db)):
    return FechaNoLaboralService(db)


@router.get("/", response_model=List[FechaNoLaboralResponse])
async def listar_fechas_no_laborales(
    service: FechaNoLaboralService = Depends(get_fecha_no_laboral_service),
):
    return service.listar_fechas_no_laborales()


@router.get("/barberia/{id_barberia}", response_model=List[FechaNoLaboralResponse])
async def listar_por_barberia(
    id_barberia: int,
    service: FechaNoLaboralService = Depends(get_fecha_no_laboral_service),
):
    return service.listar_por_barberia(id_barberia)


@router.get("/{id_fecha_no_laboral}", response_model=FechaNoLaboralResponse)
async def obtener_fecha_no_laboral(
    id_fecha_no_laboral: int,
    service: FechaNoLaboralService = Depends(get_fecha_no_laboral_service),
):
    registro = service.obtener_fecha_no_laboral(id_fecha_no_laboral)
    if not registro:
        raise HTTPException(status_code=404, detail="Fecha no laboral no encontrada")
    return registro


@router.post("/", response_model=FechaNoLaboralResponse)
async def crear_fecha_no_laboral(
    fecha: FechaNoLaboralCreate,
    service: FechaNoLaboralService = Depends(get_fecha_no_laboral_service),
):
    return service.crear_fecha_no_laboral(fecha)


@router.put("/{id_fecha_no_laboral}", response_model=FechaNoLaboralResponse)
async def actualizar_fecha_no_laboral(
    id_fecha_no_laboral: int,
    fecha: FechaNoLaboralUpdate,
    service: FechaNoLaboralService = Depends(get_fecha_no_laboral_service),
):
    updated = service.actualizar_fecha_no_laboral(id_fecha_no_laboral, fecha)
    if not updated:
        raise HTTPException(status_code=404, detail="Fecha no laboral no encontrada")
    return updated


@router.delete("/{id_fecha_no_laboral}")
async def eliminar_fecha_no_laboral(
    id_fecha_no_laboral: int,
    service: FechaNoLaboralService = Depends(get_fecha_no_laboral_service),
):
    deleted = service.eliminar_fecha_no_laboral(id_fecha_no_laboral)
    if not deleted:
        raise HTTPException(status_code=404, detail="Fecha no laboral no encontrada")
    return {"message": "Fecha no laboral eliminada correctamente"}