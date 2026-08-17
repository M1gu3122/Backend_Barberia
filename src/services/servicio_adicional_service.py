# src/services/servicio_adicional_service.py
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.servicio_adicional_model import ServicioAdicional
from src.schemas.servicio_adicional_schema import (
    ServicioAdicionalCreate,
    ServicioAdicionalResponse,
)
from src.repositories.servicio_adicional_repository import ServicioAdicionalRepository
from src.repositories.servicio_repository import ServicioRepository
from src.services.base_service import BaseService


class ServicioAdicionalService(BaseService[ServicioAdicional]):
    def __init__(self, db: Session):
        repo = ServicioAdicionalRepository(db)
        super().__init__(db=db, repository=repo)
        self._sa_repo = repo
        self._servicio_repo = ServicioRepository(db)

    # ---------------------------------------------------------------
    #  Validaciones
    # ---------------------------------------------------------------
    def _validar_servicios(self, id_servicio: int, id_adicional: int) -> None:
        if not self._servicio_repo.get_servicio_by_id(id_servicio):
            raise ValueError(f"El servicio principal con ID {id_servicio} no existe")
        if not self._servicio_repo.get_servicio_by_id(id_adicional):
            raise ValueError(f"El servicio adicional con ID {id_adicional} no existe")
        if id_servicio == id_adicional:
            raise ValueError("Un servicio no puede ser adicional de sí mismo")

    # ---------------------------------------------------------------
    #  CREATE
    # ---------------------------------------------------------------
    def crear_relacion(self, datos: ServicioAdicionalCreate) -> ServicioAdicionalResponse:
        """Crea una relación de compatibilidad principal-adicional."""
        self._validar_servicios(datos.id_servicio, datos.id_adicional)

        if self._sa_repo.get_by_servicio_and_adicional(
            datos.id_servicio, datos.id_adicional
        ):
            raise ValueError(
                f"La relación {datos.id_servicio}->{datos.id_adicional} ya existe"
            )

        relacion_orm = self._sa_repo.create(datos)
        return ServicioAdicionalResponse.model_validate(relacion_orm)

    # ---------------------------------------------------------------
    #  READ
    # ---------------------------------------------------------------
    def listar_relaciones(self) -> List[ServicioAdicionalResponse]:
        """Obtiene todas las relaciones de compatibilidad."""
        return [
            ServicioAdicionalResponse.model_validate(r)
            for r in self._sa_repo.get_all()
        ]

    def obtener_relacion(
        self, id_servicio: int, id_adicional: int
    ) -> Optional[ServicioAdicionalResponse]:
        """Obtiene una relación específica."""
        relacion = self._sa_repo.get_by_servicio_and_adicional(id_servicio, id_adicional)
        if not relacion:
            return None
        return ServicioAdicionalResponse.model_validate(relacion)

    def obtener_adicionales_por_servicio(self, id_servicio: int) -> List[ServicioAdicionalResponse]:
        """Obtiene los adicionales permitidos para un servicio principal."""
        return [
            ServicioAdicionalResponse.model_validate(r)
            for r in self._sa_repo.get_by_servicio(id_servicio)
        ]

    def obtener_ids_adicionales_por_servicio(self, id_servicio: int) -> List[int]:
        """Obtiene solo los IDs de los adicionales permitidos para un principal."""
        return self._sa_repo.get_ids_adicionales_permitidos(id_servicio)

    # ---------------------------------------------------------------
    #  DELETE
    # ---------------------------------------------------------------
    def eliminar_relacion(self, id_servicio: int, id_adicional: int) -> bool:
        """Elimina una relación de compatibilidad."""
        return self._sa_repo.delete_by_servicio_and_adicional(id_servicio, id_adicional)