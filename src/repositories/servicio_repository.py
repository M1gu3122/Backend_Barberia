# src/repositories/servicio.py

from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.servicio_model import Servicio, EstadoServicio
from src.schemas.servicio_schema import ServicioCreate, ServicioUpdate
from src.repositories.base_repository import Repository


class ServicioRepository(Repository[Servicio]):
    def __init__(self, db: Session):
        super().__init__(Servicio, db)

    def get_by_estado(self, estado: EstadoServicio) -> List[Servicio]:
        """Obtiene servicios filtrados por estado (Activo/Inactivo)."""
        return self._session.query(Servicio).filter(Servicio.estado_servicio == estado).all()

    def get_by_tipo(self, tipo_servicio: str) -> List[Servicio]:
        """Obtiene servicios cuyo tipo coincida (búsqueda parcial)."""
        return (
            self._session.query(Servicio)
            .filter(Servicio.tipo_servicio.ilike(f"%{tipo_servicio}%"))
            .all()
        )
    def get_servicio_by_id(self, id_servicio: int) -> Optional[Servicio]:
        """Obtiene un servicio por su ID."""
        return self._session.query(Servicio).filter(Servicio.id_servicio == id_servicio).first()


    def get_activos(self) -> List[Servicio]:
        """Obtiene todos los servicios activos."""
        return self.get_by_estado(EstadoServicio.ACTIVO)

    def create(self, servicio_data: ServicioCreate) -> Servicio:
        """Crea un nuevo servicio."""
        servicio = Servicio(**servicio_data.model_dump())
        self._session.add(servicio)
        self._session.commit()
        return servicio

    def update(self, id_: int, updates: ServicioUpdate) -> Optional[Servicio]:
        """Actualiza un servicio existente."""
        servicio = self._session.get(Servicio, id_)
        if not servicio:
            return None

        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(servicio, key, value)

        self._session.commit()
        self._session.refresh(servicio)
        return servicio

    def delete(self, id_: int) -> bool:
        """Elimina un servicio por ID."""
        servicio = self._session.get(Servicio, id_)
        if not servicio:
            return False

        self._session.delete(servicio)
        self._session.commit()
        return True
