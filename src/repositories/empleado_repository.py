"""
Repositorio para la tabla Empleado.
Contiene métodos para gestionar empleados (barberos, recepcionistas, administradores).
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.usuario_model import Usuario
from src.models.empleado_model import Empleado, TipoEmpleado, EstadoEmpleado
from src.schemas.empleado_schema import EmpleadoCreate, EmpleadoUpdate
from src.repositories.base_repository import Repository


class EmpleadoRepository(Repository[Empleado]):
    """Repositorio para operaciones CRUD de Empleados."""

    def __init__(self, db: Session):
        super().__init__(Empleado, db)

    # =========================================================
    # Métodos CRUD básicos (heredados de base)
    # =========================================================

    def get_by_id(self, id_: int) -> Optional[Empleado]:
        """Obtiene un empleado por su ID (que es el ID del usuario asociado)."""
        return self._session.query(self._model).filter(self._model.id_usuario == id_).first()

    def get_all(self) -> List[Empleado]:
        """Obtiene todos los empleados."""
        return self._session.query(self._model).all()

    def create(self, obj: Empleado) -> Empleado:
        """Crea un nuevo empleado."""
        self._session.add(obj)
        self._session.commit()
        self._session.refresh(obj)
        return obj

    def update(self, obj: Empleado) -> Empleado:
        """Actualiza un empleado existente."""
        self._session.add(obj)
        self._session.commit()
        self._session.refresh(obj)
        return obj

    def delete(self, obj: Empleado):
        """Elimina un empleado."""
        self._session.delete(obj)
        self._session.commit()

    # =========================================================
    # Métodos personalizados
    # =========================================================

    def get_by_tipo(self, tipo: str) -> List[Empleado]:
        """Obtiene empleados por tipo (Barbero, Recepcionista, Administrador)."""
        return self._session.query(self._model).filter(self._model.tipo_empleado == tipo).all()

    def get_barberos(self) -> List[Empleado]:
        """Obtiene solo los barberos activos."""
        return self._session.query(self._model).filter(
            self._model.tipo_empleado == TipoEmpleado.BARBERO,
            self._model.estado == EstadoEmpleado.ACTIVO
        ).all()
        
    def get_empleado(self, id_empleado: int, tipo: str) -> Optional[Empleado]:
        return self._session.query(self._model).filter(self._model.id_usuario == id_empleado, self._model.tipo_empleado == tipo).first()
        

    def get_by_barberia(self, id_barberia: int) -> List[Empleado]:
        """Obtiene empleados asociados a una barbería específica."""
        return self._session.query(self._model).filter(self._model.id_barberia == id_barberia).all()

    def exists_usuario(self, id_usuario: int) -> bool:
        """Verifica si un usuario ya es empleado"""
        return self._session.query(self._model).filter(self._model.id_usuario == id_usuario).first() is not None

    def get_empleado_por_usuario(self, id_usuario: int) -> Optional[Empleado]:
        """Obtiene un empleado por ID de usuario"""
        return self._session.query(self._model).filter(self._model.id_usuario == id_usuario).first()
