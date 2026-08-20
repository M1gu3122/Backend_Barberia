"""
Repositorio para consultas del Dashboard Admin
"""
from typing import List, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract, case

from src.models.cita_model import Cita, EstadoCita
from src.models.empleado_model import Empleado
from src.models.usuario_model import Usuario, EstadoUsuario
from src.models.servicio_model import Servicio
from src.models.cita_servicio_model import CitaServicio

from src.core.timezone import a_bd, hoy_bogota, ahora_bogota


class DashboardRepository:
    """Repositorio para consultas agregadas del dashboard."""

    def __init__(self, db: Session):
        self._db = db

    # ============================================================
    # HELPERS
    # ============================================================

    def _get_today_bounds(self, target_date: date) -> Tuple[datetime, datetime]:
        """Retorna (inicio, fin) del día."""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        return start, end

    def _get_month_bounds(self, year: int, month: int) -> Tuple[datetime, datetime]:
        """Retorna (inicio, fin) del mes."""
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end = datetime(year, month + 1, 1) - timedelta(seconds=1)
        return start, end

    def _get_prev_month(self, year: int, month: int) -> Tuple[int, int]:
        if month == 1:
            return year - 1, 12
        return year, month - 1

    # ============================================================
    # 1. SUMMARY - KPIs + estados de hoy
    # ============================================================





    def get_barberos_activos_count(self) -> int:
        """Cuenta barberos activos."""
        return self._db.query(Empleado).filter(
            Empleado.tipo_empleado == "Barbero",
            Empleado.estado == "Activo"
        ).count()

    def get_clientes_totales_count(self) -> int:
        """Cuenta clientes activos."""
        return self._db.query(Usuario).filter(Usuario.estado == EstadoUsuario.ACTIVO).count()

    def get_ingresos_citas(self, citas: List[Cita]) -> float:
        """Calcula ingresos totales de una lista de citas completadas."""
        if not citas:
            return 0.0
        
        cita_ids = [c.id_cita for c in citas]
        resultado = self._db.query(
            func.sum(Servicio.precio_servicio)
        ).join(CitaServicio, Servicio.id_servicio == CitaServicio.id_servicio).filter(
            CitaServicio.id_cita.in_(cita_ids)
        ).scalar()
        
        return float(resultado) if resultado else 0.0

    # ============================================================
    # 2. PRÓXIMAS CITAS
    # ============================================================

    def get_citas_dia(self, target_date: date) -> List[Cita]:
        """Obtiene todas las citas de un día (todos los estados)."""
        start, end = self._get_today_bounds(target_date)
        return self._db.query(Cita).filter(
            Cita.fecha_hora >= start,
            Cita.fecha_hora <= end
        ).all()

    def get_citas_hoy(self, target_date: Optional[date] = None) -> List[Cita]:
        """Obtiene las citas del día en estados Pendiente, Confirmada o Completada,
        ordenadas por prioridad de estado (Confirmada, Pendiente, Completada)
        y luego por fecha/hora."""
        if target_date is None:
            target_date = hoy_bogota()
        start, end = self._get_today_bounds(target_date)

        estados = [EstadoCita.CONFIRMADA, EstadoCita.PENDIENTE, EstadoCita.COMPLETADA]
        prioridad = case(
            {
                EstadoCita.CONFIRMADA: 1,
                EstadoCita.PENDIENTE: 2,
                EstadoCita.COMPLETADA: 3,
            },
            value=Cita.estado_cita,
        )

        return (
            self._db.query(Cita)
            .filter(
                Cita.fecha_hora >= start,
                Cita.fecha_hora <= end,
                Cita.estado_cita.in_(estados),
            )
            .order_by(prioridad, Cita.fecha_hora.asc())
            .all()
        )

    def get_servicios_cita(self, id_cita: int) -> List[Servicio]:
        """Obtiene servicios de una cita."""
        return self._db.query(Servicio).join(CitaServicio).filter(
            CitaServicio.id_cita == id_cita
        ).all()

    # ============================================================
    # 3. CITAS POR DÍA
    # ============================================================

    def get_citas_por_dia(self, dias: int) -> List[Cita]:
        """Obtiene citas de los últimos N días."""
        fin = a_bd(ahora_bogota())
        inicio = a_bd(ahora_bogota()) - timedelta(days=dias - 1)
        inicio = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return self._db.query(Cita).filter(
            Cita.fecha_hora >= inicio,
            Cita.fecha_hora <= fin
        ).all()

    def get_ingresos_por_citas(self, cita_ids: List[int]) -> float:
        """Calcula ingresos de una lista de IDs de citas."""
        if not cita_ids:
            return 0.0
        
        resultado = self._db.query(
            func.sum(Servicio.precio_servicio)
        ).join(CitaServicio, Servicio.id_servicio == CitaServicio.id_servicio).filter(
            CitaServicio.id_cita.in_(cita_ids)
        ).scalar()
        
        return float(resultado) if resultado else 0.0

    # ============================================================
    # 3.1 RESUMEN AGREGADO (día / semana / mes)
    # ============================================================

    def _get_ingresos_estimados_expr(self):
        """Expresión SQL de ingresos estimados: suma precios de servicios de
        citas Pendiente, Confirmada o Completada."""
        return func.coalesce(
            func.sum(case(
                (
                    Cita.estado_cita.in_([
                        EstadoCita.PENDIENTE,
                        EstadoCita.CONFIRMADA,
                        EstadoCita.COMPLETADA,
                    ]),
                    Servicio.precio_servicio,
                ),
                else_=0,
            )),
            0,
        )

    def get_resumen_por_dia(self, target_date: Optional[date] = None) -> List[tuple]:
        """Resumen del día (por defecto la fecha actual): total, completadas,
        canceladas e ingresos estimados."""
        if target_date is None:
            target_date = hoy_bogota()
        start, end = self._get_today_bounds(target_date)

        return (
            self._db.query(
                func.date(Cita.fecha_hora).label("periodo"),
                func.count(func.distinct(Cita.id_cita)).label("total_citas"),
                func.count(func.distinct(
                    case((Cita.estado_cita == EstadoCita.COMPLETADA, Cita.id_cita))
                )).label("citas_completadas"),
                func.count(func.distinct(
                    case((Cita.estado_cita == EstadoCita.CANCELADA, Cita.id_cita))
                )).label("citas_canceladas"),
                self._get_ingresos_estimados_expr().label("ingresos_estimados"),
            )
            .outerjoin(CitaServicio, Cita.id_cita == CitaServicio.id_cita)
            .outerjoin(Servicio, CitaServicio.id_servicio == Servicio.id_servicio)
            .filter(Cita.fecha_hora >= start, Cita.fecha_hora <= end)
            .group_by(func.date(Cita.fecha_hora))
            .order_by(func.date(Cita.fecha_hora).desc())
            .all()
        )

    def get_resumen_por_semana(self, anio: int, semana: int) -> List[tuple]:
        """Resumen de una semana específica (año ISO + semana ISO):
        total, completadas, canceladas e ingresos estimados."""
        semana_anio = anio * 100 + semana

        return (
            self._db.query(
                func.yearweek(Cita.fecha_hora, 1).label("semana"),
                func.count(func.distinct(Cita.id_cita)).label("total_citas"),
                func.count(func.distinct(
                    case((Cita.estado_cita == EstadoCita.COMPLETADA, Cita.id_cita))
                )).label("citas_completadas"),
                func.count(func.distinct(
                    case((Cita.estado_cita == EstadoCita.CANCELADA, Cita.id_cita))
                )).label("citas_canceladas"),
                self._get_ingresos_estimados_expr().label("ingresos_estimados"),
            )
            .outerjoin(CitaServicio, Cita.id_cita == CitaServicio.id_cita)
            .outerjoin(Servicio, CitaServicio.id_servicio == Servicio.id_servicio)
            .filter(func.yearweek(Cita.fecha_hora, 1) == semana_anio)
            .group_by(func.yearweek(Cita.fecha_hora, 1))
            .order_by(func.yearweek(Cita.fecha_hora, 1).desc())
            .all()
        )

    def get_resumen_por_mes(self, anio: int, mes: int) -> List[tuple]:
        """Resumen de un mes específico: total, completadas, canceladas
        e ingresos estimados."""
        return (
            self._db.query(
                func.year(Cita.fecha_hora).label("anio"),
                func.month(Cita.fecha_hora).label("mes"),
                func.count(func.distinct(Cita.id_cita)).label("total_citas"),
                func.count(func.distinct(
                    case((Cita.estado_cita == EstadoCita.COMPLETADA, Cita.id_cita))
                )).label("citas_completadas"),
                func.count(func.distinct(
                    case((Cita.estado_cita == EstadoCita.CANCELADA, Cita.id_cita))
                )).label("citas_canceladas"),
                self._get_ingresos_estimados_expr().label("ingresos_estimados"),
            )
            .outerjoin(CitaServicio, Cita.id_cita == CitaServicio.id_cita)
            .outerjoin(Servicio, CitaServicio.id_servicio == Servicio.id_servicio)
            .filter(
                func.year(Cita.fecha_hora) == anio,
                func.month(Cita.fecha_hora) == mes,
            )
            .group_by(func.year(Cita.fecha_hora), func.month(Cita.fecha_hora))
            .order_by(func.year(Cita.fecha_hora).desc(), func.month(Cita.fecha_hora).desc())
            .all()
        )

    # ============================================================
    # 3.2 CITAS POR BARBERO (día / semana / mes)
    # ============================================================

    def get_citas_barbero_por_dia(self, target_date: Optional[date] = None) -> List[tuple]:
        """Citas por barbero de un día (por defecto hoy), excluye canceladas."""
        if target_date is None:
            target_date = hoy_bogota()
        start, end = self._get_today_bounds(target_date)

        return (
            self._db.query(
                func.date(Cita.fecha_hora).label("dia"),
                Cita.id_barbero,
                func.concat(Usuario.nombres, " ", Usuario.apellidos).label("barbero"),
                func.count(Cita.id_cita).label("total_citas"),
            )
            .join(Usuario, Cita.id_barbero == Usuario.id_usuario)
            .filter(
                Cita.estado_cita != EstadoCita.CANCELADA,
                Cita.fecha_hora >= start,
                Cita.fecha_hora <= end,
            )
            .group_by(
                func.date(Cita.fecha_hora),
                Cita.id_barbero,
                Usuario.nombres,
                Usuario.apellidos,
            )
            .order_by(
                func.date(Cita.fecha_hora).desc(),
                func.count(Cita.id_cita).desc(),
            )
            .all()
        )

    def get_citas_barbero_por_semana(self, anio: int, semana: int) -> List[tuple]:
        """Citas por barbero de una semana ISO específica (excluye canceladas)."""
        semana_anio = anio * 100 + semana

        return (
            self._db.query(
                func.yearweek(Cita.fecha_hora, 1).label("semana"),
                Cita.id_barbero,
                func.concat(Usuario.nombres, " ", Usuario.apellidos).label("barbero"),
                func.count(Cita.id_cita).label("total_citas"),
            )
            .join(Usuario, Cita.id_barbero == Usuario.id_usuario)
            .filter(
                Cita.estado_cita != EstadoCita.CANCELADA,
                func.yearweek(Cita.fecha_hora, 1) == semana_anio,
            )
            .group_by(
                func.yearweek(Cita.fecha_hora, 1),
                Cita.id_barbero,
                Usuario.nombres,
                Usuario.apellidos,
            )
            .order_by(
                func.yearweek(Cita.fecha_hora, 1).desc(),
                func.count(Cita.id_cita).desc(),
            )
            .all()
        )

    def get_citas_barbero_por_mes(self, anio: int, mes: int) -> List[tuple]:
        """Citas por barbero de un mes específico (excluye canceladas)."""
        return (
            self._db.query(
                func.year(Cita.fecha_hora).label("anio"),
                func.month(Cita.fecha_hora).label("mes"),
                Cita.id_barbero,
                func.concat(Usuario.nombres, " ", Usuario.apellidos).label("barbero"),
                func.count(Cita.id_cita).label("total_citas"),
            )
            .join(Usuario, Cita.id_barbero == Usuario.id_usuario)
            .filter(
                Cita.estado_cita != EstadoCita.CANCELADA,
                func.year(Cita.fecha_hora) == anio,
                func.month(Cita.fecha_hora) == mes,
            )
            .group_by(
                func.year(Cita.fecha_hora),
                func.month(Cita.fecha_hora),
                Cita.id_barbero,
                Usuario.nombres,
                Usuario.apellidos,
            )
            .order_by(
                func.year(Cita.fecha_hora).desc(),
                func.month(Cita.fecha_hora).desc(),
                func.count(Cita.id_cita).desc(),
            )
            .all()
        )

    # ============================================================
    # 4. TOP SERVICIOS
    # ============================================================

    def get_top_servicios_mes(self, year: int, month: int, limit: int = 5) -> List[tuple]:
        """Obtiene los servicios más solicitados en un mes."""
        start, end = self._get_month_bounds(year, month)
        
        # Subquery para citas completadas del mes
        citas_completadas = self._db.query(Cita.id_cita).filter(
            Cita.fecha_hora >= start,
            Cita.fecha_hora <= end,
            Cita.estado_cita == EstadoCita.COMPLETADA
        ).subquery()
        
        # Contar servicios
        resultado = self._db.query(
            CitaServicio.id_servicio,
            func.count(CitaServicio.id_servicio).label('total')
        ).filter(
            CitaServicio.id_cita.in_(citas_completadas.select())
        ).group_by(CitaServicio.id_servicio).order_by(
            func.count(CitaServicio.id_servicio).desc()
        ).limit(limit).all()
        
        return resultado

    # ============================================================
    # 5. RENDIMIENTO BARBEROS
    # ============================================================

    def get_barberos_activos(self) -> List[Empleado]:
        """Obtiene barberos activos."""
        return self._db.query(Empleado).filter(
            Empleado.tipo_empleado == "Barbero",
            Empleado.estado == "Activo"
        ).all()

    def get_citas_barbero_mes(self, id_barbero: int, year: int, month: int) -> List[Cita]:
        """Obtiene citas de un barbero en un mes."""
        start, end = self._get_month_bounds(year, month)
        return self._db.query(Cita).filter(
            Cita.id_barbero == id_barbero,
            Cita.fecha_hora >= start,
            Cita.fecha_hora <= end
        ).all()

    # ============================================================
    # 6. INGRESOS COMPARATIVO
    # ============================================================

    def get_ingresos_mes(self, year: int, month: int) -> Tuple[float, int]:
        """Retorna (ingresos_totales, citas_completadas) de un mes."""
        start, end = self._get_month_bounds(year, month)
        
        citas = self._db.query(Cita).filter(
            Cita.fecha_hora >= start,
            Cita.fecha_hora <= end,
            Cita.estado_cita == EstadoCita.COMPLETADA
        ).all()
        
        ingresos = self.get_ingresos_citas(citas)
        return ingresos, len(citas)

    # ============================================================
    # 7. CANCELACIONES
    # ============================================================

    def get_citas_mes(self, year: int, month: int) -> List[Cita]:
        """Obtiene todas las citas de un mes."""
        start, end = self._get_month_bounds(year, month)
        return self._db.query(Cita).filter(
            Cita.fecha_hora >= start,
            Cita.fecha_hora <= end
        ).all()

    # ============================================================
    # 8. CLIENTES NUEVOS
    # ============================================================

    def get_citas_mes_agrupadas_por_cliente(self, year: int, month: int) -> List[tuple]:
        """Obtiene citas del mes agrupadas por cliente."""
        start, end = self._get_month_bounds(year, month)
        start_dt = datetime.combine(start.date(), datetime.min.time())
        end_dt = datetime.combine(end.date(), datetime.max.time())
        
        return self._db.query(
            Cita.id_cliente,
            func.count(Cita.id_cita).label('total_citas')
        ).filter(
            Cita.fecha_hora >= start_dt,
            Cita.fecha_hora <= end_dt
        ).group_by(Cita.id_cliente).all()

    def get_citas_mes_para_semanas(self, year: int, month: int) -> List[Cita]:
        """Obtiene citas del mes para agrupación semanal."""
        start, end = self._get_month_bounds(year, month)
        start_dt = datetime.combine(start.date(), datetime.min.time())
        end_dt = datetime.combine(end.date(), datetime.max.time())
        
        return self._db.query(Cita).filter(
            Cita.fecha_hora >= start_dt,
            Cita.fecha_hora <= end_dt
        ).all()
        
        
    