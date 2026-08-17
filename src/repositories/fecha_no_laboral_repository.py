# src/repositories/fecha_no_laboral_repository.py
from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.fecha_no_laboral_model import FechaNoLaboral
from src.schemas.fecha_no_laboral_schema import FechaNoLaboralCreate
from src.repositories.base_repository import Repository


class FechaNoLaboralRepository(Repository[FechaNoLaboral]):
    def __init__(self, db: Session):
        super().__init__(FechaNoLaboral, db)

    def create(self, data: FechaNoLaboralCreate) -> FechaNoLaboral:
        """Crea una nueva fecha no laboral."""
        registro = FechaNoLaboral(**data.model_dump())
        self._session.add(registro)
        self._session.commit()
        self._session.refresh(registro)
        return registro

    def get_all(self) -> List[FechaNoLaboral]:
        """Obtiene todas las fechas no laborales."""
        return self._session.query(FechaNoLaboral).all()

    def get_by_id(self, id_: int) -> Optional[FechaNoLaboral]:
        """Obtiene una fecha no laboral por su ID."""
        return self._session.get(FechaNoLaboral, id_)

    def update(self, id_: int, data: object) -> Optional[FechaNoLaboral]:
        """Actualiza una fecha no laboral existente."""
        registro = self._session.get(FechaNoLaboral, id_)
        if not registro:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(registro, key, value)
        self._session.commit()
        self._session.refresh(registro)
        return registro

    def delete(self, id_: int) -> bool:
        """Elimina una fecha no laboral por ID. Devuelve True si se eliminó."""
        registro = self._session.get(FechaNoLaboral, id_)
        if not registro:
            return False
        self._session.delete(registro)
        self._session.commit()
        return True

    def get_by_barberia(self, id_barberia: int) -> List[FechaNoLaboral]:
        """Obtiene las fechas no laborales de una barbería."""
        return (
            self._session.query(FechaNoLaboral)
            .filter(FechaNoLaboral.id_barberia == id_barberia)
            .order_by(FechaNoLaboral.fecha)
            .all()
        )

    def es_no_laboral(self, id_barberia: int, fecha: date) -> bool:
        """Regla: indica si una barbería NO atiende una fecha concreta."""
        return (
            self._session.query(FechaNoLaboral)
            .filter(
                FechaNoLaboral.id_barberia == id_barberia,
                FechaNoLaboral.fecha == fecha,
            )
            .first()
            is not None
        )