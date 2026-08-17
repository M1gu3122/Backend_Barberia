# src/services/barbero_servicio_service.py
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.barbero_servicio_model import BarberoServicio
from src.schemas.barbero_servicio_schema import BarberoServicioCreate, BarberoServicioUpdate, BarberoServicioResponse, BarberoDisponibleResponse
from src.repositories.barbero_servicio_repository import BarberoServicioRepository
from src.services.base_service import BaseService


class BarberoServicioService(BaseService[BarberoServicio]):
    def __init__(self, db: Session):
        repo = BarberoServicioRepository(db)
        super().__init__(db=db, repository=repo)

    def crear_relacion(self, datos: BarberoServicioCreate) -> BarberoServicioResponse:
        """Crea una nueva relación barbero-servicio."""
        relacion_orm = self._repo.create(datos)
        return BarberoServicioResponse.model_validate(relacion_orm)

    def obtener_relacion(self, id_usuario: int, id_servicio: int) -> Optional[BarberoServicioResponse]:
        """Obtiene una relación específica."""
        relacion = self._repo.get_by_barbero_and_servicio(id_usuario, id_servicio)
        if not relacion:
            return None
        return BarberoServicioResponse.model_validate(relacion)

    def obtener_servicios_por_barbero(self, id_usuario: int) -> List[BarberoServicioResponse]:
        """Obtiene todos los servicios asociados a un barbero."""
        relaciones = self._repo.get_by_barbero(id_usuario)
        return [BarberoServicioResponse.model_validate(r) for r in relaciones]

    def obtener_barberos_por_servicio(self, id_servicio: int) -> List[BarberoServicioResponse]:
        """Obtiene todos los barberos asociados a un servicio."""
        relaciones = self._repo.get_by_servicio(id_servicio)
        return [BarberoServicioResponse.model_validate(r) for r in relaciones]

    def eliminar_relacion(self, id_usuario: int, id_servicio: int) -> bool:
        """Elimina una relación barbero-servicio."""
        return self._repo.delete_by_barbero_and_servicio(id_usuario, id_servicio)

    def obtener_barberos_con_todos_los_servicios(self, ids_servicio: List[int]) -> List[BarberoDisponibleResponse]:
        """Obtiene los barberos activos que pueden realizar todos los servicios indicados."""
        return [
            BarberoDisponibleResponse.model_validate(b)
            for b in self._repo.get_barberos_con_todos_los_servicios(ids_servicio)
        ]
