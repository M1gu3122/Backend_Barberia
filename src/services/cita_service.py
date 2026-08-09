# src/services/cita_service.py
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.models.cita_servicio_model import CitaServicio
from src.schemas.cita_servicio_schema import CitaServicioCreate
from src.repositories.empleado_repository import EmpleadoRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.models.cita_model import Cita, EstadoCita
from src.schemas.cita_schema import CitaCreate, CitaUpdate, CitaResponse
from src.repositories.cita_repository import CitaRepository
from src.repositories.servicio_repository import ServicioRepository
from src.repositories.cita_servicio_repository import CitaServicioRepository
from src.repositories.barberia_repository import BarberiaRepository
from src.services.base_service import BaseService


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

    # Validaciones
    def _validar_cliente(self, id_cliente: int) -> bool:
        cliente = self._usuario_repo.get_by_id(id_cliente)
        return cliente is not None

    def _validar_barbero(self, id_barbero: int) -> bool:
        barbero = self._empleado_repo.get_by_id(id_barbero)
        if not barbero:
            return False
        return barbero.estado == "Activo"

    def _validar_barberia(self, id_barberia: int) -> bool:
        barberia = self._barberia_repo.get_by_id(id_barberia)
        return barberia is not None

    def _validar_barbero_en_barberia(self, id_barbero: int, id_barberia: int) -> bool:
        return True

    def _validar_servicios(self, id_servicios: List[int], id_barberia: int) -> bool:
        for id_servicio in id_servicios:
            servicio = self._servicio_repo.get_servicio_by_id(id_servicio)
            if not servicio:
                return False
        return True

    # def _validar_horario_disponible(self, id_barbero: int, fecha_hora: datetime, duracion_minutos: int) -> bool:
    #     fin_cita = fecha_hora + timedelta(minutes=duracion_minutos)

    #     # Obtener todas las citas pendientes o confirmadas para ese barbero
    #     citas_existentes = self._cita_repo.get_by_barbero(id_barbero)

    #     for cita in citas_existentes:
    #         if cita.estado_cita in [EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]:
    #             # Verificar solapamiento
    #             cita_fin = cita.fecha_hora + timedelta(minutes=self._calcular_tiempo_servicios(cita.id_cita))
    #             # Si la nueva cita comienza antes de que termine una existente, hay solapamiento
    #             if (cita.fecha_hora < fin_cita and cita_fin > fecha_hora):
    #                 return False

    #     return True

    def _validar_horario_disponible(
        self, id_barbero: int, fecha_hora: datetime, duracion_minutos: int
    ) -> bool:

        fin_cita = fecha_hora + timedelta(minutes=duracion_minutos)

        citas_existentes = self._cita_repo.get_by_barbero(id_barbero)

        for cita in citas_existentes:

            if cita.estado_cita in [EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]:

                duracion_cita_existente = self._calcular_tiempo_servicios(cita.id_cita)

            # Temporalmente 60 minutos mientras no haya servicios
            if duracion_cita_existente == 0:
                duracion_cita_existente = 60

            cita_fin = cita.fecha_hora + timedelta(minutes=duracion_cita_existente)

            if cita.fecha_hora < fin_cita and cita_fin > fecha_hora:
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

    def _validar_disponibilidad_barbero(self, datos: CitaCreate) -> bool:
        return self._validar_horario_disponible(datos.id_barbero, datos.fecha_hora, 60)

    # CREATE - Reglas de negocio actualizadas
    def crear_cita(self, datos: CitaCreate) -> CitaResponse:
        """
        Reglas de negocio:
        1. El cliente, el barbero y la barbería deben existir.
        2. El barbero debe estar activo.
        3. La fecha/hora de la cita no puede ser en el pasado.
        4. El barbero no debe tener otra cita en ese horario.
        5. Verificar disponibilidad considerando tiempo total de servicios.
        6. Validar que los servicios sean válidos.
        """

        # Regla 1: verificar existencia del cliente
        if not self._validar_cliente(datos.id_cliente):
            raise ValueError(f"El cliente con ID {datos.id_cliente} no existe")

        # Regla 2: verificar existencia del barbero
        if not self._validar_barbero(datos.id_barbero):
            raise ValueError(
                f"El barbero con ID {datos.id_barbero} no existe o no está activo"
            )

        # Regla 3: verificar existencia de la barbería
        if not self._validar_barberia(datos.id_barberia):
            raise ValueError(f"La barbería con ID {datos.id_barberia} no existe")

        # Regla 4: Verificar relación barbero-barbería
        if not self._validar_barbero_en_barberia(datos.id_barbero, datos.id_barberia):
            raise ValueError(f"El barbero no pertenece a la barbería especificada")

        # Regla 5: fecha/hora no debe ser en el pasado
        if datos.fecha_hora < datetime.now():
            raise ValueError("No se pueden crear citas en fechas/horas pasadas")

        # Regla 6: verificar disponibilidad del barbero
        if not self._validar_disponibilidad_barbero(datos):
            raise ValueError("El barbero no está disponible en ese horario")

        # Persistir la cita
        cita_orm = self._repo.create(datos)
        return CitaResponse.model_validate(cita_orm)

    # Métodos CRUD
# src/services/cita_service.py

# ...

    def listar_citas(self) -> List[CitaResponse]:
        citas = self._repo.get_all()
        return [CitaResponse.model_validate(c) for c in citas]

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

        cita_actualizada = self._repo.update(id_cita, datos)
        return CitaResponse.model_validate(cita_actualizada)

    def confirmar_cita(self, id_cita: int) -> Optional[CitaResponse]:
        cita = self._repo.get_by_id(id_cita)
        if not cita:
            return None
        cita.estado_cita = EstadoCita.CONFIRMADA
        self._db.commit()
        return CitaResponse.model_validate(cita)

    def cancelar_cita(self, id_cita: int) -> Optional[CitaResponse]:
        cita = self._repo.get_by_id(id_cita)
        if not cita:
            return None
        cita.estado_cita = EstadoCita.CANCELADA
        self._db.commit()
        return CitaResponse.model_validate(cita)

    def completar_cita(self, id_cita: int) -> Optional[CitaResponse]:
        cita = self._repo.get_by_id(id_cita)
        if not cita:
            return None
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

