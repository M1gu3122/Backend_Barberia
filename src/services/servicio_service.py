

from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.servicio_model import Servicio, EstadoServicio
from src.schemas.servicio_schema import ServicioCreate, ServicioUpdate, ServicioResponse
from src.repositories.servicio_repository import ServicioRepository
from src.services.base_service import BaseService


class ServicioService(BaseService):
    def __init__(self, db: Session):
        repo = ServicioRepository(db)
        super().__init__(db=db, repository=repo)

    # ---------------------------------------------------------------
    #  CREATE
    # ---------------------------------------------------------------

    def crear_servicio(self, datos: ServicioCreate) -> ServicioResponse:
        """
        Reglas de negocio:
        1. El tipo de servicio no puede estar vacío.
        2. El tiempo estimado debe ser mayor a 0.
        3. El precio debe ser mayor a 0.
        """
        self.validar_no_vacio(datos.tipo_servicio, "tipo_servicio")
        self.validar_positivo(datos.tiempo_estimado, "tiempo_estimado")
        self.validar_positivo(float(datos.precio_servicio), "precio_servicio")

        # Crea el servicio en la base de datos
        servicio_orm = self._repo.create(datos)
        
        # Retorna el servicio serializado correctamente
        return ServicioResponse.model_validate(servicio_orm)


    # ---------------------------------------------------------------
    #  READ
    # ---------------------------------------------------------------

    def listar_servicios(self) -> List[ServicioResponse]:
        """Lista todos los servicios."""
        return [ServicioResponse.model_validate(s) for s in self._repo.get_all()]

    def obtener_servicio_por_id(self, id_servicio: int) -> Optional[ServicioResponse]:
        """Obtiene un servicio por su ID."""
        servicio = self._repo.get_by_id(id_servicio)
        if not servicio:
            return None
        return ServicioResponse.model_validate(servicio)

    def listar_servicios_activos(self) -> List[ServicioResponse]:
        """Lista solo los servicios activos."""
        return [ServicioResponse.model_validate(s) for s in self._repo.get_by_estado(EstadoServicio.ACTIVO)]

    def buscar_servicios(self, termino: str) -> List[ServicioResponse]:
        """Busca servicios por tipo (búsqueda parcial)."""
        return [ServicioResponse.model_validate(s) for s in self._repo.get_by_tipo(termino)]

    # ---------------------------------------------------------------
    #  UPDATE
    # ---------------------------------------------------------------

    def actualizar_servicio(self, id_servicio: int, datos: ServicioUpdate) -> Optional[ServicioResponse]:
        """Actualiza un servicio existente."""
        servicio = self._repo.get_by_id(id_servicio)
        if not servicio:
            return None

        # Actualiza el objeto
        update_data = datos.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(servicio, key, value)

        self._repo.update(id_servicio, datos)  # Aquí ya se actualiza correctamente
        return ServicioResponse.model_validate(servicio)

    # ---------------------------------------------------------------
    #  DELETE
    # ---------------------------------------------------------------

    def eliminar_servicio(self, id_servicio: int) -> bool:
        """Elimina un servicio. Devuelve True si se eliminó."""
        return self._repo.delete(id_servicio)
