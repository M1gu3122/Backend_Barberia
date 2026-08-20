"""
Repositorio para la tabla Notificacion.
Gestiona las notificaciones enviadas a usuarios (clientes o empleados).
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.notificacion_model import Notificacion, TipoNotificacion, EstadoNotificacion
from src.schemas.notificacion_schema import NotificacionCreate, NotificacionUpdate
from src.core.timezone import a_bd, ahora_bogota


class NotificacionRepository:
    """Repositorio para operaciones CRUD de Notificaciones."""

    def __init__(self, db: Session):
        self._db = db

    # =========================================================
    # Métodos CRUD básicos
    # =========================================================

    def get_by_id(self, id_: int) -> Optional[Notificacion]:
        """Obtiene una notificación por su ID."""
        return self._db.get(Notificacion, id_)

    def get_all(self) -> List[Notificacion]:
        """Obtiene todas las notificaciones."""
        return self._db.query(Notificacion).all()

    def create(self, datos: NotificacionCreate) -> Notificacion:
        """Crea una nueva notificación."""
        notificacion = Notificacion(**datos.model_dump())
        # Asignar fecha de envío explícita (hora local de Colombia naive)
        notificacion.fecha_envio = a_bd(ahora_bogota())
        self._db.add(notificacion)
        self._db.commit()
        self._db.refresh(notificacion)
        return notificacion

    def update(self, id_: int, datos: NotificacionUpdate) -> Optional[Notificacion]:
        """Actualiza una notificación existente."""
        notificacion = self._db.get(Notificacion, id_)
        if not notificacion:
            return None
        update_data = datos.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(notificacion, key, value)
        self._db.commit()
        self._db.refresh(notificacion)
        return notificacion

    def delete(self, id_: int) -> bool:
        """Elimina una notificación por ID."""
        notificacion = self._db.get(Notificacion, id_)
        if not notificacion:
            return False
        self._db.delete(notificacion)
        self._db.commit()
        return True

    # =========================================================
    # Métodos personalizados
    # =========================================================

    def get_by_usuario(self, id_usuario: int) -> List[Notificacion]:
        """Obtiene todas las notificaciones de un usuario."""
        return (
            self._db.query(Notificacion)
            .filter(Notificacion.id_usuario == id_usuario)
            .order_by(Notificacion.fecha_envio.desc())
            .all()
        )

    def get_by_cita(self, id_cita: int) -> List[Notificacion]:
        """Obtiene todas las notificaciones asociadas a una cita."""
        return (
            self._db.query(Notificacion)
            .filter(Notificacion.id_cita == id_cita)
            .all()
        )

    def get_por_estado(self, estado: EstadoNotificacion) -> List[Notificacion]:
        """Obtiene notificaciones filtradas por estado."""
        return (
            self._db.query(Notificacion)
            .filter(Notificacion.estado == estado)
            .all()
        )

    def get_por_tipo(self, tipo: TipoNotificacion) -> List[Notificacion]:
        """Obtiene notificaciones filtradas por tipo."""
        return (
            self._db.query(Notificacion)
            .filter(Notificacion.tipo == tipo)
            .all()
        )

    def marcar_leida(self, id_: int) -> Optional[Notificacion]:
        """Marca una notificación como leída."""
        notificacion = self._db.get(Notificacion, id_)
        if not notificacion:
            return None
        notificacion.estado = EstadoNotificacion.LEIDA
        self._db.commit()
        self._db.refresh(notificacion)
        return notificacion

    def marcar_no_leida(self, id_: int) -> Optional[Notificacion]:
        """Marca una notificación como no leída."""
        notificacion = self._db.get(Notificacion, id_)
        if not notificacion:
            return None
        notificacion.estado = EstadoNotificacion.NO_LEIDA
        self._db.commit()
        self._db.refresh(notificacion)
        return notificacion

    def exists(self, id_: int) -> bool:
        """Verifica si una notificación existe."""
        return self.get_by_id(id_) is not None