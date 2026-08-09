# src/repositories/barbero_servicio.py
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.barbero_servicio_model import BarberoServicio
from src.schemas.barbero_servicio_schema import BarberoServicioCreate, BarberoServicioUpdate
from src.repositories.base_repository import Repository


class BarberoServicioRepository(Repository[BarberoServicio]):
    def __init__(self, db: Session):
        super().__init__(BarberoServicio, db)

    def get_by_barbero(self, id_usuario: int) -> List[BarberoServicio]:
        """Obtiene todos los servicios asociados a un barbero."""
        return self._session.query(BarberoServicio).filter(BarberoServicio.id_usuario == id_usuario).all()

    def get_by_servicio(self, id_servicio: int) -> List[BarberoServicio]:
        """Obtiene todos los barberos asociados a un servicio."""
        return self._session.query(BarberoServicio).filter(BarberoServicio.id_servicio == id_servicio).all()

    def get_by_barbero_and_servicio(self, id_usuario: int, id_servicio: int) -> Optional[BarberoServicio]:
        """Obtiene una relación específica por barbero y servicio."""
        return self._session.query(BarberoServicio).filter(
            BarberoServicio.id_usuario == id_usuario,
            BarberoServicio.id_servicio == id_servicio
        ).first()

    def create(self, data: BarberoServicioCreate) -> BarberoServicio:
        """Crea una nueva relación barbero-servicio."""
        barbero_servicio = BarberoServicio(**data.model_dump())
        self._session.add(barbero_servicio)
        self._session.commit()
        self._session.refresh(barbero_servicio)
        return barbero_servicio

    def delete_by_barbero_and_servicio(self, id_usuario: int, id_servicio: int) -> bool:
        """Elimina una relación específica."""
        barbero_servicio = self.get_by_barbero_and_servicio(id_usuario, id_servicio)
        if barbero_servicio:
            self._session.delete(barbero_servicio)
            self._session.commit()
            return True
        return False
