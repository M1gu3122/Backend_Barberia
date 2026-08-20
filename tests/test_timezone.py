"""
Pruebas unitarias del manejo de zona horaria (America/Bogota).

Se verifica que:
1. crear_cita guarda la fecha como DATETIME naive en hora de Colombia.
2. CitaResponse serializa fecha_hora con offset -05:00.
3. El dashboard usa la fecha de Bogotá cuando no se pasa fecha.
4. auto_completar_citas_vencidas compara con la hora de Bogotá.
5. La fecha_envio de notificaciones se asigna explícita en hora de Bogotá (naive).
"""

import asyncio
from datetime import date, datetime, time, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# Importar todos los modelos para configurar los mappers de SQLAlchemy
import src.models.usuario_model  # noqa: F401
import src.models.empleado_model  # noqa: F401
import src.models.servicio_model  # noqa: F401
import src.models.barberia_model  # noqa: F401
import src.models.cita_servicio_model  # noqa: F401
import src.models.notificacion_model  # noqa: F401
import src.models.barbero_servicio_model  # noqa: F401
import src.models.servicio_barberia_model  # noqa: F401
import src.models.horario_barberia_model  # noqa: F401
import src.models.servicio_adicional_model  # noqa: F401

from src.core.timezone import (
    BOGOTA_TZ,
    a_bogota,
    a_bd,
    desde_bd,
    hoy_bogota,
    ahora_bogota,
)
from src.models.cita_model import Cita, EstadoCita
from src.models.servicio_model import EstadoServicio, TipoServicio
from src.models.usuario_model import EstadoUsuario
from src.models.barberia_model import EstadoBarberia
from src.schemas.cita_schema import CitaCreate, CitaResponse
from src.schemas.notificacion_schema import NotificacionCreate, NotificacionResponse
from src.services.cita_service import CitaService
from src.services.dashboard_service import DashboardService
from src.repositories.notificacion_repository import NotificacionRepository


def _servicio_activo(tiempo_estimado: int = 0) -> SimpleNamespace:
    return SimpleNamespace(
        tiempo_estimado=tiempo_estimado,
        estado_servicio=EstadoServicio.ACTIVO,
        tipo_servicio=TipoServicio.PRINCIPAL,
    )


@pytest.fixture
def cita_service() -> CitaService:
    """CitaService con todos los repositorios mockeados (estilo test_cita_service)."""
    svc = CitaService(db=None)
    svc._db = MagicMock()

    svc._usuario_repo = MagicMock()
    svc._empleado_repo = MagicMock()
    svc._barberia_repo = MagicMock()
    svc._cita_servicio_repo = MagicMock()
    svc._servicio_repo = MagicMock()
    svc._horario_repo = MagicMock()
    svc._barbero_servicio_repo = MagicMock()
    svc._servicio_adicional_repo = MagicMock()
    svc._fecha_no_laboral_repo = MagicMock()

    repo = MagicMock()
    svc._repo = repo
    svc._cita_repo = repo

    svc._usuario_repo.get_by_id.return_value = SimpleNamespace(
        estado=EstadoUsuario.ACTIVO
    )
    svc._empleado_repo.get_empleado.return_value = SimpleNamespace(
        estado="Activo", id_barberia=3
    )
    svc._barberia_repo.get_by_id.return_value = SimpleNamespace(
        estado=EstadoBarberia.ACTIVO
    )
    svc._cita_repo.get_by_barbero.return_value = []
    svc._cita_repo.get_by_cliente.return_value = []
    svc._servicio_repo.get_servicio_by_id.return_value = _servicio_activo()
    svc._barbero_servicio_repo.puede_realizar_todos.return_value = True
    svc._servicio_adicional_repo.get_ids_adicionales_permitidos.return_value = []
    svc._fecha_no_laboral_repo.es_no_laboral.return_value = False
    svc._horario_repo.get_horario_para_fecha.return_value = SimpleNamespace(
        hora_apertura=time.min, hora_cierre=time.max
    )
    repo.existe_cita_solapada.return_value = False
    return svc


def _build_cita(fecha_hora: datetime) -> CitaCreate:
    return CitaCreate(
        fecha_hora=fecha_hora,
        estado_cita=EstadoCita.PENDIENTE,
        id_cliente=1,
        id_barbero=2,
        id_barberia=3,
        ids_servicios=[1],
    )


class TestHelpersCore:

    def test_a_bd_convierte_a_naive_en_bogota(self):
        entrada = datetime(2026, 8, 19, 15, 0, tzinfo=BOGOTA_TZ)
        salida = a_bd(entrada)
        assert salida.tzinfo is None
        assert salida == datetime(2026, 8, 19, 15, 0)

    def test_a_bd_convierte_otra_zona_a_hora_bogota(self):
        from datetime import timezone, timedelta as td

        entrada = datetime(2026, 8, 19, 15, 0, tzinfo=timezone(td(hours=0)))  # UTC
        salida = a_bd(entrada)
        assert salida == datetime(2026, 8, 19, 10, 0)  # 15:00 UTC = 10:00 Bogotá

    def test_desde_bd_adjunta_zona_bogota(self):
        naive = datetime(2026, 8, 19, 10, 0)
        salida = desde_bd(naive)
        assert salida.tzinfo is not None
        assert salida.utcoffset().total_seconds() == -18000  # -05:00


