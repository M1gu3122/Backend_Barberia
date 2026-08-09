"""
Servicio de negocio para la gestión de notificaciones.
---------------------------------------------------
Responsabilidades:
    - Validar que el usuario exista antes de crear una notificación.
    - Validar que la cita exista (si se proporciona).
    - Validar que el tipo de notificación sea uno de los permitidos.
    - Permitir marcar notificaciones como leídas/no leídas.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.notificacion_model import Notificacion, TipoNotificacion, EstadoNotificacion
from src.schemas.notificacion_schema import NotificacionCreate, NotificacionUpdate, NotificacionResponse
from src.repositories.notificacion_repository import NotificacionRepository
from src.repositories.usuario_repository import UsuarioRepository


class NotificacionService:
    """Servicio de negocio para notificaciones."""

    def __init__(self, db: Session):
        self._db = db
        self._repo = NotificacionRepository(db)
        self._usuario_repo = UsuarioRepository(db)

    # ---------------------------------------------------------------
    #  CREATE
    # ---------------------------------------------------------------
    def crear_notificacion(
        self, datos: NotificacionCreate
    ) -> NotificacionResponse:
        """
        Reglas de negocio:
        1. El usuario debe existir.
        2. Si se proporciona una cita, debe existir.
        3. El tipo de notificación debe ser válido.
        """
        # Regla 1: verificar usuario existe
        if not self._usuario_repo.exists(datos.id_usuario):
            raise ValueError(
                f"El usuario con ID {datos.id_usuario} no existe"
            )

        # Regla 2: si se especifica una cita, debe existir
        if datos.id_cita:
            from repositories.cita_repository import CitaRepository
            cita_repo = CitaRepository(self._db)
            if not cita_repo.get_by_id(datos.id_cita):
                raise ValueError(
                    f"La cita con ID {datos.id_cita} no existe"
                )

        notificacion_orm = self._repo.create(datos)
        return NotificacionResponse.model_validate(notificacion_orm)

    # ---------------------------------------------------------------
    #  READ
    # ---------------------------------------------------------------
    def listar_notificaciones(self) -> List[NotificacionResponse]:
        """Lista todas las notificaciones."""
        return [
            NotificacionResponse.model_validate(n)
            for n in self._repo.get_all()
        ]

    def obtener_notificacion_por_id(
        self, id_notificacion: int
    ) -> Optional[NotificacionResponse]:
        """Obtiene una notificación por su ID."""
        notificacion = self._repo.get_by_id(id_notificacion)
        if not notificacion:
            return None
        return NotificacionResponse.model_validate(notificacion)

    def listar_por_usuario(
        self, id_usuario: int
    ) -> List[NotificacionResponse]:
        """Lista notificaciones de un usuario específico."""
        from sqlalchemy import and_
        return [
            NotificacionResponse.model_validate(n)
            for n in self._repo.filter_by(id_usuario=id_usuario)
        ]

    def listar_por_cita(
        self, id_cita: int
    ) -> List[NotificacionResponse]:
        """Lista notificaciones asociadas a una cita específica."""
        return [
            NotificacionResponse.model_validate(n)
            for n in self._repo.filter_by(id_cita=id_cita)
        ]

    def listar_no_leidas(self) -> List[NotificacionResponse]:
        """Lista todas las notificaciones no leídas."""
        return [
            NotificacionResponse.model_validate(n)
            for n in self._repo.get_by_estado(EstadoNotificacion.NO_LEIDA)
        ]

    # ---------------------------------------------------------------
    #  UPDATE
    # ---------------------------------------------------------------
    def marcar_como_leida(
        self, id_notificacion: int
    ) -> Optional[NotificacionResponse]:
        """Marca una notificación como leída."""
        notificacion = self._repo.get_by_id(id_notificacion)
        if not notificacion:
            return None
        notificacion.estado = EstadoNotificacion.LEIDA
        self._db.commit()
        return NotificacionResponse.model_validate(notificacion)

    def marcar_como_no_leida(
        self, id_notificacion: int
    ) -> Optional[NotificacionResponse]:
        """Marca una notificación como no leída."""
        notificacion = self._repo.get_by_id(id_notificacion)
        if not notificacion:
            return None
        notificacion.estado = EstadoNotificacion.NO_LEIDA
        self._db.commit()
        return NotificacionResponse.model_validate(notificacion)

    def actualizar_notificacion(
        self, id_notificacion: int, datos: NotificacionUpdate
    ) -> Optional[NotificacionResponse]:
        """Actualiza una notificación existente."""
        notificacion = self._repo.get_by_id(id_notificacion)
        if not notificacion:
            return None

        notificacion_actualizada = self._repo.update(
            id_notificacion, datos
        )
        return NotificacionResponse.model_validate(notificacion_actualizada)

    # ---------------------------------------------------------------
    #  DELETE
    # ---------------------------------------------------------------
    def eliminar_notificacion(self, id_notificacion: int) -> bool:
        """Elimina una notificación. Devuelve True si se eliminó."""
        return self._repo.delete(id_notificacion)

    # ---------------------------------------------------------------
    #  HELPERS
    # ---------------------------------------------------------------
    def existe(self, id_notificacion: int) -> bool:
        """Verifica si una notificación existe."""
        return self._repo.exists(id_notificacion)