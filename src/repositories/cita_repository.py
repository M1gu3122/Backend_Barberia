# src/repositories/cita_repository.py
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from src.models.cita_model import Cita, EstadoCita
from src.models.servicio_model import Servicio
from src.schemas.cita_schema import CitaCreate, CitaUpdate

class CitaRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, id_: int) -> Optional[Cita]:
        return self._db.query(Cita).filter(Cita.id_cita == id_).first()

    def get_all(self) -> List[Cita]:
        return self._db.query(Cita).all()

    def create(self, cita_data: CitaCreate) -> Cita:
        cita = Cita(**cita_data.model_dump(exclude={"ids_servicios"}))
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

    def existe_cita_solapada(
        self, id_barbero: int, fecha_hora: datetime, id_cita_actual: int
    ) -> bool:
        """Comprueba si existe otra cita distinta a `id_cita_actual` para el
        mismo barbero en la misma fecha/hora.
        Se normaliza la zona horaria comparando contra el almacenado en la BD
        (que es naive)."""
        from zoneinfo import ZoneInfo

        # Normalizar a naive si la BD almacena naive y la entrada trae tz
        if fecha_hora.tzinfo is not None:
            fecha_hora = fecha_hora.replace(tzinfo=None)

        return (
            self._db.query(Cita)
            .filter(
                Cita.id_barbero == id_barbero,
                Cita.fecha_hora == fecha_hora,
                Cita.id_cita != id_cita_actual,
            )
            .first()
            is not None
        )

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

    def get_citas_con_detalle(self, id_cliente: Optional[int] = None) -> List[dict]:
        """
        Obtiene las citas con los servicios agrupados y los datos del
        cliente y del barbero. Si se pasa `id_cliente`, filtra por ese cliente.

        Equivale a:
SELECT u.id_usuario, c.id_cita, c.id_barbero,
               u.nombres, u.apellidos, u.telefono, u.correo,
               GROUP_CONCAT(s.nombre_servicio SEPARATOR ', ') AS servicios,
               func.coalesce(func.sum(Servicio.tiempo_estimado), 0).label("tiempo_total"),
               eb.nombres AS nombres_barbero, eb.apellidos AS apellidos_barbero,
               c.fecha_hora, c.estado_cita
        FROM cita c
        INNER JOIN usuario u ON u.id_usuario = c.id_cliente
        INNER JOIN cita_servicio cs ON c.id_cita = cs.id_cita
        INNER JOIN servicio s ON s.id_servicio = cs.id_servicio
        INNER JOIN empleado e ON e.id_usuario = c.id_barbero
        INNER JOIN usuario eb ON eb.id_usuario = e.id_usuario
        [WHERE u.id_usuario = :id_cliente]
        GROUP BY u.id_usuario, c.id_cita, c.id_barbero,
                 u.nombres, u.apellidos, u.telefono, u.correo,
                 eb.nombres, eb.apellidos, c.fecha_hora, c.estado_cita
        ORDER BY c.fecha_hora DESC
        """
        from sqlalchemy.orm import aliased
        from src.models.usuario_model import Usuario
        from src.models.cita_servicio_model import CitaServicio
        from src.models.servicio_model import Servicio
        from src.models.empleado_model import Empleado

        Barbero = aliased(Usuario)

        query = (
            self._db.query(
                Usuario.id_usuario,
                Cita.id_cita,
                Cita.id_barbero,
                Usuario.nombres,
                Usuario.apellidos,
                Usuario.telefono,
                Usuario.correo,
                func.group_concat(
                    Servicio.nombre_servicio.op("SEPARATOR")(text("', '"))
                ).label("servicios"),
                func.coalesce(
                    func.sum(Servicio.tiempo_estimado),
                    0
                ).label("tiempo_total"),
                Barbero.nombres.label("nombres_barbero"),
                Barbero.apellidos.label("apellidos_barbero"),
                Cita.fecha_hora,
                Cita.estado_cita,
            )
            .join(Usuario, Usuario.id_usuario == Cita.id_cliente)
            .join(CitaServicio, Cita.id_cita == CitaServicio.id_cita)
            .join(Servicio, Servicio.id_servicio == CitaServicio.id_servicio)
            .join(Empleado, Empleado.id_usuario == Cita.id_barbero)
            .join(Barbero, Barbero.id_usuario == Empleado.id_usuario)
            .group_by(
                Usuario.id_usuario,
                Cita.id_cita,
                Cita.id_barbero,
                Usuario.nombres,
                Usuario.apellidos,
                Usuario.telefono,
                Usuario.correo,
                Barbero.nombres,
                Barbero.apellidos,
                Cita.fecha_hora,
                Cita.estado_cita,
            )
        )

        if id_cliente is not None:
            query = query.filter(Usuario.id_usuario == id_cliente)

        rows = query.order_by(Cita.fecha_hora.desc()).all()

        return [
            {
                "id_usuario": id_usuario,
                "id_cita": id_cita,
                "id_barbero": id_barbero,
                "nombres": nombres,
                "apellidos": apellidos,
                "telefono": telefono,
                "correo": correo,
                "servicios": servicios,
                "tiempo_total": tiempo_total,
                "nombres_barbero": nombres_barbero,
                "apellidos_barbero": apellidos_barbero,
                "fecha_hora": fecha_hora,
                "estado_cita": estado_cita,
            }
            for (
                id_usuario,
                id_cita,
                id_barbero,
                nombres,
                apellidos,
                telefono,
                correo,
                servicios,
                tiempo_total,
                nombres_barbero,
                apellidos_barbero,
                fecha_hora,
                estado_cita,
            ) in rows
        ]