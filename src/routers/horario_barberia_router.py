# src/routers/horario_barberia_router.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from src.config.database import get_db
from src.services.horario_barberia_service import HorarioBarberiaService
from src.schemas.horario_barberia_schema import (
    HorarioBarberiaCreate,
    HorarioBarberiaUpdate,
    HorarioBarberiaResponse,
)

router = APIRouter(
    prefix="/horarios-barberia",
    tags=["Horarios Barbería"],
    responses={404: {"description": "No encontrado"}}
)


def get_horario_barberia_service(db: Session = Depends(get_db)):
    return HorarioBarberiaService(db)


@router.get("/", response_model=List[HorarioBarberiaResponse])
async def listar_horarios(
    service: HorarioBarberiaService = Depends(get_horario_barberia_service),
):
    return service.listar_horarios()


@router.get("/barberia/{id_barberia}", response_model=List[HorarioBarberiaResponse])
async def listar_horarios_por_barberia(
    id_barberia: int,
    service: HorarioBarberiaService = Depends(get_horario_barberia_service),
):
    return service.listar_horarios_por_barberia(id_barberia)


@router.get("/barberia/{id_barberia}/dia/{dia_semana}", response_model=HorarioBarberiaResponse)
async def obtener_horario_por_dia(
    id_barberia: int,
    dia_semana: str,
    service: HorarioBarberiaService = Depends(get_horario_barberia_service),
):
    horario = service.obtener_horario_por_dia(id_barberia, dia_semana)
    if not horario:
        raise HTTPException(
            status_code=404,
            detail=f"No hay horario para {dia_semana} en la barbería {id_barberia}",
        )
    return horario


@router.get("/barberia/{id_barberia}/fecha/{fecha}", response_model=HorarioBarberiaResponse)
async def obtener_horario_para_fecha(
    id_barberia: int,
    fecha: datetime,
    service: HorarioBarberiaService = Depends(get_horario_barberia_service),
):
    horario = service.obtener_horario_para_fecha(id_barberia, fecha)
    if not horario:
        raise HTTPException(
            status_code=404,
            detail=f"La barbería {id_barberia} no atiende esa fecha",
        )
    return horario


@router.get("/{id_horario}", response_model=HorarioBarberiaResponse)
async def obtener_horario(
    id_horario: int,
    service: HorarioBarberiaService = Depends(get_horario_barberia_service),
):
    horario = service.obtener_horario(id_horario)
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    return horario


@router.post("/", response_model=HorarioBarberiaResponse)
async def crear_horario(
    horario: HorarioBarberiaCreate,
    service: HorarioBarberiaService = Depends(get_horario_barberia_service),
):
    return service.crear_horario(horario)


@router.put("/{id_horario}", response_model=HorarioBarberiaResponse)
async def actualizar_horario(
    id_horario: int,
    horario: HorarioBarberiaUpdate,
    service: HorarioBarberiaService = Depends(get_horario_barberia_service),
):
    updated = service.actualizar_horario(id_horario, horario)
    if not updated:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    return updated


@router.delete("/{id_horario}")
async def eliminar_horario(
    id_horario: int,
    service: HorarioBarberiaService = Depends(get_horario_barberia_service),
):
    deleted = service.eliminar_horario(id_horario)
    if not deleted:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    return {"message": "Horario eliminado correctamente"}