"""
Pruebas unitarias para el método crear_cita de CitaService.
Se mockean los repositorios para no depender de la base de datos.
"""

from datetime import datetime, timedelta, time
from types import SimpleNamespace
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

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

from src.models.cita_model import Cita, EstadoCita
from src.models.servicio_model import EstadoServicio, TipoServicio
from src.models.usuario_model import EstadoUsuario
from src.models.barberia_model import EstadoBarberia
from src.schemas.cita_schema import CitaCreate
from src.services.cita_service import CitaService

COL_TZ = ZoneInfo("America/Bogota")


def _servicio_activo(
    tiempo_estimado: int = 0, tipo: TipoServicio = TipoServicio.PRINCIPAL
) -> SimpleNamespace:
    """Servicio mock activo para las pruebas."""
    return SimpleNamespace(
        tiempo_estimado=tiempo_estimado,
        estado_servicio=EstadoServicio.ACTIVO,
        tipo_servicio=tipo,
    )


def _fecha_futura(dias: int = 1, horas: int = 0) -> datetime:
    """Devuelve una fecha futura (con timezone) para pruebas válidas."""
    return datetime.now(COL_TZ) + timedelta(days=dias, hours=horas)


def _build_cita(fecha_hora: datetime) -> CitaCreate:
    return CitaCreate(
        fecha_hora=fecha_hora,
        estado_cita=EstadoCita.PENDIENTE,
        id_cliente=1,
        id_barbero=2,
        id_barberia=3,
        ids_servicios=[1, 2],
    )


@pytest.fixture
def service() -> CitaService:
    """CitaService con todos los repositorios mockeados."""
    svc = CitaService(db=None)

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

    # Comportamiento por defecto: cliente activo, barbero activo y sin citas
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
    return svc