class TestCrearCitaTimezone:

    def test_crear_cita_guarda_naive_en_hora_bogota(self, cita_service):
        cita_service._cita_servicio_repo.create = MagicMock()

        cliente = SimpleNamespace(
            id_usuario=1,
            correo="cliente@test.com",
            nombres="Ana",
            apellidos="Perez",
        )
        cita_service._repo.create.return_value = SimpleNamespace(
            id_cita=1,
            id_cliente=1,
            id_barbero=2,
            id_barberia=3,
            estado_cita=EstadoCita.PENDIENTE,
            fecha_hora=datetime(2026, 8, 19, 10, 0),  # naive Bogotá
            nombres="Ana",
            apellidos="Perez",
            correo="cliente@test.com",
            cliente=cliente,
        )

        ahora_fijo = datetime(2026, 8, 18, 12, 0, tzinfo=BOGOTA_TZ)
        # 15:00 UTC = 10:00 Bogotá
        datos = _build_cita(datetime(2026, 8, 19, 15, 0, tzinfo=timezone.utc))

        async def _send_noop(*args, **kwargs):
            return True

        with patch("src.services.cita_service.ahora_bogota", return_value=ahora_fijo), \
             patch("src.services.cita_service.send_notification", side_effect=_send_noop), \
             patch("src.services.cita_service.schedule_notification", return_value=True):
            asyncio.run(cita_service.crear_cita(datos))

        # Se guardó naive y en hora local de Colombia (10:00, no 15:00)
        assert datos.fecha_hora.tzinfo is None
        assert datos.fecha_hora == datetime(2026, 8, 19, 10, 0)
        # El repo recibió el datetime naive
        creado = cita_service._repo.create.call_args[0][0]
        assert creado.fecha_hora.tzinfo is None


class TestSerializacionCita:

    def test_cita_response_serializa_con_offset_menos_0500(self):
        cita = SimpleNamespace(
            id_cita=1,
            fecha_hora=datetime(2026, 8, 19, 10, 0),  # naive = hora Bogotá
            estado_cita=EstadoCita.PENDIENTE,
            id_cliente=1,
            id_barbero=2,
            id_barberia=3,
            nombres="Ana",
            apellidos="Perez",
            correo="cliente@test.com",
        )
        resultado = CitaResponse.model_validate(cita)
        json_data = resultado.model_dump(mode="json")
        assert json_data["fecha_hora"] == "2026-08-19T10:00:00-05:00"


class TestDashboardBogota:

    def test_resumen_por_dia_usa_hoy_de_bogota(self):
        svc = DashboardService(db=None)
        svc._repo = MagicMock()
        svc._repo.get_resumen_por_dia.return_value = []

        with patch("src.services.dashboard_service.hoy_bogota", return_value=date(2026, 8, 18)):
            svc.get_resumen_por_dia()

        svc._repo.get_resumen_por_dia.assert_called_once_with(date(2026, 8, 18))

    def test_hoy_bogota_es_la_fecha_local_de_colombia(self):
        # 23:30 Bogotá = 04:30 UTC del día siguiente
        instante = datetime(2026, 8, 18, 23, 30, tzinfo=BOGOTA_TZ)
        with patch("src.core.timezone.ahora_bogota", return_value=instante):
            assert hoy_bogota() == date(2026, 8, 18)


class TestAutoCompletarBogota:

    def test_auto_completar_compara_en_hora_bogota(self):
        svc = CitaService(db=None)
        svc._db = MagicMock()

        cita_vencida = Cita(
            id_cita=1,
            fecha_hora=datetime(2026, 8, 18, 10, 0),  # naive Bogotá
            estado_cita=EstadoCita.PENDIENTE,
            id_cliente=1,
            id_barbero=2,
            id_barberia=3,
        )
        cita_futura = Cita(
            id_cita=2,
            fecha_hora=datetime(2026, 8, 18, 13, 0),  # naive Bogotá
            estado_cita=EstadoCita.PENDIENTE,
            id_cliente=1,
            id_barbero=2,
            id_barberia=3,
        )
        svc._db.query.return_value.filter.return_value.all.return_value = [
            cita_vencida,
            cita_futura,
        ]
        svc._calcular_tiempo_servicios = lambda _id: 30  # type: ignore

        ahora_fijo = datetime(2026, 8, 18, 12, 0, tzinfo=BOGOTA_TZ)
        with patch("src.services.cita_service.ahora_bogota", return_value=ahora_fijo):
            actualizadas = svc.auto_completar_citas_vencidas()

        assert actualizadas == 1
        assert cita_vencida.estado_cita == EstadoCita.COMPLETADA
        assert cita_futura.estado_cita == EstadoCita.PENDIENTE


class TestNotificacionFechaEnvio:

    def test_create_asigna_fecha_envio_naive_bogota(self):
        repo = NotificacionRepository(db=MagicMock())
        datos = NotificacionCreate(
            titulo="Hola",
            mensaje="Prueba",
            tipo="Recordatorio",
            id_usuario=1,
        )

        instante = datetime(2026, 8, 18, 23, 30, tzinfo=BOGOTA_TZ)
        with patch("src.repositories.notificacion_repository.ahora_bogota", return_value=instante):
            notificacion = repo.create(datos)

        assert notificacion.fecha_envio.tzinfo is None
        assert notificacion.fecha_envio == datetime(2026, 8, 18, 23, 30)
        repo._db.add.assert_called_once()

    def test_notificacion_response_serializa_con_offset(self):
        notificacion = SimpleNamespace(
            id_notificacion=1,
            titulo="Hola",
            mensaje="Prueba",
            fecha_envio=datetime(2026, 8, 18, 23, 30),  # naive Bogotá
            estado="No Leida",
            tipo="Recordatorio",
            id_usuario=1,
            id_cita=None,
        )
        resultado = NotificacionResponse.model_validate(notificacion)
        json_data = resultado.model_dump(mode="json")
        assert json_data["fecha_envio"] == "2026-08-18T23:30:00-05:00"