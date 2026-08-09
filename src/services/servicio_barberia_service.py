# src/services/servicio_barberia_service.py
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.servicio_barberia_model import ServicioBarberia
from src.schemas.servicio_barberia_schema import ServicioBarberiaCreate, ServicioBarberiaUpdate, ServicioBarberiaResponse
from src.repositories.servicio_barberia_repository import ServicioBarberiaRepository
from src.services.base_service import BaseService


class ServicioBarberiaService(BaseService[ServicioBarberia]):
    def __init__(self, db: Session):
        repo = ServicioBarberiaRepository(db)
        super().__init__(db=db, repository=repo)

    def crear_relacion(self, datos: ServicioBarberiaCreate) -> ServicioBarberiaResponse:
        """Crea una nueva relación servicio-barbería."""
        relacion_orm = self._repo.create(datos)
        return ServicioBarberiaResponse.model_validate(relacion_orm)

    def obtener_relacion(self, id_barberia: int, id_servicio: int) -> Optional[ServicioBarberiaResponse]:
        """Obtiene una relación específica."""
        relacion = self._repo.get_by_barberia_and_servicio(id_barberia, id_servicio)
        if not relacion:
            return None
        return ServicioBarberiaResponse.model_validate(relacion)

    def actualizar_relacion(self, id_barberia: int, id_servicio: int, datos: ServicioBarberiaUpdate) -> Optional[ServicioBarberiaResponse]:
        """Actualiza una relación servicio-barbería existente."""
        relacion_actualizada = self._repo.update(id_barberia, id_servicio, datos)
        if not relacion_actualizada:
            return None
        return ServicioBarberiaResponse.model_validate(relacion_actualizada)

    def obtener_servicios_por_barberia(self, id_barberia: int) -> List[ServicioBarberiaResponse]:
        """Obtiene todos los servicios asociados a una barbería."""
        relaciones = self._repo.get_by_barberia(id_barberia)
        return [ServicioBarberiaResponse.model_validate(r) for r in relaciones]

    def obtener_barberias_por_servicio(self, id_servicio: int) -> List[ServicioBarberiaResponse]:
        """Obtiene todas las barberías que ofrecen un servicio."""
        relaciones = self._repo.get_by_servicio(id_servicio)
        return [ServicioBarberiaResponse.model_validate(r) for r in relaciones]

    def eliminar_relacion(self, id_barberia: int, id_servicio: int) -> bool:
        """Elimina una relación servicio-barbería."""
        return self._repo.delete_by_barberia_and_servicio(id_barberia, id_servicio)