class TestCrearCita:

    def test_crear_cita_exitosa(self, service):
        fecha = _fecha_futura()
        datos = _build_cita(fecha)

        cita_orm = Cita(
            id_cita=1,
            fecha_hora=fecha,
            estado_cita=EstadoCita.PENDIENTE,
            id_cliente=1,
            id_barbero=2,
            id_barberia=3,
        )
        service._repo.create.return_value = cita_orm

        resultado = service.crear_cita(datos)

        assert resultado.id_cita == 1
        service._repo.create.assert_called_once_with(datos)

    def test_crear_cita_fecha_naive_futura(self, service):
        """Una fecha naive futura se asume en America/Bogota y debe crear la cita."""
        fecha_naive = datetime.now() + timedelta(days=1)
        datos = _build_cita(fecha_naive)

        cita_orm = Cita(
            id_cita=2,
            fecha_hora=fecha_naive,
            estado_cita=EstadoCita.PENDIENTE,
            id_cliente=1,
            id_barbero=2,
            id_barberia=3,
        )
        service._repo.create.return_value = cita_orm

        resultado = service.crear_cita(datos)

        assert resultado.id_cita == 2
        service._repo.create.assert_called_once()

    def test_cliente_inactivo(self, service):
        service._usuario_repo.get_by_id.return_value = SimpleNamespace(
            estado=EstadoUsuario.INACTIVO
        )
        datos = _build_cita(_fecha_futura())

        with pytest.raises(ValueError, match="no existe o no está activo"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_cliente_no_existe(self, service):
        service._usuario_repo.get_by_id.return_value = None
        datos = _build_cita(_fecha_futura())

        with pytest.raises(ValueError, match="El cliente con ID 1 no existe"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_barberia_inactiva(self, service):
        service._barberia_repo.get_by_id.return_value = SimpleNamespace(
            estado=EstadoBarberia.INACTIVO
        )
        datos = _build_cita(_fecha_futura())

        with pytest.raises(ValueError, match="no existe o no está activa"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_barbero_no_existe(self, service):
        service._empleado_repo.get_empleado.return_value = None
        datos = _build_cita(_fecha_futura())

        with pytest.raises(ValueError, match="El barbero con ID 2 no existe o no está activo"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_barbero_inactivo(self, service):
        service._empleado_repo.get_empleado.return_value = SimpleNamespace(estado="Inactivo")
        datos = _build_cita(_fecha_futura())

        with pytest.raises(ValueError, match="no existe o no está activo"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_barbero_de_otra_barberia(self, service):
        service._empleado_repo.get_empleado.return_value = SimpleNamespace(
            estado="Activo", id_barberia=999
        )
        datos = _build_cita(_fecha_futura())

        with pytest.raises(ValueError, match="no pertenece a la barbería"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_fecha_en_el_pasado(self, service):
        fecha_pasada = datetime.now(COL_TZ) - timedelta(days=1)
        datos = _build_cita(fecha_pasada)

        with pytest.raises(ValueError, match="No se pueden crear citas en fechas/horas pasadas"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_fecha_en_el_pasado_naive(self, service):
        fecha_pasada = datetime.now() - timedelta(days=1)
        datos = _build_cita(fecha_pasada)

        with pytest.raises(ValueError, match="No se pueden crear citas en fechas/horas pasadas"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_barbero_ocupado_solapamiento(self, service):
        service._servicio_repo.get_servicio_by_id.return_value = _servicio_activo(30)
        fecha = _fecha_futura()
        cita_existente = SimpleNamespace(
            id_cita=99,
            fecha_hora=fecha,
            estado_cita=EstadoCita.PENDIENTE,
        )
        service._cita_repo.get_by_barbero.return_value = [cita_existente]
        service._cita_servicio_repo.get_servicios_by_cita.return_value = []

        datos = _build_cita(fecha)

        with pytest.raises(ValueError, match="El barbero no está disponible en ese horario"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_servicio_no_existe(self, service):
        service._servicio_repo.get_servicio_by_id.return_value = None
        datos = _build_cita(_fecha_futura())

        with pytest.raises(ValueError, match="no existen o no están activos"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_servicio_inactivo(self, service):
        service._servicio_repo.get_servicio_by_id.return_value = SimpleNamespace(
            tiempo_estimado=0, estado_servicio=EstadoServicio.INACTIVO
        )
        datos = _build_cita(_fecha_futura())

        with pytest.raises(ValueError, match="no existen o no están activos"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_servicio_adicional_no_compatible(self, service):
        def _mock_servicio(id_servicio):
            if id_servicio == 1:
                return _servicio_activo(30, TipoServicio.PRINCIPAL)
            return _servicio_activo(15, TipoServicio.ADICIONAL)

        service._servicio_repo.get_servicio_by_id.side_effect = _mock_servicio
        service._servicio_adicional_repo.get_ids_adicionales_permitidos.return_value = []
        datos = _build_cita(_fecha_futura())

        with pytest.raises(ValueError, match="no es compatible"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_servicio_adicional_compatible(self, service):
        def _mock_servicio(id_servicio):
            if id_servicio == 1:
                return _servicio_activo(30, TipoServicio.PRINCIPAL)
            return _servicio_activo(15, TipoServicio.ADICIONAL)

        service._servicio_repo.get_servicio_by_id.side_effect = _mock_servicio
        service._servicio_adicional_repo.get_ids_adicionales_permitidos.return_value = [2]
        cita_orm = Cita(
            id_cita=5,
            fecha_hora=_fecha_futura(),
            estado_cita=EstadoCita.PENDIENTE,
            id_cliente=1,
            id_barbero=2,
            id_barberia=3,
        )
        service._repo.create.return_value = cita_orm

        resultado = service.crear_cita(_build_cita(_fecha_futura()))

        assert resultado.id_cita == 5

    def test_cita_solo_con_servicios_adicionales(self, service):
        """Un cliente puede pedir solo servicios adicionales (sin principal)."""
        service._servicio_repo.get_servicio_by_id.side_effect = lambda _id: _servicio_activo(
            15, TipoServicio.ADICIONAL
        )
        cita_orm = Cita(
            id_cita=6,
            fecha_hora=_fecha_futura(),
            estado_cita=EstadoCita.PENDIENTE,
            id_cliente=1,
            id_barbero=2,
            id_barberia=3,
        )
        service._repo.create.return_value = cita_orm

        resultado = service.crear_cita(_build_cita(_fecha_futura()))

        assert resultado.id_cita == 6

    def test_barbero_no_puede_realizar_todos_los_servicios(self, service):
        service._barbero_servicio_repo.puede_realizar_todos.return_value = False
        datos = _build_cita(_fecha_futura())

        with pytest.raises(ValueError, match="no puede realizar todos los servicios"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_crear_cita_sin_servicios(self, service):
        datos = _build_cita(_fecha_futura())
        datos.ids_servicios = []

        with pytest.raises(ValueError, match="La cita debe incluir al menos un servicio"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_servicios_repetidos(self, service):
        datos = _build_cita(_fecha_futura())
        datos.ids_servicios = [1, 1]

        with pytest.raises(ValueError, match="No se pueden repetir servicios"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_cliente_con_cita_solapada(self, service):
        service._servicio_repo.get_servicio_by_id.return_value = _servicio_activo(30)
        fecha = _fecha_futura()
        cita_existente = SimpleNamespace(
            id_cita=99,
            fecha_hora=fecha,
            estado_cita=EstadoCita.PENDIENTE,
        )
        service._cita_repo.get_by_cliente.return_value = [cita_existente]
        service._cita_servicio_repo.get_servicios_by_cita.return_value = []

        datos = _build_cita(fecha)

        with pytest.raises(ValueError, match="El cliente ya tiene una cita"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_cita_fuera_del_horario_atencion(self, service):
        service._horario_repo.get_horario_para_fecha.return_value = SimpleNamespace(
            hora_apertura=time(10, 0), hora_cierre=time(11, 0)
        )
        fecha = (datetime.now(COL_TZ) + timedelta(days=1)).replace(
            hour=15, minute=0, second=0, microsecond=0
        )
        datos = _build_cita(fecha)

        with pytest.raises(ValueError, match="fuera del horario de atención"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_cita_barberia_cerrada_ese_dia(self, service):
        service._horario_repo.get_horario_para_fecha.return_value = None
        datos = _build_cita(_fecha_futura())

        with pytest.raises(ValueError, match="fuera del horario de atención"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_cita_en_fecha_no_laboral(self, service):
        service._fecha_no_laboral_repo.es_no_laboral.return_value = True
        datos = _build_cita(_fecha_futura())

        with pytest.raises(ValueError, match="no atiende en esta fecha"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_cita_excede_hora_de_cierre(self, service):
        service._horario_repo.get_horario_para_fecha.return_value = SimpleNamespace(
            hora_apertura=time(8, 0), hora_cierre=time(20, 0)
        )
        service._servicio_repo.get_servicio_by_id.return_value = _servicio_activo(40)
        fecha = (datetime.now(COL_TZ) + timedelta(days=1)).replace(
            hour=19, minute=40, second=0, microsecond=0
        )
        datos = _build_cita(fecha)

        with pytest.raises(ValueError, match="fuera del horario de atención"):
            service.crear_cita(datos)

        service._repo.create.assert_not_called()

    def test_cita_dentro_del_horario_con_duracion(self, service):
        service._horario_repo.get_horario_para_fecha.return_value = SimpleNamespace(
            hora_apertura=time(8, 0), hora_cierre=time(20, 0)
        )
        service._servicio_repo.get_servicio_by_id.return_value = _servicio_activo(40)
        fecha = (datetime.now(COL_TZ) + timedelta(days=1)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        cita_orm = Cita(
            id_cita=4,
            fecha_hora=fecha,
            estado_cita=EstadoCita.PENDIENTE,
            id_cliente=1,
            id_barbero=2,
            id_barberia=3,
        )
        service._repo.create.return_value = cita_orm

        resultado = service.crear_cita(_build_cita(fecha))

        assert resultado.id_cita == 4
        service._repo.create.assert_called_once()

    def test_barbero_disponible_con_cita_terminada(self, service):
        """Una cita COMPLETADA/CANCELADA no bloquea el horario."""
        fecha = _fecha_futura()
        cita_terminada = SimpleNamespace(
            id_cita=98,
            fecha_hora=fecha,
            estado_cita=EstadoCita.CANCELADA,
        )
        service._cita_repo.get_by_barbero.return_value = [cita_terminada]

        cita_orm = Cita(
            id_cita=3,
            fecha_hora=fecha,
            estado_cita=EstadoCita.PENDIENTE,
            id_cliente=1,
            id_barbero=2,
            id_barberia=3,
        )
        service._repo.create.return_value = cita_orm

        resultado = service.crear_cita(_build_cita(fecha))

        assert resultado.id_cita == 3
        service._repo.create.assert_called_once()
