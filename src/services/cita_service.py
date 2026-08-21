# src/services/cita_service.py
from typing import List, Optional
from fastapi import HTTPException
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
import os

from src.core.timezone import a_bogota, BOGOTA_TZ


from src.models.cita_servicio_model import CitaServicio
from src.schemas.cita_servicio_schema import CitaServicioCreate
from src.repositories.empleado_repository import EmpleadoRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.models.cita_model import Cita, EstadoCita
from src.models.servicio_model import EstadoServicio, TipoServicio
from src.models.usuario_model import EstadoUsuario
from src.models.barberia_model import EstadoBarberia
from src.models.usuario_model import EstadoUsuario
from src.models.barberia_model import EstadoBarberia
from src.schemas.cita_schema import (
    CitaCreate,
    CitaUpdate,
    CitaResponse,
    CitaDetalleResponse,
)
from src.repositories.cita_repository import CitaRepository
from src.repositories.servicio_repository import ServicioRepository
from src.repositories.cita_servicio_repository import CitaServicioRepository
from src.repositories.barberia_repository import BarberiaRepository
from src.repositories.horario_barberia_repository import HorarioBarberiaRepository
from src.repositories.barbero_servicio_repository import BarberoServicioRepository
from src.repositories.servicio_adicional_repository import ServicioAdicionalRepository
from src.repositories.fecha_no_laboral_repository import FechaNoLaboralRepository
from src.services.base_service import BaseService
from src.messaging.email import send_notification, schedule_notification

# Configuración de buffer de tiempo (minutos) para reservas de cita
# Se suma a la duración total de los servicios para considerar tiempo de preparación/limpieza
BUFFER_MINUTOS = int(os.getenv("CITA_BUFFER_MINUTOS", "5"))


