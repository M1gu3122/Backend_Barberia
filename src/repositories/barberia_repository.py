# src/repositories/barberia_repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.models.barberia_model import Barberia
from src.schemas.barberia_schema import BarberiaCreate, BarberiaUpdate
from src.repositories.base_repository import Repository


class BarberiaRepository(Repository[Barberia]):
    def __init__(self, db: Session):
        super().__init__(Barberia, db)

    # -------------------------------------------------------------
    # CRUD BÁSICO
    # -------------------------------------------------------------

    def create(self, data: BarberiaCreate) -> Barberia:
        """Crea una nueva barbería."""
        barberia = Barberia(**data.model_dump())
        self._session.add(barberia)
        self._session.commit()
        self._session.refresh(barberia)
        return barberia

    def get_all(self) -> List[Barberia]:
        """Obtiene todas las barberías."""
        return self._session.query(Barberia).all()

    def get_by_id(self, id_: int) -> Optional[Barberia]:
        """Obtiene una barbería por su ID."""
        return self._session.get(Barberia, id_)

    def update(self, id_: int, data: BarberiaUpdate) -> Optional[Barberia]:
        """Actualiza una barbería existente."""
        barberia = self._session.get(Barberia, id_)
        if not barberia:
            return None
        # `exclude_unset=True` para que sólo se actualicen los campos enviados.
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(barberia, key, value)
        self._session.commit()
        self._session.refresh(barberia)
        return barberia

    def delete(self, obj: Barberia) -> None:
        """Elimina una barbería por ID. Devuelve True si se eliminó."""
        self._session.delete(obj)
        self._session.commit()

