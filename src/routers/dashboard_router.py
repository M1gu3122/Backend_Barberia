"""
Router para Dashboard Admin
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from src.schemas.cita_schema import CitaResponse
from src.services.cita_service import CitaService
from src.config.database import get_db
from src.services.dashboard_service import DashboardService
from src.core.timezone import hoy_bogota
from src.schemas.dashboard_schema import (
    DashboardSummaryResponse,
    ProximasCitasResponse,
    CitasPorDiaResponse,
    ResumenPeriodoResponse,
    ResumenMesResponse,
    BarberoPeriodoResponse,
    BarberoMesResponse,
    TopServiciosResponse,
    BarberoRendimientoResponse,
    IngresosComparativoResponse,
    CancelacionesResponse,
    ClientesNuevosResponse
)


def get_cita_service(db: Session = Depends(get_db)):
    return CitaService(db)


def get_cita_service(db: Session = Depends(get_db)):
    return CitaService(db)

router = APIRouter(
    prefix="/admin/dashboard",
    tags=["Dashboard Admin"],
    responses={404: {"description": "No encontrado"}}
)


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


def _parse_fecha(fecha: Optional[str]) -> Optional[date]:
    """Parsea una fecha YYYY-MM-DD o retorna None si no es válida."""
    if not fecha:
        return None
    try:
        return date.fromisoformat(fecha)
    except ValueError:
        return None


# ============================================================
# 1. SUMMARY - KPIs + estados de hoy
# ============================================================
@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    fecha: Optional[str] = Query(None, description="Fecha YYYY-MM-DD (default: hoy)"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    KPIs principales + distribución de estados para el día.
    """
    target_date = None
    if fecha:
        try:
            target_date = date.fromisoformat(fecha)
        except ValueError:
            target_date = hoy_bogota()
    else:
        target_date = hoy_bogota()

    return service.get_summary(target_date)



