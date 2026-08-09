# src/services/cita_servicio_service.py
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.cita_servicio_model import CitaServicio
from src.schemas.cita_servicio_schema import CitaServicioCreate, CitaServicioUpdate, CitaServicioResponse
from src.repositories.cita_servicio_repository import CitaServicioRepository
from src.services.base_service import BaseService


class CitaServicioService(BaseService[CitaServicio]):
    def __init__(self, db: Session):
        repo = CitaServicioRepository(db)
        super().__init__(db=db, repository=repo)

    def crear_relacion(self, datos: CitaServicioCreate) -> CitaServicioResponse:
        """Crea una nueva relación cita-servicio."""
        relacion_orm = self._repo.create(datos)
        return CitaServicioResponse.model_validate(relacion_orm)

    def obtener_relacion(self, id_cita: int, id_servicio: int) -> Optional[CitaServicioResponse]:
        """Obtiene una relación específica."""
        relacion = self._repo.get_by_cita_and_servicio(id_cita, id_servicio)
        if not relacion:
            return None
        return CitaServicioResponse.model_validate(relacion)

    def obtener_servicios_por_cita(self, id_cita: int) -> List[CitaServicioResponse]:
        """Obtiene todos los servicios asociados a una cita."""
        relaciones = self._repo.get_by_cita(id_cita)
        return [CitaServicioResponse.model_validate(r) for r in relaciones]

    def obtener_citas_por_servicio(self, id_servicio: int) -> List[CitaServicioResponse]:
        """Obtiene todas las citas que incluyen un servicio."""
        relaciones = self._repo.get_by_servicio(id_servicio)
        return [CitaServicioResponse.model_validate(r) for r in relaciones]

    def eliminar_relacion(self, id_cita: int, id_servicio: int) -> bool:
        """Elimina una relación cita-servicio."""
        return self._repo.delete_by_cita_and_servicio(id_cita, id_servicio)
