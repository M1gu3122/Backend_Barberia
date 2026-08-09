"""
Rutas para la gestión de empleados.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from src.models.empleado_model import EstadoEmpleado
from src.repositories.usuario_repository import UsuarioRepository
from src.services.empleado_service import EmpleadoService
from src.config.database import get_db
from src.schemas.empleado_schema import EmpleadoCreate, EmpleadoUpdate, EmpleadoResponse
from src.repositories.empleado_repository import EmpleadoRepository


router = APIRouter(
    prefix="/empleados",
    tags=["Empleados"],
    responses={404: {"description": "No encontrado"}}
)


def get_empleado_service(db: Session = Depends(get_db)):
    """Inyección de dependencias para el servicio de empleados"""
    empleado_repo = EmpleadoRepository(db)
    usuario_repo = UsuarioRepository(db)
    return EmpleadoService(empleado_repo, usuario_repo, db)


@router.post("/crear_empleado", response_model=EmpleadoResponse)
async def crear_empleado(
    datos: EmpleadoCreate, 
    service: EmpleadoService = Depends(get_empleado_service)
):
    """
    Crear un nuevo empleado.
    
    Args:
        datos (EmpleadoCreate): Datos para crear el empleado
        service: Servicio de empleado

    Returns:
        EmpleadoResponse: El empleado creado

    Raises:
        HTTPException: Si hay errores de validación o de creación
    """
    try:
        return service.crear_empleado(datos)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear empleado: {str(e)}")


@router.get("/obtener_empleados", response_model=List[EmpleadoResponse])
async def listar_empleados(service: EmpleadoService = Depends(get_empleado_service)):
    """
    Listar todos los empleados.

    Args:
        service: Servicio de empleado

    Returns:
        List[EmpleadoResponse]: Lista de empleados
    """
    try:
        return service.listar_empleados()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar empleados: {str(e)}")


@router.get("/obtener_empleado/{id_empleado}", response_model=EmpleadoResponse)
async def obtener_empleado(
    id_empleado: int, 
    service: EmpleadoService = Depends(get_empleado_service)
):
    """
    Obtener un empleado por su ID.

    Args:
        id_empleado (int): ID del empleado a buscar
        service: Servicio de empleado

    Returns:
        EmpleadoResponse: Datos del empleado encontrado

    Raises:
        HTTPException: Si no se encuentra el empleado
    """
    try:
        empleado = service.obtener_empleado_por_id(id_empleado)
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
        return empleado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener empleado: {str(e)}")


@router.put("/actualizar_empleado/{id_empleado}", response_model=EmpleadoResponse)
async def actualizar_empleado(
    id_empleado: int, 
    empleado_actualizado: EmpleadoUpdate,
    service: EmpleadoService = Depends(get_empleado_service)
):
    """
    Actualizar un empleado existente.

    Args:
        id_empleado (int): ID del empleado a actualizar
        empleado_actualizado (EmpleadoUpdate): Datos para actualizar el empleado
        service: Servicio de empleado

    Returns:
        EmpleadoResponse: El empleado actualizado

    Raises:
        HTTPException: Si no se encuentra el empleado o hay errores de validación
    """
    try:
        empleado = service.actualizar_empleado(id_empleado, empleado_actualizado)
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
        return empleado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar empleado: {str(e)}")


@router.delete("/eliminar_empleado/{id_empleado}")
async def eliminar_empleado(
    id_empleado: int, 
    service: EmpleadoService = Depends(get_empleado_service)
):
    """
    Eliminar un empleado por su ID.

    Args:
        id_empleado (int): ID del empleado a eliminar
        service: Servicio de empleado

    Returns:
        dict: Mensaje de confirmación

    Raises:
        HTTPException: Si no se encuentra el empleado
    """
    try:
        eliminado = service.eliminar_empleado(id_empleado)
        if not eliminado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")
        return {"message": "Empleado eliminado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar empleado: {str(e)}")


# =========================================================
# Rutas adicionales
# =========================================================

@router.get("/obtener_barberos", response_model=List[EmpleadoResponse])
async def listar_barberos(service: EmpleadoService = Depends(get_empleado_service)):
    """
    Listar todos los barberos activos.

    Args:
        service: Servicio de empleado

    Returns:
        List[EmpleadoResponse]: Lista de barberos
    """
    try:
        return service.obtener_barberos()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar barberos: {str(e)}")





@router.get("/tipo/{tipo_empleado}", response_model=List[EmpleadoResponse])
async def listar_empleados_por_tipo(
    tipo_empleado: str, 
    service: EmpleadoService = Depends(get_empleado_service)
):
    """
    Listar empleados de un tipo específico.

    Args:
        tipo_empleado (str): Tipo de empleado (Barbero, Recepcionista, Administrador)
        service: Servicio de empleado

    Returns:
        List[EmpleadoResponse]: Lista de empleados del tipo especificado
    """
    try:
        # Validar tipo de empleado
        from src.models.empleado_model import TipoEmpleado
        try:
            TipoEmpleado(tipo_empleado)
        except ValueError:
            raise HTTPException(status_code=400, detail="Tipo de empleado inválido")
        
        return service.obtener_por_tipo(TipoEmpleado(tipo_empleado))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar empleados por tipo: {str(e)}")
    

@router.put("/{id_empleado}/desactivar")
async def desactivar_empleado(id_empleado: int, service: EmpleadoService = Depends(get_empleado_service)):
    """
    Desactivar un empleado.

    Args:
        id_empleado (int): ID del empleado a desactivar
        service: Servicio de empleado

    Returns:
        dict: Mensaje de confirmación

    Raises:
        HTTPException: Si no se encuentra el empleado
    """
    try:
        service.cambiar_estado(id_empleado, EstadoEmpleado.INACTIVO)
        return {"message": "Empleado desactivado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al desactivar empleado: {str(e)}")
