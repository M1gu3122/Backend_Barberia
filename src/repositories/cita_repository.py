# src/repositories/cita_repository.py
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.models.cita_model import Cita, EstadoCita
from src.schemas.cita_schema import CitaCreate, CitaUpdate

class CitaRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, id_: int) -> Optional[Cita]:
        return self._db.query(Cita).filter(Cita.id_cita == id_).first()

    def get_all(self) -> List[Cita]:
        return self._db.query(Cita).all()

    def create(self, cita_data: CitaCreate) -> Cita:
        cita = Cita(**cita_data.model_dump())
        self._db.add(cita)
        self._db.commit()
        self._db.refresh(cita)
        return cita

    def update(self, id_: int, updates: CitaUpdate) -> Optional[Cita]:
        cita = self._db.query(Cita).filter(Cita.id_cita == id_).first()
        if not cita:
            return None

        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(cita, key, value)

        self._db.commit()
        self._db.refresh(cita)
        return cita

    def delete(self, id_: int) -> bool:
        cita = self._db.query(Cita).filter(Cita.id_cita == id_).first()
        if not cita:
            return False

        self._db.delete(cita)
        self._db.commit()
        return True

    # Métodos personalizados
    def get_by_cliente(self, id_cliente: int) -> List[Cita]:
        return self._db.query(Cita).filter(Cita.id_cliente == id_cliente).order_by(Cita.fecha_hora.desc()).all()

    def get_by_barbero(self, id_barbero: int) -> List[Cita]:
        return self._db.query(Cita).filter(Cita.id_barbero == id_barbero).order_by(Cita.fecha_hora.desc()).all()

    def get_by_barberia(self, id_barberia: int) -> List[Cita]:
        return self._db.query(Cita).filter(Cita.id_barberia == id_barberia).order_by(Cita.fecha_hora.desc()).all()

    def get_by_estado(self, estado: EstadoCita) -> List[Cita]:
        return self._db.query(Cita).filter(Cita.estado_cita == estado).order_by(Cita.fecha_hora).all()

   
    def get_by_fecha(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[Cita]:
        return self._db.query(Cita).filter(
            Cita.fecha_hora >= fecha_inicio,
            Cita.fecha_hora <= fecha_fin
        ).order_by(Cita.fecha_hora).all()

    def get_barbero_disponible(self, id_barbero: int, fecha_hora: datetime, duracion_min: int = 30) -> bool:
        fin = fecha_hora + datetime.timedelta(minutes=duracion_min)
        # Corregido: el filtro estaba mal
        cita_disponible = self._db.query(Cita).filter(
            Cita.id_barbero == id_barbero,
            Cita.estado_cita.in_([EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]),
            Cita.fecha_hora < fin,
            Cita.fecha_hora >= fecha_hora
        ).first()
        return cita_disponible is None

    def cambiar_estado(self, id_: int, nuevo_estado: EstadoCita) -> Optional[Cita]:
        cita = self._db.query(Cita).filter(Cita.id_cita == id_).first()
        if not cita:
            return None
        cita.estado_cita = nuevo_estado
        self._db.commit()
        self._db.refresh(cita)
        return cita

    def exists(self, id_: int) -> bool:
        return self.get_by_id(id_) is not None

    def get_citas_por_rango_fecha(self, fecha_inicio: datetime, fecha_fin: datetime, estados: List[EstadoCita] = None) -> List[Cita]:
        query = self._db.query(Cita).filter(
            Cita.fecha_hora >= fecha_inicio,
            Cita.fecha_hora <= fecha_fin
        )
        
        if estados:
            query = query.filter(Cita.estado_cita.in_(estados))
            
        return query.order_by(Cita.fecha_hora).all()

    def get_citas_disponibles_para_fecha(self, fecha: datetime, duracion_min: int = 30) -> List[Cita]:
        return self._db.query(Cita).filter(
            Cita.fecha_hora >= fecha,
            Cita.fecha_hora < datetime.combine(fecha.date(), datetime.min.time()) + datetime.timedelta(days=1),
            Cita.estado_cita.in_([EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA])
        ).order_by(Cita.fecha_hora).all()
