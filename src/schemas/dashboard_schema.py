"""
Esquemas Pydantic para Dashboard Admin
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date
from decimal import Decimal


class KPIsResponse(BaseModel):
    citas_hoy: int
    citas_pendientes: int
    citas_confirmadas: int
    citas_en_atencion: int
    citas_completadas: int
    citas_canceladas: int
    ingresos_hoy: float
    barberos_activos: int
    clientes_totales: int
    clientes_nuevos_mes: int


class EstadosHoyResponse(BaseModel):
    pendiente: int
    confirmada: int
    en_atencion: int
    completada: int
    cancelada: int


class DashboardSummaryResponse(BaseModel):
    fecha: date
    kpis: KPIsResponse
    estados_hoy: EstadosHoyResponse


class ServicioCitaResponse(BaseModel):
    id: int
    nombre: str
    duracion: int
    precio: float


class ClienteResumenResponse(BaseModel):
    id: int
    nombre: str
    telefono: str


class BarberoResumenResponse(BaseModel):
    id: int
    nombre: str


class ProximaCitaResponse(BaseModel):
    id_cita: int
    fecha: date
    hora: str
    estado: str
    cliente: Optional[ClienteResumenResponse] = None
    barbero: Optional[BarberoResumenResponse] = None
    servicios: List[ServicioCitaResponse]


class ProximasCitasResponse(BaseModel):
    citas: List[ProximaCitaResponse]
    total: int


class CitasPorDiaItem(BaseModel):
    fecha: date
    total: int
    completadas: int
    canceladas: int
    ingresos: float


class CitasPorDiaResponse(BaseModel):
    datos: List[CitasPorDiaItem]
    total_periodo: int
    promedio_diario: float


class ResumenPeriodoItem(BaseModel):
    periodo: str
    total_citas: int
    citas_completadas: int
    citas_canceladas: int
    ingresos_estimados: float


class ResumenPeriodoResponse(BaseModel):
    datos: List[ResumenPeriodoItem]


class ResumenMesItem(BaseModel):
    anio: int
    mes: int
    total_citas: int
    citas_completadas: int
    citas_canceladas: int
    ingresos_estimados: float


class ResumenMesResponse(BaseModel):
    datos: List[ResumenMesItem]


class BarberoPeriodoItem(BaseModel):
    periodo: str
    id_barbero: int
    barbero: str
    total_citas: int


class BarberoPeriodoResponse(BaseModel):
    datos: List[BarberoPeriodoItem]


class BarberoMesItem(BaseModel):
    anio: int
    mes: int
    id_barbero: int
    barbero: str
    total_citas: int


class BarberoMesResponse(BaseModel):
    datos: List[BarberoMesItem]


class TopServicioItem(BaseModel):
    id: int
    nombre: str
    total_citas: int
    ingresos: float
    porcentaje: float


class TopServiciosResponse(BaseModel):
    servicios: List[TopServicioItem]
    total_servicios_mes: int


class BarberoRendimientoItem(BaseModel):
    id: int
    nombre: str
    total_citas: int
    completadas: int
    canceladas: int
    ingresos: float
    ocupacion_promedio: float


class BarberoRendimientoResponse(BaseModel):
    barberos: List[BarberoRendimientoItem]
    promedio_ocupacion: float


class IngresosMesResponse(BaseModel):
    mes: str
    ingresos_totales: float
    citas_completadas: int
    ticket_promedio: float


class VariacionResponse(BaseModel):
    ingresos_pct: float
    citas_pct: float
    ticket_pct: float


class IngresosComparativoResponse(BaseModel):
    mes_actual: IngresosMesResponse
    mes_anterior: IngresosMesResponse
    variacion: VariacionResponse


class CancelacionesResponse(BaseModel):
    total_canceladas: int
    tasa_cancelacion: float


class ClientesPorSemana(BaseModel):
    semana: str
    nuevos: int


class ClientesNuevosResponse(BaseModel):
    total_nuevos: int
    por_semana: List[ClientesPorSemana]
    conversion_primera_cita: float