# ============================================================
# 2. PRÓXIMAS CITAS (agenda de hoy)
# ============================================================
@router.get("/proximas-citas", response_model=ProximasCitasResponse)
async def get_proximas_citas(
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Agenda del día: citas Pendientes, Confirmadas y Completadas,
    ordenadas por prioridad de estado y hora.
    """
    return service.get_citas_hoy()



# ============================================================
# 3. CITAS POR DÍA (últimos N días) - para gráfico de barras
# ============================================================
@router.get("/citas-por-dia", response_model=CitasPorDiaResponse)
async def get_citas_por_dia(
    dias: int = Query(30, ge=7, le=90),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Agrupación de citas por día para gráfico de barras.
    """
    return service.get_citas_por_dia(dias)


# ============================================================
# 3.1 RESUMEN AGREGADO (día / semana / mes)
# ============================================================
@router.get("/resumen-por-dia", response_model=ResumenPeriodoResponse)
async def get_resumen_por_dia(
    fecha: Optional[str] = Query(None, description="Fecha YYYY-MM-DD (default: hoy)"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Resumen del día: total, completadas, canceladas e ingresos estimados.
    """
    target_date = _parse_fecha(fecha) or hoy_bogota()
    return service.get_resumen_por_dia(target_date)


@router.get("/resumen-por-semana", response_model=ResumenPeriodoResponse)
async def get_resumen_por_semana(
    anio: Optional[int] = Query(None, description="Año ISO de la semana (default: año actual)"),
    semana: Optional[int] = Query(None, ge=1, le=53, description="Semana ISO 1-53 (default: semana actual)"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Resumen de una semana: total, completadas, canceladas e ingresos estimados.
    Por defecto usa la semana en curso.
    """
    hoy = hoy_bogota()
    iso = hoy.isocalendar()
    anio_obj = anio if anio is not None else iso.year
    semana_obj = semana if semana is not None else iso.week
    return service.get_resumen_por_semana(anio_obj, semana_obj)


@router.get("/resumen-por-mes", response_model=ResumenMesResponse)
async def get_resumen_por_mes(
    anio: Optional[int] = Query(None, description="Año (default: año actual)"),
    mes: Optional[int] = Query(None, ge=1, le=12, description="Mes 1-12 (default: mes actual)"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Resumen de un mes: total, completadas, canceladas e ingresos estimados.
    Por defecto usa el mes en curso.
    """
    hoy = hoy_bogota()
    anio_obj = anio if anio is not None else hoy.year
    mes_obj = mes if mes is not None else hoy.month
    return service.get_resumen_por_mes(anio_obj, mes_obj)


# ============================================================
# 3.2 CITAS POR BARBERO (día / semana / mes)
# ============================================================
@router.get("/barberos-por-dia", response_model=BarberoPeriodoResponse)
async def get_barberos_por_dia(
    fecha: Optional[str] = Query(None, description="Fecha YYYY-MM-DD (default: hoy)"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Citas por barbero del día (excluye canceladas). Por defecto usa hoy.
    """
    target_date = _parse_fecha(fecha) or hoy_bogota()
    return service.get_barberos_por_dia(target_date)


@router.get("/barberos-por-semana", response_model=BarberoPeriodoResponse)
async def get_barberos_por_semana(
    anio: Optional[int] = Query(None, description="Año ISO de la semana (default: año actual)"),
    semana: Optional[int] = Query(None, ge=1, le=53, description="Semana ISO 1-53 (default: semana actual)"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Citas por barbero de una semana (excluye canceladas). Por defecto usa la semana en curso.
    """
    hoy = hoy_bogota()
    iso = hoy.isocalendar()
    anio_obj = anio if anio is not None else iso.year
    semana_obj = semana if semana is not None else iso.week
    return service.get_barberos_por_semana(anio_obj, semana_obj)


@router.get("/barberos-por-mes", response_model=BarberoMesResponse)
async def get_barberos_por_mes(
    anio: Optional[int] = Query(None, description="Año (default: año actual)"),
    mes: Optional[int] = Query(None, ge=1, le=12, description="Mes 1-12 (default: mes actual)"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Citas por barbero de un mes (excluye canceladas). Por defecto usa el mes en curso.
    """
    hoy = hoy_bogota()
    anio_obj = anio if anio is not None else hoy.year
    mes_obj = mes if mes is not None else hoy.month
    return service.get_barberos_por_mes(anio_obj, mes_obj)


# ============================================================
# 4. TOP SERVICIOS (mes actual)
# ============================================================
@router.get("/top-servicios", response_model=TopServiciosResponse)
async def get_top_servicios(
    mes: Optional[str] = Query(None, description="YYYY-MM (default: mes actual)"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Top 5 servicios más solicitados en el mes.
    """
    hoy = hoy_bogota()
    year, month = hoy.year, hoy.month
    
    if mes:
        try:
            year, month = map(int, mes.split("-"))
        except (ValueError, AttributeError):
            pass

    return service.get_top_servicios(year, month)


# ============================================================
# 5. RENDIMIENTO BARBEROS (mes actual)
# ============================================================
@router.get("/barberos-rendimiento", response_model=BarberoRendimientoResponse)
async def get_barberos_rendimiento(
    mes: Optional[str] = Query(None, description="YYYY-MM (default: mes actual)"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Rendimiento de barberos en el mes: citas, ingresos, ocupación.
    """
    hoy = hoy_bogota()
    year, month = hoy.year, hoy.month
    
    if mes:
        try:
            year, month = map(int, mes.split("-"))
        except (ValueError, AttributeError):
            pass

    return service.get_barberos_rendimiento(year, month)


# ============================================================
# 6. INGRESOS COMPARATIVO (mes vs mes anterior)
# ============================================================
@router.get("/ingresos-comparativo", response_model=IngresosComparativoResponse)
async def get_ingresos_comparativo(
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Comparación de ingresos: mes actual vs mes anterior.
    """
    return service.get_ingresos_comparativo()


# ============================================================
# 7. CANCELACIONES (mes actual)
# ============================================================
@router.get("/cancelaciones", response_model=CancelacionesResponse)
async def get_cancelaciones(
    mes: Optional[str] = Query(None, description="YYYY-MM (default: mes actual)"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Tasa de cancelación, no-shows y motivos del mes.
    """
    hoy = hoy_bogota()
    year, month = hoy.year, hoy.month
    
    if mes:
        try:
            year, month = map(int, mes.split("-"))
        except (ValueError, AttributeError):
            pass

    return service.get_cancelaciones(year, month)


# ============================================================
# 8. CLIENTES NUEVOS (mes actual)
# ============================================================
@router.get("/clientes-nuevos", response_model=ClientesNuevosResponse)
async def get_clientes_nuevos(
    mes: Optional[str] = Query(None, description="YYYY-MM (default: mes actual)"),
    service: DashboardService = Depends(get_dashboard_service)
):
    """
    Clientes registrados en el mes + conversión primera cita.
    """
    hoy = hoy_bogota()
    year, month = hoy.year, hoy.month
    
    if mes:
        try:
            year, month = map(int, mes.split("-"))
        except (ValueError, AttributeError):
            pass

    return service.get_clientes_nuevos(year, month)


