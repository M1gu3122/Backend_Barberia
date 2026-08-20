# src/repositories/cita_repository.py
from typing import List, Optional
from datetime import datetime, timedelta
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
        from sqlalchemy.exc import IntegrityError

        cita = Cita(**cita_data.model_dump(exclude={"ids_servicios"}))
        self._db.add(cita)
        try:
            self._db.flush()
            self._db.refresh(cita)  # Obtener ID auto-increment en MySQL
        except IntegrityError as e:
            self._db.rollback()
            err_msg = str(e.orig).lower()
            if "foreign key" in err_msg or "foreign_key" in err_msg:
                if "id_cliente" in err_msg or "usuario" in err_msg:
                    raise ValueError("El cliente (id_cliente) no existe")
                elif "id_barbero" in err_msg or "empleado" in err_msg:
                    raise ValueError("El barbero (id_barbero) no existe")
                elif "id_barberia" in err_msg or "barberia" in err_msg:
                    raise ValueError("La barbería (id_barberia) no existe")
            raise ValueError(f"Error de integridad al crear cita: {e.orig}")
        except Exception as e:
            self._db.rollback()
            raise ValueError(f"Error al crear cita: {e}")
        return cita

    def update(self, id_: int, updates: CitaUpdate) -> Optional[Cita]:
        cita = self._db.query(Cita).filter(Cita.id_cita == id_).first()
        if not cita:
            return None

        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
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
        return (
            self._db.query(Cita)
            .filter(Cita.id_cliente == id_cliente)
            .order_by(Cita.fecha_hora.desc())
            .all()
        )

    def get_by_barbero(self, id_barbero: int) -> List[Cita]:
        return (
            self._db.query(Cita)
            .filter(Cita.id_barbero == id_barbero)
            .order_by(Cita.fecha_hora.desc())
            .all()
        )

    def get_by_barberia(self, id_barberia: int) -> List[Cita]:
        return (
            self._db.query(Cita)
            .filter(Cita.id_barberia == id_barberia)
            .order_by(Cita.fecha_hora.desc())
            .all()
        )

    def existe_cita_solapada(
        self,
        id_barbero: int,
        fecha_hora: datetime,
        id_cita_actual: int = 0,
        duracion_minutos: int = 30,
    ) -> bool:
        """
        Verifica si existe una cita activa del mismo barbero
        que se solape con el intervalo de la nueva cita.

        Intervalos:
            nueva:     [fecha_hora, fecha_hora + duracion)
            existente: [cita.fecha_hora, cita.fecha_hora + duracion_existente)

        Hay solapamiento cuando:

            inicio_existente < fin_nueva
            AND
            inicio_nueva < fin_existente
        """

        from src.core.timezone import a_bd
        from src.models.cita_servicio_model import CitaServicio

        fecha_hora = a_bd(fecha_hora)

        fin_nueva = fecha_hora + timedelta(minutes=duracion_minutos)

        # Obtener las citas activas del barbero.
        citas = (
            self._db.query(Cita)
            .filter(
                Cita.id_barbero == id_barbero,
                Cita.id_cita != id_cita_actual,
                Cita.estado_cita.in_(
                    [
                        EstadoCita.PENDIENTE,
                        EstadoCita.CONFIRMADA,
                        EstadoCita.EN_ATENCION,
                    ]
                ),
            )
            .all()
        )

        for cita_existente in citas:

            # Obtener la duración total de los servicios
            # asociados a la cita existente.
            duracion_existente = (
                self._db.query(func.coalesce(func.sum(Servicio.tiempo_estimado), 30))
                .join(CitaServicio, CitaServicio.id_servicio == Servicio.id_servicio)
                .filter(CitaServicio.id_cita == cita_existente.id_cita)
                .scalar()
            )

            duracion_existente = int(duracion_existente or 30)

            inicio_existente = cita_existente.fecha_hora
            fin_existente = inicio_existente + timedelta(minutes=duracion_existente)

            # Comprobación REAL de solapamiento.
            if inicio_existente < fin_nueva and fecha_hora < fin_existente:
                return True

        return False

    def get_by_estado(self, estado: EstadoCita) -> List[Cita]:
        return (
            self._db.query(Cita)
            .filter(Cita.estado_cita == estado)
            .order_by(Cita.fecha_hora)
            .all()
        )

    def get_by_fecha(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[Cita]:
        return (
            self._db.query(Cita)
            .filter(Cita.fecha_hora >= fecha_inicio, Cita.fecha_hora <= fecha_fin)
            .order_by(Cita.fecha_hora)
            .all()
        )


    def get_barbero_disponible(
        self, id_barbero: int, fecha_hora: datetime, duracion_min: int = 30
    ) -> bool:

        from src.core.timezone import a_bd
        from src.models.cita_servicio_model import CitaServicio

        fecha_hora = a_bd(fecha_hora)

        fin_nueva = fecha_hora + timedelta(minutes=duracion_min)

        citas = (
            self._db.query(Cita)
            .filter(
                Cita.id_barbero == id_barbero,
                Cita.estado_cita.in_(
                    [
                        EstadoCita.PENDIENTE,
                        EstadoCita.CONFIRMADA,
                        EstadoCita.EN_ATENCION,
                    ]
                ),
            )
            .all()
        )

        for cita in citas:

            duracion = (
                self._db.query(func.coalesce(func.sum(Servicio.tiempo_estimado), 30))
                .join(CitaServicio, CitaServicio.id_servicio == Servicio.id_servicio)
                .filter(CitaServicio.id_cita == cita.id_cita)
                .scalar()
            )

            duracion = int(duracion or 30)

            inicio_existente = cita.fecha_hora
            fin_existente = inicio_existente + timedelta(minutes=duracion)

            if inicio_existente < fin_nueva and fecha_hora < fin_existente:
                return False

        return True

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

    def get_citas_por_rango_fecha(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        estados: List[EstadoCita] = None,
    ) -> List[Cita]:
        query = self._db.query(Cita).filter(
            Cita.fecha_hora >= fecha_inicio, Cita.fecha_hora <= fecha_fin
        )

        if estados:
            query = query.filter(Cita.estado_cita.in_(estados))

        return query.order_by(Cita.fecha_hora).all()

    def get_citas_disponibles_para_fecha(
        self, fecha: datetime, duracion_min: int = 30
    ) -> List[Cita]:
        return (
            self._db.query(Cita)
            .filter(
                Cita.fecha_hora >= fecha,
                Cita.fecha_hora
                < datetime.combine(fecha.date(), datetime.min.time())
                + timedelta(days=1),
                Cita.estado_cita.in_([EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]),
            )
            .order_by(Cita.fecha_hora)
            .all()
        )

    def get_proximas_citas(self, fecha: datetime) -> List[Cita]:
        """Obtiene las próximas citas para una fecha específica (solo Pendientes y Confirmadas)."""
        inicio_dia = datetime.combine(fecha.date(), datetime.min.time())
        fin_dia = inicio_dia + timedelta(days=1)
        return (
            self._db.query(Cita)
            .filter(
                Cita.fecha_hora >= inicio_dia,
                Cita.fecha_hora < fin_dia,
                Cita.estado_cita.in_([EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]),
            )
            .order_by(Cita.fecha_hora.asc())
            .all()
        )

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
                func.coalesce(func.sum(Servicio.tiempo_estimado), 0).label(
                    "tiempo_total"
                ),
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
