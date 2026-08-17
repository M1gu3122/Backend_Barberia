# src/services/fecha_no_laboral_service.py
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.fecha_no_laboral_model import FechaNoLaboral
from src.schemas.fecha_no_laboral_schema import (
    FechaNoLaboralCreate,
    FechaNoLaboralUpdate,
    FechaNoLaboralResponse,
)
from src.repositories.fecha_no_laboral_repository import FechaNoLaboralRepository
from src.repositories.barberia_repository import BarberiaRepository
from src.services.base_service import BaseService


class FechaNoLaboralService(BaseService[FechaNoLaboral]):
    def __init__(self, db: Session):
        repo = FechaNoLaboralRepository(db)
        super().__init__(db=db, repository=repo)
        self._fecha_no_laboral_repo = repo
        self._barberia_repo = BarberiaRepository(db)

    def _validar_barberia(self, id_barberia: int) -> None:
        if not self._barberia_repo.get_by_id(id_barberia):
            raise ValueError(f"La barbería con ID {id_barberia} no existe")

    # ---------------------------------------------------------------
    #  CREATE
    # ---------------------------------------------------------------
    def crear_fecha_no_laboral(
        self, datos: FechaNoLaboralCreate
    ) -> FechaNoLaboralResponse:
        """Registra una fecha en la que la barbería no atiende."""
        self._validar_barberia(datos.id_barberia)

        registro = self._fecha_no_laboral_repo.es_no_laboral(datos.id_barberia, datos.fecha)
        if registro:
            raise ValueError(
                f"La barbería {datos.id_barberia} ya está cerrada el {datos.fecha}"
            )

        fecha_orm = self._fecha_no_laboral_repo.create(datos)
        return FechaNoLaboralResponse.model_validate(fecha_orm)

    # ---------------------------------------------------------------
    #  READ
    # ---------------------------------------------------------------
    def listar_fechas_no_laborales(self) -> List[FechaNoLaboralResponse]:
        """Obtiene todas las fechas no laborales."""
        return [
            FechaNoLaboralResponse.model_validate(f)
            for f in self._fecha_no_laboral_repo.get_all()
        ]

    def listar_por_barberia(self, id_barberia: int) -> List[FechaNoLaboralResponse]:
        """Obtiene las fechas no laborales de una barbería."""
        return [
            FechaNoLaboralResponse.model_validate(f)
            for f in self._fecha_no_laboral_repo.get_by_barberia(id_barberia)
        ]

    def obtener_fecha_no_laboral(
        self, id_fecha_no_laboral: int
    ) -> Optional[FechaNoLaboralResponse]:
        """Obtiene una fecha no laboral por su ID."""
        registro = self._fecha_no_laboral_repo.get_by_id(id_fecha_no_laboral)
        if not registro:
            return None
        return FechaNoLaboralResponse.model_validate(registro)

    # ---------------------------------------------------------------
    #  UPDATE
    # ---------------------------------------------------------------
    def actualizar_fecha_no_laboral(
        self, id_fecha_no_laboral: int, datos: FechaNoLaboralUpdate
    ) -> Optional[FechaNoLaboralResponse]:
        """Actualiza una fecha no laboral existente."""
        registro = self._fecha_no_laboral_repo.get_by_id(id_fecha_no_laboral)
        if not registro:
            return None
        fecha_actualizada = self._fecha_no_laboral_repo.update(id_fecha_no_laboral, datos)
        return FechaNoLaboralResponse.model_validate(fecha_actualizada)

    # ---------------------------------------------------------------
    #  DELETE
    # ---------------------------------------------------------------
    def eliminar_fecha_no_laboral(self, id_fecha_no_laboral: int) -> bool:
        """Elimina una fecha no laboral por ID."""
        return self._fecha_no_laboral_repo.delete(id_fecha_no_laboral)