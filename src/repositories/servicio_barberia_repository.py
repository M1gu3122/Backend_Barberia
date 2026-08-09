# src/repositories/servicio_barberia.py
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.servicio_barberia_model import ServicioBarberia
from src.schemas.servicio_barberia_schema import ServicioBarberiaCreate, ServicioBarberiaUpdate
from src.repositories.base_repository import Repository


class ServicioBarberiaRepository(Repository[ServicioBarberia]):
    def __init__(self, db: Session):
        super().__init__(ServicioBarberia, db)

    def get_by_barberia(self, id_barberia: int) -> List[ServicioBarberia]:
        """Obtiene todos los servicios asociados a una barbería."""
        return self._session.query(ServicioBarberia).filter(ServicioBarberia.id_barberia == id_barberia).all()

    def get_by_servicio(self, id_servicio: int) -> List[ServicioBarberia]:
        """Obtiene todas las barberías que ofrecen un servicio."""
        return self._session.query(ServicioBarberia).filter(ServicioBarberia.id_servicio == id_servicio).all()

    def get_by_barberia_and_servicio(self, id_barberia: int, id_servicio: int) -> Optional[ServicioBarberia]:
        """Obtiene una relación específica por barbería y servicio."""
        return self._session.query(ServicioBarberia).filter(
            ServicioBarberia.id_barberia == id_barberia,
            ServicioBarberia.id_servicio == id_servicio
        ).first()

    def create(self, data: ServicioBarberiaCreate) -> ServicioBarberia:
        """Crea una nueva relación servicio-barbería."""
        servicio_barberia = ServicioBarberia(**data.model_dump())
        self._session.add(servicio_barberia)
        self._session.commit()
        self._session.refresh(servicio_barberia)
        return servicio_barberia

    def update(self, id_barberia: int, id_servicio: int, data: ServicioBarberiaUpdate) -> Optional[ServicioBarberia]:
        """Actualiza una relación servicio-barbería existente."""
        servicio_barberia = self.get_by_barberia_and_servicio(id_barberia, id_servicio)
        if not servicio_barberia:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(servicio_barberia, key, value)
            
        self._session.commit()
        self._session.refresh(servicio_barberia)
        return servicio_barberia

    def delete_by_barberia_and_servicio(self, id_barberia: int, id_servicio: int) -> bool:
        """Elimina una relación específica."""
        servicio_barberia = self.get_by_barberia_and_servicio(id_barberia, id_servicio)
        if servicio_barberia:
            self._session.delete(servicio_barberia)
            self._session.commit()
            return True
        return False
