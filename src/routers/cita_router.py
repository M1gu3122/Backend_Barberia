# src/routers/cita_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.schemas.cita_servicio_schema import CitaServicioCreate
from src.config.database import get_db
from src.services.cita_service import CitaService
from src.schemas.cita_schema import CitaCreate, CitaUpdate, CitaResponse

router = APIRouter(
    prefix="/citas",
    tags=["Citas"],
    responses={404: {"description": "No encontrado"}}
)

def get_cita_service(db: Session = Depends(get_db)):
    return CitaService(db)

@router.get("/obtener_citas/", response_model=List[CitaResponse])
async def listar_citas(skip: int = 0, limit: int = 100, service: CitaService = Depends(get_cita_service)):
    citas = service.listar_citas()
    return citas

@router.get("/obtener_cita/{id}", response_model=CitaResponse)
async def obtener_cita(id: int, service: CitaService = Depends(get_cita_service)):
    cita = service.obtener_cita_por_id(id)  
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita

@router.post("/crear_cita/", response_model=CitaResponse) 
async def crear_cita(cita: CitaCreate, service: CitaService = Depends(get_cita_service)):
    try:
        nueva_cita = service.crear_cita(cita)  
        return nueva_cita
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/actualizar_cita/{id}", response_model=CitaResponse)
async def actualizar_cita(id: int, cita: CitaUpdate, service: CitaService = Depends(get_cita_service)):
    updated_cita = service.actualizar_cita(id, cita)  
    if not updated_cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return updated_cita

@router.delete("/eliminar_cita/{id}")
async def eliminar_cita(id: int, service: CitaService = Depends(get_cita_service)):
    deleted = service.eliminar_cita(id) 
    if not deleted:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return {"message": "Cita eliminada correctamente"}

@router.get("/obtener_citas_por_cliente/{id_cliente}", response_model=List[CitaResponse])
async def listar_citas_por_cliente(id_cliente: int, service: CitaService = Depends(get_cita_service)):
    citas = service.listar_citas_por_cliente(id_cliente)
    return citas

@router.get("/obtener_citas_por_barbero/{id_barbero}", response_model=List[CitaResponse])
async def listar_citas_por_barbero(id_barbero: int, service: CitaService = Depends(get_cita_service)):
    citas = service.listar_citas_por_barbero(id_barbero)
    return citas

@router.get("/obtener_citas_por_fecha/{fecha_inicio}/{fecha_fin}", response_model=List[CitaResponse])
async def listar_citas_por_fecha(
    fecha_inicio: str, 
    fecha_fin: str, 
    service: CitaService = Depends(get_cita_service)
):
    from datetime import datetime
    try:
        inicio = datetime.fromisoformat(fecha_inicio)
        fin = datetime.fromisoformat(fecha_fin)
        citas = service.listar_citas_por_fecha(inicio, fin)
        return citas
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")
    
    # src/routers/cita_router.py
@router.post("/asignar_servicios/{id_cita}/servicios")
async def asignar_servicios_a_cita(
    id_cita: int, 
    servicios: List[int], 
    service: CitaService = Depends(get_cita_service)
):
    # Validar que la cita exista
    cita = service.obtener_cita_por_id(id_cita)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Asignar servicios uno por uno
    for servicio_id in servicios:
        # Crear la relación en la tabla intermedia
        cita_servicio_data = CitaServicioCreate(
            id_cita=id_cita,
            id_servicio=servicio_id
        )
        service.asignar_servicio_a_cita(cita_servicio_data)
    
    # Calcular tiempo total
    tiempo_total = service._calcular_tiempo_servicios(id_cita)
    
    return {
        "message": "Servicios asignados correctamente", 
        "tiempo_total": tiempo_total,
        "cita_id": id_cita
    }

@router.put("/{id_cita}/confirmar")
async def confirmar_cita(id_cita: int, service: CitaService = Depends(get_cita_service)):
    cita = service.obtener_cita_por_id(id_cita)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    service.confirmar_cita(id_cita)
    return {"message": "Cita confirmada"}

@router.put("/{id_cita}/cancelar")
async def cancelar_cita(id_cita: int, service: CitaService = Depends(get_cita_service)):
    cita = service.obtener_cita_por_id(id_cita)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    service.cancelar_cita(id_cita)
    return {"message": "Cita cancelada"}

@router.put("/{id_cita}/completar")
async def completar_cita(id_cita: int, service: CitaService = Depends(get_cita_service)):
    cita = service.obtener_cita_por_id(id_cita)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    service.completar_cita(id_cita)
    return {"message": "Cita completada"}