class CitaService(BaseService):
    def __init__(self, db: Session):
        repo = CitaRepository(db)
        super().__init__(db=db, repository=repo)
        self._servicio_repo = ServicioRepository(db)
        self._cita_servicio_repo = CitaServicioRepository(db)
        self._barberia_repo = BarberiaRepository(db)
        self._usuario_repo = UsuarioRepository(db)
        self._empleado_repo = EmpleadoRepository(db)
        self._cita_repo = CitaRepository(db)
        self._horario_repo = HorarioBarberiaRepository(db)
        self._barbero_servicio_repo = BarberoServicioRepository(db)
        self._servicio_adicional_repo = ServicioAdicionalRepository(db)
        self._fecha_no_laboral_repo = FechaNoLaboralRepository(db)

    # Validaciones
    def _validar_cliente(self, id_cliente: int) -> bool:
        """Regla 1: el cliente debe existir y estar activo."""
        cliente = self._usuario_repo.get_by_id(id_cliente)
        if not cliente:
            return False
        return cliente.estado == EstadoUsuario.ACTIVO

    def _validar_barbero(self, id_barbero: int, tipo_empleado: str) -> bool:
        barbero = self._empleado_repo.get_empleado(id_barbero, tipo_empleado)
        if not barbero:
            return False
        return barbero.estado == "Activo"

    def _validar_barbero_en_barberia(self, id_barbero: int, id_barberia: int) -> bool:
        barbero = self._empleado_repo.get_empleado(id_barbero, "Barbero")
        if not barbero:
            return False
        return barbero.id_barberia == id_barberia

    def _validar_barberia(self, id_barberia: int) -> bool:
        """Regla 3: la barbería debe existir y estar activa."""
        barberia = self._barberia_repo.get_by_id(id_barberia)
        if not barberia:
            return False
        return barberia.estado == EstadoBarberia.ACTIVO

    # def _validar_barbero_en_barberia(self, id_barbero: int, id_barberia: int) -> bool:
    #     return True

    def _validar_servicios(self, id_servicios: List[int], id_barberia: int) -> bool:
        """Reglas 7 y 8: todos los servicios deben existir y estar activos."""
        for id_servicio in id_servicios:
            servicio = self._servicio_repo.get_servicio_by_id(id_servicio)
            if not servicio:
                return False
            if servicio.estado_servicio != EstadoServicio.ACTIVO:
                return False
        return True

    def _validar_barbero_servicios(
        self, id_barbero: int, id_servicios: List[int]
    ) -> bool:
        """Regla 9: el barbero debe poder realizar todos los servicios seleccionados."""
        return self._barbero_servicio_repo.puede_realizar_todos(
            id_barbero, id_servicios
        )

    def _validar_compatibilidad_adicionales(self, id_servicios: List[int]) -> bool:
        """Regla 10: si hay servicio principal, los adicionales deben ser
        compatibles con él. Una cita puede contener solo servicios adicionales."""
        principal_id = None
        adicionales: List[int] = []

        for id_servicio in id_servicios:
            servicio = self._servicio_repo.get_servicio_by_id(id_servicio)
            if servicio.tipo_servicio == TipoServicio.PRINCIPAL:
                principal_id = id_servicio
            elif servicio.tipo_servicio == TipoServicio.ADICIONAL:
                adicionales.append(id_servicio)

        # Sin servicio principal: se permite la cita solo con adicionales
        if not principal_id:
            return True

        permitidos = set(
            self._servicio_adicional_repo.get_ids_adicionales_permitidos(principal_id)
        )
        return all(adicional in permitidos for adicional in adicionales)



    def _validar_horario_disponible(
        self, id_barbero: int, fecha_hora: datetime, duracion_minutos: int
    ) -> bool:
        citas_existentes = self._cita_repo.get_by_barbero(id_barbero)

        # Normalizar la fecha de entrada a hora de Bogotá (aware)
        # Si es naive, se interpreta como hora local de Colombia; si es aware, se convierte
        from src.core.timezone import a_bogota

        fecha_hora = a_bogota(fecha_hora)
        # Para comparación con la base de datos (naive), quitar el tzinfo
        fecha_hora_naive = fecha_hora.replace(tzinfo=None)

        fin_cita = fecha_hora_naive + timedelta(minutes=duracion_minutos)

        for cita in citas_existentes:
            # Solo verificar solapamiento si la cita está pendiente o confirmada
            if cita.estado_cita in [EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]:

                duracion_cita_existente = self._calcular_tiempo_servicios(cita.id_cita)

                if duracion_cita_existente == 0:
                    duracion_cita_existente = 60

                # Asegurarse que la fecha de la cita existente sea naive para comparación
                cita_fecha = cita.fecha_hora
                if cita_fecha.tzinfo is not None:
                    cita_fecha = cita_fecha.replace(tzinfo=None)

                cita_fin = cita_fecha + timedelta(minutes=duracion_cita_existente)

                # Verificar solapamiento: la nueva cita comienza antes de que termine la existente
                # Y la existente termina después de que empieza la nueva
                if cita_fecha < fin_cita and cita_fin > fecha_hora_naive:
                    return False

        return True

    def _calcular_tiempo_servicios(self, id_cita: int) -> int:
        tiempo_total = 0
        cita_servicios = self._cita_servicio_repo.get_servicios_by_cita(id_cita)

        for cita_servicio in cita_servicios:
            servicio = self._servicio_repo.get_servicio_by_id(cita_servicio.id_servicio)
            if servicio:
                tiempo_total += servicio.tiempo_estimado

        return tiempo_total

    def _validar_servicios_no_repetidos(self, id_servicios: List[int]) -> bool:
        """Regla 15: no se permiten servicios repetidos en una misma cita."""
        return len(set(id_servicios)) == len(id_servicios)

    def _validar_cliente_disponible(
        self, id_cliente: int, fecha_hora: datetime, duracion_min: int
    ) -> bool:
        """Regla 13: el cliente no debe tener otra cita solapada."""
        citas_existentes = self._cita_repo.get_by_cliente(id_cliente)

        # Normalizar la zona horaria según las citas existentes (naive vs aware)
        tz_info = None
        if citas_existentes:
            tz_info = citas_existentes[0].fecha_hora.tzinfo

        if tz_info is not None and fecha_hora.tzinfo is None:
            fecha_hora = fecha_hora.replace(tzinfo=tz_info)
        elif tz_info is None and fecha_hora.tzinfo is not None:
            fecha_hora = fecha_hora.replace(tzinfo=None)

        fin_cita = fecha_hora + timedelta(minutes=duracion_min)

        for cita in citas_existentes:
            if cita.estado_cita in [EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]:
                duracion_cita_existente = self._calcular_tiempo_servicios(cita.id_cita)
                if duracion_cita_existente == 0:
                    duracion_cita_existente = 60
                cita_fin = cita.fecha_hora + timedelta(minutes=duracion_cita_existente)
                if cita.fecha_hora < fin_cita and cita_fin > fecha_hora:
                    return False

        return True

    def _calcular_tiempo_total(self, ids_servicios: List[int]) -> int:
        """Suma el tiempo estimado de los servicios seleccionados más el buffer."""
        tiempo_total = BUFFER_MINUTOS
        for id_servicio in ids_servicios:
            servicio = self._servicio_repo.get_servicio_by_id(id_servicio)
            if servicio:
                tiempo_total += servicio.tiempo_estimado
        return tiempo_total

    def _validar_horario_atencion(
        self, id_barberia: int, fecha_hora: datetime, duracion_min: int
    ) -> bool:
        """Reglas 6 y 14: la cita debe caer dentro del horario de atención
        y no debe exceder la hora de cierre."""
        horario = self._horario_repo.get_horario_para_fecha(id_barberia, fecha_hora)
        if not horario:
            return False

        hora_inicio = fecha_hora.time()
        if hora_inicio < horario.hora_apertura or hora_inicio >= horario.hora_cierre:
            return False

        fin_cita = fecha_hora + timedelta(minutes=duracion_min)
        if fin_cita.time() > horario.hora_cierre:
            return False

        return True

    # CREATE - Reglas de negocio actualizadas
    
    async def crear_cita(self, datos: CitaCreate) -> CitaResponse:
        COL_TZ = ZoneInfo("America/Bogota")
        """
        Reglas de negocio:
        1  El cliente debe estar activo.
        2. El barbero debe estar activo.
        3. La fecha/hora de la cita no puede ser en el pasado.
        4. El barbero no debe tener otra cita en ese horario.
        5. Verificar disponibilidad considerando tiempo total de servicios.
        6. Validar que los servicios sean válidos.
        """

        # Regla 1: verificar existencia y estado activo del cliente
        if not self._validar_cliente(datos.id_cliente):
            raise ValueError(
                f"El cliente con ID {datos.id_cliente} no existe o no está activo"
            )

        # Regla 2: verificar existencia del barbero
        if not self._validar_barbero(datos.id_barbero, "Barbero"):
            raise ValueError(
                f"El barbero con ID {datos.id_barbero} no existe o no está activo"
            )

        # Regla 3: la barbería debe existir y estar activa
        if not self._validar_barberia(datos.id_barberia):
            raise ValueError(
                f"La barbería con ID {datos.id_barberia} no existe o no está activa"
            )

        # Regla 4: el barbero debe pertenecer a la barbería de la cita
        if not self._validar_barbero_en_barberia(datos.id_barbero, datos.id_barberia):
            raise ValueError(
                f"El barbero con ID {datos.id_barbero} no pertenece a la barbería {datos.id_barberia}"
            )

        # Regla 5: fecha/hora no debe ser en el pasado
        fecha_hora = datos.fecha_hora
        if fecha_hora.tzinfo is None:
            fecha_hora = fecha_hora.replace(tzinfo=COL_TZ)
        if fecha_hora < datetime.now(COL_TZ):
            raise ValueError("No se pueden crear citas en fechas/horas pasadas")

        # Validar que la cita incluya al menos un servicio
        if not datos.ids_servicios:
            raise ValueError("La cita debe incluir al menos un servicio")

        # Regla 15: no se permiten servicios repetidos
        if not self._validar_servicios_no_repetidos(datos.ids_servicios):
            raise ValueError("No se pueden repetir servicios en una misma cita")

        # Reglas 7 y 8: los servicios deben existir y estar activos
        if not self._validar_servicios(datos.ids_servicios, datos.id_barberia):
            raise ValueError("Uno o más servicios no existen o no están activos")

        # Regla 9: el barbero debe poder realizar todos los servicios
        if not self._validar_barbero_servicios(datos.id_barbero, datos.ids_servicios):
            raise ValueError(
                "El barbero no puede realizar todos los servicios seleccionados"
            )

        # Regla 10: los servicios adicionales deben ser compatibles con el principal
        if not self._validar_compatibilidad_adicionales(datos.ids_servicios):
            raise ValueError(
                "El servicio adicional no es compatible con el servicio principal"
            )

        # Reglas 12, 6 y 14: la duración total debe caber dentro del horario
        # de atención y sin cruzar la hora de cierre
        duracion_total = self._calcular_tiempo_total(datos.ids_servicios)

        # La barbería no atiende en fechas no laborales (festivos, cierres)
        if self._fecha_no_laboral_repo.es_no_laboral(
            datos.id_barberia, fecha_hora.date()
        ):
            raise ValueError("La barbería no atiende en esta fecha")

        if not self._validar_horario_atencion(
            datos.id_barberia, fecha_hora, duracion_total
        ):
            raise ValueError(
                "La cita está fuera del horario de atención o excede la hora de cierre"
            )

        # Regla 11: el barbero no debe tener otra cita solapada (duración real)
        if not self._validar_horario_disponible(
            datos.id_barbero, fecha_hora, duracion_total
        ):
            raise ValueError("El barbero no está disponible en ese horario")

        # Regla 13: el cliente no debe tener otra cita solapada
        if not self._validar_cliente_disponible(
            datos.id_cliente, fecha_hora, duracion_total
        ):
            raise ValueError("El cliente ya tiene una cita en ese horario")

        # Regla nueva: no permitir crear cita si ya existe otra con el mismo barbero
        # y mismo horario exacto. Se permite reasignar a distinto barbero.
        # Se pasa la duración total para validar solapamiento real de intervalos
        if self._repo.existe_cita_solapada(
            datos.id_barbero, datos.fecha_hora, 0, duracion_total
        ):
            raise HTTPException(
                status_code=400,
                detail="Ya existe una cita agendada para este barbero en ese horario",
            )

        # Persistir la cita
        cita_orm = self._repo.create(datos)

        # Cargar la relación cliente para que CitaResponse pueda acceder a nombres, apellidos, correo
        self._db.refresh(cita_orm, attribute_names=["cliente"])

        # Persistir los servicios asociados a la cita
        for id_servicio in datos.ids_servicios:
            self._cita_servicio_repo.create(
                CitaServicioCreate(
                    id_cita=cita_orm.id_cita,
                    id_servicio=id_servicio,
                )
            )

        # Confirmar la transacción: sin COMMIT la cita se revierte al
        # cerrar la sesión (get_db no hace commit) y nunca se guarda en BD.
        self._db.commit()

        # Validar y obtener datos del cliente para notificaciones
        if not cita_orm.cliente or not cita_orm.cliente.correo:
            return CitaResponse.model_validate(cita_orm)

        cliente = cita_orm.cliente

        # Notificación inmediata de confirmación
        # await send_notification(
        #     subject="Confirmación de cita",
        #     recipients=[cliente.correo],
        #     body=f"Hola {cliente.nombres} {cliente.apellidos}, tu cita ha sido agendada para {cita_orm.fecha_hora.strftime('%d/%m/%Y %H:%M')}.",
        #     subtype="plain",
        # )

        # Programar recordatorio 3 minutos antes
        fecha_recordatorio = cita_orm.fecha_hora - timedelta(minutes=3)

        # Solo programar si la fecha del recordatorio es futura
        if fecha_recordatorio > datetime.now():
            schedule_notification(
                subject="⏰ Recordatorio de cita",
                recipients=[cliente.correo],
                body=f"Hola {cliente.nombres} {cliente.apellidos}, recuerda tu cita agendada para el {cita_orm.fecha_hora.strftime('%d/%m/%Y %H:%M')}.",
                run_date=fecha_recordatorio,
                job_id=str(cita_orm.id_cita),  # APScheduler requiere string para id
                subtype="plain",
            )

        return CitaResponse.model_validate(cita_orm)

    # Métodos CRUD
    # src/services/cita_service.py

    # ...

    def listar_citas(self) -> List[CitaResponse]:
        citas = self._repo.get_all()
        return [CitaResponse.model_validate(c) for c in citas]

    def listar_citas_con_detalle(self) -> List[CitaDetalleResponse]:
        """Obtiene las citas con los servicios agrupados y datos del cliente y barbero."""
        return [
            CitaDetalleResponse.model_validate(d)
            for d in self._repo.get_citas_con_detalle()
        ]

    # ...

    def obtener_cita_por_id(self, id_cita: int) -> Optional[CitaResponse]:
        cita = self._repo.get_by_id(id_cita)
        if not cita:
            return None
        return CitaResponse.model_validate(cita)

    def listar_citas_por_cliente(self, id_cliente: int) -> List[CitaResponse]:
        return [
            CitaResponse.model_validate(c)
            for c in self._repo.get_by_cliente(id_cliente)
        ]

    def listar_citas_por_cliente_con_detalle(
        self, id_cliente: int
    ) -> List[CitaDetalleResponse]:
        """Citas de un cliente con servicios agrupados y datos del barbero."""
        return [
            CitaDetalleResponse.model_validate(d)
            for d in self._repo.get_citas_con_detalle(id_cliente)
        ]

    def listar_citas_por_barbero(self, id_barbero: int) -> List[CitaResponse]:
        return [
            CitaResponse.model_validate(c)
            for c in self._repo.get_by_barbero(id_barbero)
        ]

    def listar_citas_por_fecha(
        self, fecha_inicio: datetime, fecha_fin: datetime
    ) -> List[CitaResponse]:
        return [
            CitaResponse.model_validate(c)
            for c in self._repo.get_by_fecha(fecha_inicio, fecha_fin)
        ]

    def actualizar_cita(
        self, id_cita: int, datos: CitaUpdate
    ) -> Optional[CitaResponse]:
        cita = self._repo.get_by_id(id_cita)
        if not cita:
            return None

        # ✅ Validación: solo bloquear si se intenta cambiar el estado a un valor no permitido
        # Si solo se actualizan campos operativos (barbero, fecha, hora), se permite
        # Validar transición de estado únicamente si realmente cambia el estado
        if (
            datos.estado_cita is not None
            and datos.estado_cita != cita.estado_cita
            and not cita.puede_transitar_a(datos.estado_cita)
        ):
            raise HTTPException(
                status_code=400,
                detail=f"No se puede cambiar la cita de "
                f"'{cita.estado_cita.value}' a '{datos.estado_cita.value}'",
            )

        # Validación: no se puede actualizar una cita completada
        if cita.estado_cita == EstadoCita.COMPLETADA:
            raise HTTPException(
                status_code=400, detail="No se puede actualizar una cita completada"
            )

        # Validación: no se puede actualizar una cita cancelada
        if cita.estado_cita == EstadoCita.CANCELADA:
            raise HTTPException(
                status_code=400, detail="No se puede actualizar una cita cancelada"
            )

        # Validación: no se puede actualizar una cita en En Atención
        if cita.estado_cita == EstadoCita.EN_ATENCION:
            raise HTTPException(
                status_code=400,
                detail="No se puede actualizar una cita en estado 'En Atención'",
            )

        # Validación: la fecha no puede ser del pasado si se está modificando
        if datos.fecha_hora and cita.fecha_hora != datos.fecha_hora:
            fecha_hora = datos.fecha_hora
            if fecha_hora.tzinfo is None:
                fecha_hora = fecha_hora.replace(tzinfo=ZoneInfo("America/Bogota"))
            if fecha_hora < datetime.now(ZoneInfo("America/Bogota")):
                raise HTTPException(
                    status_code=400,
                    detail="No se pueden actualizar citas a fechas pasadas",
                )

        # ✅ NUEVO: Detectar qué campos realmente van a cambiar (para optimizar validaciones)
        # Un campo se considera "cambiando" si el valor nuevo es diferente al actual
        # y no es None (para campos opcionales)
        _cambiando_fecha = datos.fecha_hora is not None and cita.fecha_hora != datos.fecha_hora
        _cambiando_barbero = datos.id_barbero is not None and cita.id_barbero != datos.id_barbero
        # Extraer IDs de servicios actuales de la cita (vía relación CitaServicio)
        ids_servicios_actuales = [s.id_servicio for s in cita.servicios]
        _cambiando_servicios = datos.ids_servicios is not None and ids_servicios_actuales != datos.ids_servicios

        # ✅ Si vienen servicios, reemplazarlos (borrar y crear)
        if datos.ids_servicios is not None:
            if not datos.ids_servicios:
                raise ValueError("La cita debe incluir al menos un servicio")

            # Regla 15: no se permiten servicios repetidos
            if not self._validar_servicios_no_repetidos(datos.ids_servicios):
                raise ValueError("No se pueden repetir servicios en una misma cita")

            # Reglas 7 y 8: servicios deben existir y estar activos
            if not self._validar_servicios(datos.ids_servicios, cita.id_barberia):
                raise ValueError("Uno o más servicios no existen o no están activos")

            # Regla 9: el barbero debe poder realizar todos los servicios
            if not self._validar_barbero_servicios(
                cita.id_barbero, datos.ids_servicios
            ):
                raise ValueError(
                    "El barbero no puede realizar todos los servicios seleccionados"
                )

            # Regla 10: compatibilidad de adicionales con el principal
            if not self._validar_compatibilidad_adicionales(datos.ids_servicios):
                raise ValueError(
                    "El servicio adicional no es compatible con el servicio principal"
                )

            # Reemplazar servicios de la cita
            self._cita_servicio_repo.delete_by_cita(id_cita)
            for sid in datos.ids_servicios:
                self._cita_servicio_repo.create(
                    CitaServicioCreate(id_cita=id_cita, id_servicio=sid)
                )

            # ✅ NUEVO: Si cambian servicios, recalcular duración total con buffer
            # y validar disponibilidad con el nuevo intervalo
            if _cambiando_servicios:
                duracion_total = self._calcular_tiempo_total(datos.ids_servicios)
                # Aquí continuaríamos con validación de disponibilidad abajo

        # ✅ NUEVA LÓGICA DE REPROGRAMACIÓN COMPLETA
        # Solo saltarse la validación de solapamiento si SOLO se cambia el estado
        # En cualquier otro caso (fecha, hora, barbero, servicios), validar completamente
        # excluyendo la propia cita actual (id_cita).
        _solo_cambio_estado = (
            datos.estado_cita is not None
            and (datos.fecha_hora is None or datos.fecha_hora == cita.fecha_hora)
            and (datos.id_barbero is None or datos.id_barbero == cita.id_barbero)
            and not _cambiando_servicios
        )

        if not _solo_cambio_estado:
            # Validación de disponibilidad cuando se modifican campos operativos

            # Determinar el barbero a validar (nuevo o el actual)
            barbero_a_validar = (
                datos.id_barbero
                if datos.id_barbero is not None
                else cita.id_barbero
            )

            # Determinar la fecha/hora a validar
            fecha_a_validar = (
                datos.fecha_hora
                if datos.fecha_hora is not None
                else cita.fecha_hora
            )

            # Si se cambiaron servicios, ya recalcó duracion_total arriba.
            # Si no, calcularla ahora con buffer usando IDs de la relación actual.
            if not _cambiando_servicios:
                duracion_total = self._calcular_tiempo_total(
                    [s.id_servicio for s in cita.servicios]
                )

            # Ejecutar validación de solapamiento, excluyendo la propia cita
            if self._repo.existe_cita_solapada(
                barbero_a_validar, fecha_a_validar, id_cita
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Ya existe una cita agendada para este barbero en ese horario",
                )

        # Si solo cambia el estado (y ningún otro campo), no se realizaron validaciones
        # de disponibilidad anteriormente en este bloque, así que pularemos el update
        # si hay cambios de estado que requieren validación adicional más abajo.
        # El repository.update manejará el guardado efectivo.

        cita_actualizada = self._repo.update(id_cita, datos)
        return CitaResponse.model_validate(cita_actualizada)

    def confirmar_cita(self, id_cita: int) -> Optional[CitaResponse]:
        cita = self._repo.get_by_id(id_cita)
        if not cita:
            return None
        if not cita.puede_transitar_a(EstadoCita.CONFIRMADA):  # type: ignore[arg-type]
            raise ValueError(
                f"No se puede confirmar una cita en estado '{cita.estado_cita.value}'"
            )
        cita.estado_cita = EstadoCita.CONFIRMADA
        self._db.commit()
        return CitaResponse.model_validate(cita)

    def cancelar_cita(self, id_cita: int) -> Optional[CitaResponse]:
        cita = self._repo.get_by_id(id_cita)

        if not cita:
            return None

        if not cita.puede_transitar_a(EstadoCita.CANCELADA):
            raise HTTPException(
                status_code=400,
                detail=f"No se puede cancelar una cita en estado '{cita.estado_cita.value}'",
            )

        cita.estado_cita = EstadoCita.CANCELADA
        self._db.commit()

        return CitaResponse.model_validate(cita)

    def completar_cita(self, id_cita: int) -> Optional[CitaResponse]:
        cita = self._repo.get_by_id(id_cita)
        if not cita:
            return None
        if not cita.puede_transitar_a(EstadoCita.COMPLETADA):  # type: ignore[arg-type]
            raise ValueError(
                f"Solo se pueden completar citas en estado '{cita.estado_cita.value}' "
                f"o EN_ATENCIÓN, no desde '{cita.estado_cita.value}'"
            )
        cita.estado_cita = EstadoCita.COMPLETADA
        self._db.commit()
        return CitaResponse.model_validate(cita)

    def eliminar_cita(self, id_cita: int) -> bool:
        return self._repo.delete(id_cita)

    # src/services/cita_service.py
    def asignar_servicio_a_cita(self, datos: CitaServicioCreate) -> CitaServicio:
        """Asigna un servicio a una cita"""
        servicio_orm = self._cita_servicio_repo.create(datos)
        return servicio_orm

    def auto_completar_citas_vencidas(self) -> int:
        """
        Scheduler que se ejecuta cada 5 minutos y gestiona los estados de las citas:
        
        Reglas:
        1. Si una cita PENDIENTE está a menos de 5 minutos de su inicio y sigue PENDIENTE,
           se cancela automáticamente (no se convierte a COMPLETADA).
        2. Si una cita EN_ATENCIÓN tiene su tiempo estimado cumplido, pasa a COMPLETADA.
        3. Nunca convierte directamente PENDIENTE a COMPLETADA.
        4. No modifica citas CANCELADA ni COMPLETADA automáticamente.
        5. El scheduler debe ejecutarse cada 5 minutos.
        
        Retorna la cantidad de citas actualizadas.
        """
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo
        from sqlalchemy import or_

        COL_TZ = ZoneInfo("America/Bogota")
        ahora = datetime.now(COL_TZ)

        # Estados que no deben modificarse automáticamente
        estados_inmutables = [EstadoCita.CANCELADA, EstadoCita.COMPLETADA]

        # Obtener citas que no son estados finales
        citas_a_procesar = (
            self._db.query(Cita)
            .filter(Cita.estado_cita.notin_(estados_inmutables))
            .all()
        )

        actualizadas = 0

        for cita in citas_a_procesar:
            # Normalizar zona horaria de la cita
            fecha_hora_cita = cita.fecha_hora
            if fecha_hora_cita.tzinfo is None:
                fecha_hora_cita = fecha_hora_cita.replace(tzinfo=COL_TZ)

            duracion_total = self._calcular_tiempo_servicios(cita.id_cita)
            if duracion_total == 0:
                duracion_total = 30  # fallback

            fin_estimado = fecha_hora_cita + timedelta(minutes=duracion_total)

            if cita.estado_cita == EstadoCita.PENDIENTE:
                # Regla 1 & 6: Si PENDIENTE y faltan 5 minutos o menos para su inicio,
                # cancelar automáticamente (NUNCA convertir a COMPLETADA directamente)
                tiempo_hasta_inicio = (fecha_hora_cita - ahora).total_seconds() / 60
                if 0 <= tiempo_hasta_inicio <= 5:
                    # Cita próxima a iniciar y aún PENDIENTE -> auto-cancelar
                    cita.estado_cita = EstadoCita.CANCELADA
                    actualizadas += 1
                # Si ya pasó el tiempo o faltan más de 5 minutos, dejarla como PENDIENTE
                # (no hacer nada, respetar la regla de no pasar PENDIENTE a COMPLETADA)

            elif cita.estado_cita == EstadoCita.EN_ATENCIÓN:
                # Regla 4: Si EN_ATENCIÓN y se cumplió el tiempo estimado, completar
                if ahora >= fin_estimado:
                    cita.estado_cita = EstadoCita.COMPLETADA
                    actualizadas += 1
                # Si no se cumplió el tiempo, dejarla EN_ATENCIÓN

            # Regla 2 & 3: Para CONFIRMADA y otros estados, no aplicar cambios automáticos
            # que violen la regla de no pasar PENDIENTE a COMPLETADA

        if actualizadas > 0:
            self._db.commit()

        return actualizadas
