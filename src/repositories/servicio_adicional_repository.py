# src/repositories/servicio_adicional_repository.py
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.servicio_adicional_model import ServicioAdicional
from src.schemas.servicio_adicional_schema import ServicioAdicionalCreate
from src.repositories.base_repository import Repository


class ServicioAdicionalRepository(Repository[ServicioAdicional]):
    def __init__(self, db: Session):
        super().__init__(ServicioAdicional, db)

    def create(self, data: ServicioAdicionalCreate) -> ServicioAdicional:
        """Crea una nueva relación principal-adicional."""
        relacion = ServicioAdicional(**data.model_dump())
        self._session.add(relacion)
        self._session.commit()
        self._session.refresh(relacion)
        return relacion

    def get_all(self) -> List[ServicioAdicional]:
        """Obtiene todas las relaciones principal-adicional."""
        return self._session.query(ServicioAdicional).all()

    def get_by_servicio(self, id_servicio: int) -> List[ServicioAdicional]:
        """Obtiene los adicionales permitidos para un servicio principal."""
        return (
            self._session.query(ServicioAdicional)
            .filter(ServicioAdicional.id_servicio == id_servicio)
            .all()
        )

    def get_ids_adicionales_permitidos(self, id_servicio: int) -> List[int]:
        """Obtiene solo los IDs de los adicionales permitidos para un principal."""
        rows = (
            self._session.query(ServicioAdicional.id_adicional)
            .filter(ServicioAdicional.id_servicio == id_servicio)
            .all()
        )
        return [row[0] for row in rows]

    def get_by_adicional(self, id_adicional: int) -> List[ServicioAdicional]:
        """Obtiene los servicios principales que permiten un adicional concreto."""
        return (
            self._session.query(ServicioAdicional)
            .filter(ServicioAdicional.id_adicional == id_adicional)
            .all()
        )

    def get_by_servicio_and_adicional(
        self, id_servicio: int, id_adicional: int
    ) -> Optional[ServicioAdicional]:
        """Obtiene una relación específica principal-adicional."""
        return (
            self._session.query(ServicioAdicional)
            .filter(
                ServicioAdicional.id_servicio == id_servicio,
                ServicioAdicional.id_adicional == id_adicional,
            )
            .first()
        )

    def delete_by_servicio_and_adicional(self, id_servicio: int, id_adicional: int) -> bool:
        """Elimina una relación principal-adicional."""
        relacion = self.get_by_servicio_and_adicional(id_servicio, id_adicional)
        if not relacion:
            return False
        self._session.delete(relacion)
        self._session.commit()
        return True