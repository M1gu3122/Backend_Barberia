# src/services/horario_barberia_service.py
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.horario_barberia_model import HorarioBarberia
from src.schemas.horario_barberia_schema import (
    DIAS_SEMANA,
    HorarioBarberiaCreate,
    HorarioBarberiaUpdate,
    HorarioBarberiaResponse,
)
from src.repositories.horario_barberia_repository import HorarioBarberiaRepository
from src.repositories.barberia_repository import BarberiaRepository
from src.services.base_service import BaseService


class HorarioBarberiaService(BaseService[HorarioBarberia]):
    def __init__(self, db: Session):
        repo = HorarioBarberiaRepository(db)
        super().__init__(db=db, repository=repo)
        self._horario_repo = repo
        self._barberia_repo = BarberiaRepository(db)

    # ---------------------------------------------------------------
    #  Validaciones comunes
    # ---------------------------------------------------------------
    def _validar_datos(
        self, dia_semana: str, hora_apertura: object, hora_cierre: object
    ) -> None:
        if dia_semana not in DIAS_SEMANA:
            raise ValueError(
                f"Día de la semana inválido: {dia_semana}. Debe ser uno de: {', '.join(DIAS_SEMANA)}"
            )
        if hora_cierre <= hora_apertura:
            raise ValueError("La hora de cierre debe ser posterior a la hora de apertura")

    def _validar_barberia(self, id_barberia: int) -> None:
        if not self._barberia_repo.get_by_id(id_barberia):
            raise ValueError(f"La barbería con ID {id_barberia} no existe")

    # ---------------------------------------------------------------
    #  CREATE
    # ---------------------------------------------------------------
    def crear_horario(self, datos: HorarioBarberiaCreate) -> HorarioBarberiaResponse:
        """Crea un horario para un día de la semana de una barbería."""
        self._validar_barberia(datos.id_barberia)
        self._validar_datos(datos.dia_semana, datos.hora_apertura, datos.hora_cierre)

        if self._horario_repo.get_by_dia(datos.id_barberia, datos.dia_semana):
            raise ValueError(
                f"Ya existe un horario para {datos.dia_semana} en la barbería {datos.id_barberia}"
            )

        horario_orm = self._horario_repo.create(datos)
        return HorarioBarberiaResponse.model_validate(horario_orm)

    # ---------------------------------------------------------------
    #  READ
    # ---------------------------------------------------------------
    def listar_horarios(self) -> List[HorarioBarberiaResponse]:
        """Obtiene todos los horarios."""
        return [
            HorarioBarberiaResponse.model_validate(h)
            for h in self._horario_repo.get_all()
        ]

    def listar_horarios_por_barberia(self, id_barberia: int) -> List[HorarioBarberiaResponse]:
        """Obtiene los horarios de una barbería."""
        return [
            HorarioBarberiaResponse.model_validate(h)
            for h in self._horario_repo.get_by_barberia(id_barberia)
        ]

    def obtener_horario(self, id_horario: int) -> Optional[HorarioBarberiaResponse]:
        """Obtiene un horario por su ID."""
        horario = self._horario_repo.get_by_id(id_horario)
        if not horario:
            return None
        return HorarioBarberiaResponse.model_validate(horario)

    def obtener_horario_por_dia(
        self, id_barberia: int, dia_semana: str
    ) -> Optional[HorarioBarberiaResponse]:
        """Obtiene el horario de un día concreto de una barbería."""
        horario = self._horario_repo.get_by_dia(id_barberia, dia_semana)
        if not horario:
            return None
        return HorarioBarberiaResponse.model_validate(horario)

    def obtener_horario_para_fecha(
        self, id_barberia: int, fecha: object
    ) -> Optional[HorarioBarberiaResponse]:
        """Obtiene el horario vigente para una fecha concreta."""
        horario = self._horario_repo.get_horario_para_fecha(id_barberia, fecha)
        if not horario:
            return None
        return HorarioBarberiaResponse.model_validate(horario)

    # ---------------------------------------------------------------
    #  UPDATE
    # ---------------------------------------------------------------
    def actualizar_horario(
        self, id_horario: int, datos: HorarioBarberiaUpdate
    ) -> Optional[HorarioBarberiaResponse]:
        """Actualiza un horario existente."""
        horario = self._horario_repo.get_by_id(id_horario)
        if not horario:
            return None

        dia_semana = datos.dia_semana if datos.dia_semana is not None else horario.dia_semana
        hora_apertura = (
            datos.hora_apertura if datos.hora_apertura is not None else horario.hora_apertura
        )
        hora_cierre = (
            datos.hora_cierre if datos.hora_cierre is not None else horario.hora_cierre
        )
        self._validar_datos(dia_semana, hora_apertura, hora_cierre)

        horario_actualizado = self._horario_repo.update(id_horario, datos)
        return HorarioBarberiaResponse.model_validate(horario_actualizado)

    # ---------------------------------------------------------------
    #  DELETE
    # ---------------------------------------------------------------
    def eliminar_horario(self, id_horario: int) -> bool:
        """Elimina un horario por ID."""
        return self._horario_repo.delete(id_horario)