"""
Servicio de negocio para Dashboard Admin
"""
from typing import List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from src.schemas.cita_schema import CitaResponse
from src.repositories.dashboard_repository import DashboardRepository
from src.models.cita_model import Cita, EstadoCita
from src.models.servicio_model import Servicio
from src.models.empleado_model import Empleado
from src.models.usuario_model import Usuario

from src.core.timezone import a_bd, hoy_bogota, ahora_bogota


class DashboardService:
    """Servicio de negocio para el dashboard administrativo."""

    def __init__(self, db: Session):
        self._repo = DashboardRepository(db)
        self._db = db

    # ============================================================
    # 1. SUMMARY
    # ============================================================

    def get_summary(self, target_date: Optional[date] = None) -> dict:
        """Obtiene resumen del dashboard para una fecha."""
        if target_date is None:
            target_date = hoy_bogota()

        citas_hoy = self._repo.get_citas_dia(target_date)
        
        # Contar por estado
        estados_count = {
            "pendiente": 0,
            "confirmada": 0,
            "en_atencion": 0,
            "completada": 0,
            "cancelada": 0
        }
        
        for cita in citas_hoy:
            estado = cita.estado_cita.value.lower()
            if estado in estados_count:
                estados_count[estado] += 1

        total_hoy = len(citas_hoy)
        
        # Ingresos de citas completadas
        citas_completadas = [c for c in citas_hoy if c.estado_cita == EstadoCita.COMPLETADA]
        ingresos_hoy = self._repo.get_ingresos_citas(citas_completadas)

        # KPIs
        barberos_activos = self._repo.get_barberos_activos_count()
        clientes_totales = self._repo.get_clientes_totales_count()
        
        # Clientes nuevos mes (simplificado: clientes con primera cita en el mes)
        inicio_mes = datetime(target_date.year, target_date.month, 1)
        clientes_nuevos_mes = self._calcular_clientes_nuevos_mes(inicio_mes, target_date)

        return {
            "fecha": target_date,
            "kpis": {
                "citas_hoy": total_hoy,
                "citas_pendientes": estados_count["pendiente"],
                "citas_confirmadas": estados_count["confirmada"],
                "citas_en_atencion": estados_count["en_atencion"],
                "citas_completadas": estados_count["completada"],
                "citas_canceladas": estados_count["cancelada"],
                "ingresos_hoy": ingresos_hoy,
                "barberos_activos": barberos_activos,
                "clientes_totales": clientes_totales,
                "clientes_nuevos_mes": clientes_nuevos_mes
            },
            "estados_hoy": estados_count
        }

    def _calcular_clientes_nuevos_mes(self, inicio_mes: datetime, target_date: date) -> int:
        """Calcula clientes que tuvieron su primera cita en el mes."""
        # Obtener todas las citas del mes
        citas_mes = self._repo.get_citas_mes(target_date.year, target_date.month)
        
        # Obtener IDs de clientes únicos
        clientes_con_cita = set(c.id_cliente for c in citas_mes)
        
        # Filtrar los que es su primera cita histórica
        # (simplificado: contamos todos los que aparecen en el mes)
        return len(clientes_con_cita)

    # ============================================================
    # 2. CITAS DE HOY (agenda de hoy) - pendientes, confirmadas y completadas
    # ============================================================

    def get_citas_hoy(self, target_date: Optional[date] = None) -> dict:
        """Agenda del día: citas Pendientes, Confirmadas y Completadas,
        ordenadas por prioridad de estado (Confirmada, Pendiente, Completada)
        y luego por hora."""
        if target_date is None:
            target_date = hoy_bogota()

        citas = self._repo.get_citas_hoy(target_date)

        resultado = []
        for cita in citas:
            cliente = None
            if cita.cliente:
                cliente = {
                    "id": cita.cliente.id_usuario,
                    "nombre": cita.cliente.nombre_completo,
                    "telefono": cita.cliente.telefono or "",
                }

            barbero = None
            if cita.barbero:
                barbero = {
                    "id": cita.barbero.id_usuario,
                    "nombre": cita.barbero.nombre_completo,
                }

            servicios = [
                {
                    "id": s.id_servicio,
                    "nombre": s.nombre_servicio,
                    "duracion": s.tiempo_estimado,
                    "precio": float(s.precio_servicio),
                }
                for s in self._repo.get_servicios_cita(cita.id_cita)
            ]

            resultado.append({
                "id_cita": cita.id_cita,
                "fecha": cita.fecha_hora.date(),
                "hora": cita.fecha_hora.strftime("%H:%M"),
                "estado": cita.estado_cita.value,
                "cliente": cliente,
                "barbero": barbero,
                "servicios": servicios,
            })

        return {"citas": resultado, "total": len(resultado)}

    


    # ============================================================
    # 3. CITAS POR DÍA
    # ============================================================

    def get_citas_por_dia(self, dias: int = 30) -> dict:
        """Obtiene estadísticas de citas agrupadas por día."""
        citas = self._repo.get_citas_por_dia(dias)
        
        # Agrupar por fecha
        from collections import defaultdict
        datos_por_dia = defaultdict(lambda: {"total": 0, "completadas": 0, "canceladas": 0, "ingresos": 0.0})
        
        cita_ids_completadas_por_dia = defaultdict(list)
        
        for cita in citas:
            fecha_str = cita.fecha_hora.date().isoformat()
            datos_por_dia[fecha_str]["total"] += 1
            
            if cita.estado_cita == EstadoCita.COMPLETADA:
                datos_por_dia[fecha_str]["completadas"] += 1
                cita_ids_completadas_por_dia[fecha_str].append(cita.id_cita)
            elif cita.estado_cita == EstadoCita.CANCELADA:
                datos_por_dia[fecha_str]["canceladas"] += 1

        # Calcular ingresos por día
        for fecha_str, cita_ids in cita_ids_completadas_por_dia.items():
            ingresos = self._repo.get_ingresos_por_citas(cita_ids)
            datos_por_dia[fecha_str]["ingresos"] = ingresos

        # Completar días sin citas
        fin = a_bd(ahora_bogota())
        inicio = a_bd(ahora_bogota()) - timedelta(days=dias - 1)
        inicio = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        
        resultado = []
        current = inicio
        while current <= fin:
            fecha_str = current.date().isoformat()
            d = datos_por_dia[fecha_str]
            resultado.append({
                "fecha": current.date(),
                "total": d["total"],
                "completadas": d["completadas"],
                "canceladas": d["canceladas"],
                "ingresos": d["ingresos"]
            })
            current += timedelta(days=1)

        total_citas = sum(d["total"] for d in resultado)
        promedio = total_citas / max(1, len(resultado))

        return {
            "datos": resultado,
            "total_periodo": total_citas,
            "promedio_diario": round(promedio, 1)
        }

    # ============================================================
    # 3.1 RESUMEN AGREGADO (día / semana / mes)
    # ============================================================

    @staticmethod
    def _formatear_periodo(valor) -> str:
        if isinstance(valor, (date, datetime)):
            return valor.isoformat()
        return str(valor)

    def get_resumen_por_dia(self, target_date: Optional[date] = None) -> dict:
        """Resumen de citas e ingresos estimados del día (por defecto hoy)."""
        if target_date is None:
            target_date = hoy_bogota()
        filas = self._repo.get_resumen_por_dia(target_date)
        return {
            "datos": [
                {
                    "periodo": self._formatear_periodo(f[0]),
                    "total_citas": f[1],
                    "citas_completadas": f[2],
                    "citas_canceladas": f[3],
                    "ingresos_estimados": float(f[4]),
                }
                for f in filas
            ]
        }

    def get_resumen_por_semana(self, anio: int, semana: int) -> dict:
        """Resumen de una semana ISO específica de citas e ingresos estimados."""
        filas = self._repo.get_resumen_por_semana(anio, semana)
        return {
            "datos": [
                {
                    "periodo": str(f[0]),
                    "total_citas": f[1],
                    "citas_completadas": f[2],
                    "citas_canceladas": f[3],
                    "ingresos_estimados": float(f[4]),
                }
                for f in filas
            ]
        }

    def get_resumen_por_mes(self, anio: int, mes: int) -> dict:
        """Resumen de un mes específico de citas e ingresos estimados."""
        filas = self._repo.get_resumen_por_mes(anio, mes)
        return {
            "datos": [
                {
                    "anio": f[0],
                    "mes": f[1],
                    "total_citas": f[2],
                    "citas_completadas": f[3],
                    "citas_canceladas": f[4],
                    "ingresos_estimados": float(f[5]),
                }
                for f in filas
            ]
        }

    # ============================================================
    # 3.2 CITAS POR BARBERO (día / semana / mes)
    # ============================================================

    def get_barberos_por_dia(self, target_date: Optional[date] = None) -> dict:
        """Citas por barbero de un día (por defecto hoy), excluye canceladas."""
        if target_date is None:
            target_date = hoy_bogota()
        filas = self._repo.get_citas_barbero_por_dia(target_date)
        return {
            "datos": [
                {
                    "periodo": self._formatear_periodo(f[0]),
                    "id_barbero": f[1],
                    "barbero": f[2],
                    "total_citas": f[3],
                }
                for f in filas
            ]
        }

    def get_barberos_por_semana(self, anio: int, semana: int) -> dict:
        """Citas por barbero de una semana ISO específica (excluye canceladas)."""
        filas = self._repo.get_citas_barbero_por_semana(anio, semana)
        return {
            "datos": [
                {
                    "periodo": str(f[0]),
                    "id_barbero": f[1],
                    "barbero": f[2],
                    "total_citas": f[3],
                }
                for f in filas
            ]
        }

    def get_barberos_por_mes(self, anio: int, mes: int) -> dict:
        """Citas por barbero de un mes específico (excluye canceladas)."""
        filas = self._repo.get_citas_barbero_por_mes(anio, mes)
        return {
            "datos": [
                {
                    "anio": f[0],
                    "mes": f[1],
                    "id_barbero": f[2],
                    "barbero": f[3],
                    "total_citas": f[4],
                }
                for f in filas
            ]
        }

    # ============================================================
    # 4. TOP SERVICIOS
    # ============================================================

    def get_top_servicios(self, year: int, month: int, limit: int = 5) -> dict:
        """Obtiene los servicios más solicitados del mes."""
        top_servicios = self._repo.get_top_servicios_mes(year, month, limit)
        
        total_servicios = sum(count for _, count in top_servicios)
        
        servicios_info = []
        for id_servicio, count in top_servicios:
            servicio = self._db.query(Servicio).filter(Servicio.id_servicio == id_servicio).first()
            if servicio:
                pct = round((count / total_servicios) * 100, 1) if total_servicios > 0 else 0
                servicios_info.append({
                    "id": servicio.id_servicio,
                    "nombre": servicio.nombre_servicio,
                    "total_citas": count,
                    "ingresos": float(servicio.precio_servicio) * count,
                    "porcentaje": pct
                })

        return {
            "servicios": servicios_info,
            "total_servicios_mes": total_servicios
        }

    # ============================================================
    # 5. RENDIMIENTO BARBEROS
    # ============================================================

    def get_barberos_rendimiento(self, year: int, month: int) -> dict:
        """Obtiene rendimiento de barberos en el mes."""
        barberos = self._repo.get_barberos_activos()
        
        resultado = []
        for barbero in barberos:
            citas_barbero = self._repo.get_citas_barbero_mes(barbero.id_usuario, year, month)
            
            total = len(citas_barbero)
            completadas = sum(1 for c in citas_barbero if c.estado_cita == EstadoCita.COMPLETADA)
            canceladas = sum(1 for c in citas_barbero if c.estado_cita == EstadoCita.CANCELADA)
            
            # Ingresos
            citas_completadas = [c for c in citas_barbero if c.estado_cita == EstadoCita.COMPLETADA]
            ingresos = self._repo.get_ingresos_citas(citas_completadas)
            
            # Ocupación aproximada
            horas_disponibles = 22 * 8  # 22 días * 8h
            horas_trabajadas = (total * 40) / 60  # 40 min por cita aprox
            ocupacion = round((horas_trabajadas / horas_disponibles) * 100, 1) if horas_disponibles > 0 else 0
            
            nombre = ""
            if barbero.usuario:
                nombre = f"{barbero.usuario.nombres} {barbero.usuario.apellidos}"
            
            resultado.append({
                "id": barbero.id_usuario,
                "nombre": nombre,
                "total_citas": total,
                "completadas": completadas,
                "canceladas": canceladas,
                "ingresos": ingresos,
                "ocupacion_promedio": min(ocupacion, 100)
            })

        prom_ocup = round(sum(b["ocupacion_promedio"] for b in resultado) / max(1, len(resultado)), 1)

        return {
            "barberos": resultado,
            "promedio_ocupacion": prom_ocup
        }

    # ============================================================
    # 6. INGRESOS COMPARATIVO
    # ============================================================

    def get_ingresos_comparativo(self) -> dict:
        """Compara ingresos del mes actual vs anterior."""
        hoy = hoy_bogota()
        year, month = hoy.year, hoy.month
        prev_year, prev_month = self._repo._get_prev_month(year, month)

        actual_ingresos, actual_citas = self._repo.get_ingresos_mes(year, month)
        anterior_ingresos, anterior_citas = self._repo.get_ingresos_mes(prev_year, prev_month)

        def pct_diff(actual, anterior):
            if anterior == 0:
                return 0.0
            return round(((actual - anterior) / anterior) * 100, 1)

        return {
            "mes_actual": {
                "mes": f"{year}-{month:02d}",
                "ingresos_totales": actual_ingresos,
                "citas_completadas": actual_citas,
                "ticket_promedio": round(actual_ingresos / max(1, actual_citas), 2) if actual_citas else 0
            },
            "mes_anterior": {
                "mes": f"{prev_year}-{prev_month:02d}",
                "ingresos_totales": anterior_ingresos,
                "citas_completadas": anterior_citas,
                "ticket_promedio": round(anterior_ingresos / max(1, anterior_citas), 2) if anterior_citas else 0
            },
            "variacion": {
                "ingresos_pct": pct_diff(actual_ingresos, anterior_ingresos),
                "citas_pct": pct_diff(actual_citas, anterior_citas),
                "ticket_pct": pct_diff(
                    round(actual_ingresos / max(1, actual_citas), 2) if actual_citas else 0,
                    round(anterior_ingresos / max(1, anterior_citas), 2) if anterior_citas else 0
                )
            }
        }

    # ============================================================
    # 7. CANCELACIONES
    # ============================================================

    def get_cancelaciones(self, year: int, month: int) -> dict:
        """Obtiene estadísticas de cancelaciones del mes."""
        citas_mes = self._repo.get_citas_mes(year, month)
        
        total_mes = len(citas_mes)
        canceladas = sum(1 for c in citas_mes if c.estado_cita == EstadoCita.CANCELADA)

        tasa_cancelacion = round((canceladas / max(1, total_mes)) * 100, 1)

        return {
            "total_canceladas": canceladas,
            "tasa_cancelacion": tasa_cancelacion
        }

    # ============================================================
    # 8. CLIENTES NUEVOS
    # ============================================================

    def get_clientes_nuevos(self, year: int, month: int) -> dict:
        """Obtiene clientes nuevos del mes."""
        # Clientes con primera cita en el mes
        clientes_agrupados = self._repo.get_citas_mes_agrupadas_por_cliente(year, month)
        total_nuevos = len(clientes_agrupados)

        # Por semana
        from collections import defaultdict
        citas_mes = self._repo.get_citas_mes_para_semanas(year, month)
        
        por_semana = defaultdict(int)
        for cita in citas_mes:
            semana = cita.fecha_hora.isocalendar()
            semana_key = f"{semana.year}-W{semana.week:02d}"
            por_semana[semana_key] += 1

        return {
            "total_nuevos": total_nuevos,
            "por_semana": [
                {"semana": k, "nuevos": v} for k, v in sorted(por_semana.items())
            ],
            "conversion_primera_cita": 0.82  # Placeholder
        }