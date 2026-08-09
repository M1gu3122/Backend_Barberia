# src/routers/barberia_router.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.services.barberia_service import BarberiaService
from src.schemas.barberia_schema import BarberiaCreate, BarberiaUpdate, BarberiaResponse

router = APIRouter(
    prefix="/barberias",
    tags=["Barberías"],
    responses={404: {"description": "No encontrado"}}
)

def get_barberia_service(db: Session = Depends(get_db)):
    
    return BarberiaService(db)

@router.get("/obtener_barberia/", response_model=BarberiaResponse)
async def get_barberia(service: BarberiaService = Depends(get_barberia_service)):
    # Obtener la única barbería (ID = 1)
    barberia = service.obtener_barberia()
    return barberia

@router.post("/crear_barberia/", response_model=BarberiaResponse)
async def create_barberia(barberia: BarberiaCreate, service: BarberiaService = Depends(get_barberia_service)):
    return service.crear_barberia(barberia)

@router.put("/actualizar_barberia/{id}", response_model=BarberiaResponse)
async def update_barberia(barberia: BarberiaUpdate, service: BarberiaService = Depends(get_barberia_service)):
    updated = service.actualizar_barberia(barberia)
    if not updated:
        raise HTTPException(status_code=404, detail="Barbería no encontrada")
    return updated

@router.delete("/eliminar_barberia/{id}")
async def delete_barberia(id: int, service: BarberiaService = Depends(get_barberia_service)):
    
    deleted = service.eliminar_barberia(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Barbería no encontrada")
    return {"message": "Barbería eliminada correctamente"}


