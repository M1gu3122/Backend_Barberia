# src/repositories/horario_barberia_repository.py
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.horario_barberia_model import HorarioBarberia
from src.schemas.horario_barberia_schema import (
    HorarioBarberiaCreate,
    HorarioBarberiaUpdate,
)
from src.repositories.base_repository import Repository


class HorarioBarberiaRepository(Repository[HorarioBarberia]):
    def __init__(self, db: Session):
        super().__init__(HorarioBarberia, db)

    def create(self, data: HorarioBarberiaCreate) -> HorarioBarberia:
        """Crea un nuevo horario."""
        horario = HorarioBarberia(**data.model_dump())
        self._session.add(horario)
        self._session.commit()
        self._session.refresh(horario)
        return horario

    def get_all(self) -> List[HorarioBarberia]:
        """Obtiene todos los horarios."""
        return self._session.query(HorarioBarberia).all()

    def update(self, id_: int, data: HorarioBarberiaUpdate) -> Optional[HorarioBarberia]:
        """Actualiza un horario existente."""
        horario = self._session.get(HorarioBarberia, id_)
        if not horario:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(horario, key, value)
        self._session.commit()
        self._session.refresh(horario)
        return horario

    def get_by_id(self, id_: int) -> Optional[HorarioBarberia]:
        """Obtiene un horario por su ID."""
        return self._session.get(HorarioBarberia, id_)

    def delete(self, id_: int) -> bool:
        """Elimina un horario por ID. Devuelve True si se eliminó."""
        horario = self._session.get(HorarioBarberia, id_)
        if not horario:
            return False
        self._session.delete(horario)
        self._session.commit()
        return True

    def get_by_barberia(self, id_barberia: int) -> List[HorarioBarberia]:
        """Obtiene todos los horarios de una barbería."""
        return (
            self._session.query(HorarioBarberia)
            .filter(HorarioBarberia.id_barberia == id_barberia)
            .order_by(HorarioBarberia.dia_semana)
            .all()
        )

    def get_by_dia(self, id_barberia: int, dia_semana: str) -> Optional[HorarioBarberia]:
        """Obtiene el horario de un día concreto de una barbería."""
        return (
            self._session.query(HorarioBarberia)
            .filter(
                HorarioBarberia.id_barberia == id_barberia,
                HorarioBarberia.dia_semana == dia_semana,
            )
            .first()
        )

    def get_dias_abiertos(self, id_barberia: int) -> List[HorarioBarberia]:
        """Obtiene los días en los que la barbería atiende (no festivos)."""
        return self.get_by_barberia(id_barberia)

    def get_horario_para_fecha(self, id_barberia: int, fecha: object) -> Optional[HorarioBarberia]:
        """
        Obtiene el horario de la barbería para la fecha indicada,
        resolviendo el día de la semana (Lunes...Domingo) automáticamente.
        """
        dias = {
            0: "Lunes",
            1: "Martes",
            2: "Miércoles",
            3: "Jueves",
            4: "Viernes",
            5: "Sábado",
            6: "Domingo",
        }
        dia_semana = dias.get(fecha.weekday())
        if not dia_semana:
            return None
        return self.get_by_dia(id_barberia, dia_semana)