# src/repositories/cita_servicio.py
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.cita_servicio_model import CitaServicio
from src.schemas.cita_servicio_schema import CitaServicioCreate, CitaServicioUpdate
from src.repositories.base_repository import Repository


class CitaServicioRepository(Repository[CitaServicio]):
    def __init__(self, db: Session):
        super().__init__(CitaServicio, db)

    def get_by_cita(self, id_cita: int) -> List[CitaServicio]:
        """Obtiene todos los servicios asociados a una cita."""
        return self._session.query(CitaServicio).filter(CitaServicio.id_cita == id_cita).all()

    def get_by_servicio(self, id_servicio: int) -> List[CitaServicio]:
        """Obtiene todas las citas que incluyen un servicio."""
        return self._session.query(CitaServicio).filter(CitaServicio.id_servicio == id_servicio).all()

    def get_by_cita_and_servicio(self, id_cita: int, id_servicio: int) -> Optional[CitaServicio]:
        """Obtiene una relación específica por cita y servicio."""
        return self._session.query(CitaServicio).filter(
            CitaServicio.id_cita == id_cita,
            CitaServicio.id_servicio == id_servicio
        ).first()
        
    def get_servicios_by_cita(self, id_cita: int) -> List[CitaServicio]:
        """Obtiene todos los servicios asociados a una cita."""
        return self._session.query(CitaServicio).filter(CitaServicio.id_cita == id_cita).all()


    def create(self, data: CitaServicioCreate) -> CitaServicio:
        """Crea una nueva relación cita-servicio."""
        cita_servicio = CitaServicio(**data.model_dump())
        self._session.add(cita_servicio)
        self._session.flush()
        self._session.refresh(cita_servicio)  # Obtener ID en MySQL
        return cita_servicio

    def delete_by_cita_and_servicio(self, id_cita: int, id_servicio: int) -> bool:
        """Elimina una relación específica."""
        cita_servicio = self.get_by_cita_and_servicio(id_cita, id_servicio)
        if cita_servicio:
            self._session.delete(cita_servicio)
            self._session.commit()
            return True
        return False

    def delete_by_cita(self, id_cita: int) -> bool:
        """Elimina todas las relaciones de una cita."""
        citas_servicios = self._session.query(CitaServicio).filter(
            CitaServicio.id_cita == id_cita
        ).all()
        if not citas_servicios:
            return False
        for cs in citas_servicios:
            self._session.delete(cs)
        self._session.commit()
        return True
