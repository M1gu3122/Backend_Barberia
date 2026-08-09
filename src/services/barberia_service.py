# src/services/barberia_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

from src.models.barberia_model import Barberia
from src.schemas.barberia_schema import BarberiaCreate, BarberiaUpdate, BarberiaResponse
from src.repositories.barberia_repository import BarberiaRepository
from src.services.base_service import BaseService


class BarberiaService(BaseService[Barberia]):
    def __init__(self, db: Session):
        repo = BarberiaRepository(db)
        super().__init__(db=db, repository=repo)

    # ---------------------------------------------------------------
    #  CREATE
    # ---------------------------------------------------------------
    def crear_barberia(self, datos: BarberiaCreate) -> BarberiaResponse:
        """
        Reglas de negocio:
        1. El nombre de la barbería no puede estar vacío.
        2. La dirección no puede estar vacía.
        """
        if not datos.nombre_barberia or not datos.nombre_barberia.strip():
            raise ValueError("El nombre de la barbería es obligatorio")

        if not datos.direccion or not datos.direccion.strip():
            raise ValueError("La dirección es obligatoria")

        barberia_orm = self._repo.create(datos)
        return BarberiaResponse.model_validate(barberia_orm)

    # ---------------------------------------------------------------
    #  READ
    # ---------------------------------------------------------------
    def obtener_barberia(self) -> BarberiaResponse:
        """Obtiene la única barbería existente."""
        barberia = self._repo.get_by_id(1)  # ID fijo para barbería única
        if not barberia:
            raise HTTPException(status_code=404, detail="Barbería no encontrada")
        return BarberiaResponse.model_validate(barberia)

    # ---------------------------------------------------------------
    #  UPDATE
    # ---------------------------------------------------------------
    def actualizar_barberia(self, datos: BarberiaUpdate) -> BarberiaResponse:
        """Actualiza la única barbería."""
        barberia = self._repo.get_by_id(1)
        if not barberia:
            raise HTTPException(status_code=404, detail="Barbería no encontrada")

        update_data = datos.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(barberia, key, value)

        self._repo.update(1, datos)  # ID fijo
        return BarberiaResponse.model_validate(barberia)

    # ---------------------------------------------------------------
    #  DELETE
    # ---------------------------------------------------------------def eliminar_barberia(self, id_barberia: int) -> bool:
    def eliminar_barberia(self, id_barberia: int) -> bool:
        barberia = self._repo.get_by_id(id_barberia)
        if barberia:
            self._repo.delete(barberia)  # Esto ya hace el commit
            return True
        return False



