"""
Servicio de negocio para la gestión de empleados.
---------------------------------------------------
Responsabilidades:
    - Validar que el usuario no exista antes de crear un empleado.
    - Validar que el tipo de empleado sea válido.
    - Verificar que la fecha de contratación no sea futura.
    - Crear tanto el usuario como el empleado en una sola operación.
    - Listar empleados por tipo o por barbería.
"""

from typing import List, Optional
from datetime import date
from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.models.usuario_model import Usuario
from src.models.empleado_model import Empleado, TipoEmpleado, EstadoEmpleado
from src.schemas.empleado_schema import EmpleadoCreate, EmpleadoUpdate, EmpleadoResponse
from src.repositories.empleado_repository import EmpleadoRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.services.base_service import BaseService
from src.core.timezone import hoy_bogota


class EmpleadoService(BaseService[Empleado]):
    """Servicio de negocio para empleados."""

    def __init__(
        self,
        empleado_repo: EmpleadoRepository,
        usuario_repo: UsuarioRepository,
        db: Session,
    ):
        super().__init__(db, empleado_repo)
        self._empleado_repo = empleado_repo
        self._usuario_repo = usuario_repo
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # ---------------------------------------------------------------
    #  CREATE
    # ---------------------------------------------------------------
    # src/services/empleado_service.py
    def crear_empleado(self, datos: EmpleadoCreate) -> EmpleadoResponse:
        """
        Reglas de negocio:
        1. El usuario no debe existir previamente (evitar duplicados)
        2. El nombre de usuario debe ser único
        3. El correo debe ser único
        4. La fecha de contratación no puede ser futura
        5. El tipo de empleado debe ser válido
        """
        # Validar que el usuario no exista ya como empleado o cliente
        if self._empleado_repo.exists(datos.id_usuario):
            raise ValueError("Ya existe un usuario con ese ID")


        # Validar fecha de contratación
        if datos.fecha_contratacion > hoy_bogota():
            raise ValueError("La fecha de contratación no puede ser futura")

        # Validar tipo de empleado
        try:
            TipoEmpleado(datos.tipo_empleado)
        except ValueError:
            raise ValueError("Tipo de empleado inválido")

        # Crear el empleado (solo los campos de la tabla empleado)
        empleado = Empleado(
            id_usuario=datos.id_usuario,
            tipo_empleado=datos.tipo_empleado,
            estado="Activo",  # Estado por defecto
            fecha_contratacion=datos.fecha_contratacion,
            id_barberia=datos.id_barberia,
        )

        # Crear empleado en la base de datos
        empleado_creado = self._empleado_repo.create(empleado)

        return EmpleadoResponse.model_validate(empleado_creado)

    # def hash_contraseña(self, contraseña: str) -> str:
    #     """Hashea la contraseña usando bcrypt"""
    #     return self.pwd_context.hash(contraseña)

    # ---------------------------------------------------------------
    #  READ
    # ---------------------------------------------------------------
    def listar_empleados(self) -> List[EmpleadoResponse]:
        """Lista todos los empleados."""
        return [
            EmpleadoResponse.model_validate(e)
            for e in self._empleado_repo.get_all()
        ]

    def obtener_empleado_por_id(
        self, id_usuario: int
    ) -> Optional[EmpleadoResponse]:
        """Obtiene un empleado por su ID."""
        empleado = self._empleado_repo.get_by_id(id_usuario)
        if not empleado:
            return None
        return EmpleadoResponse.model_validate(empleado)

    def obtener_barberos(self) -> List[EmpleadoResponse]:
        """Obtiene solo los barberos activos."""
        return [
            EmpleadoResponse.model_validate(e)
            for e in self._empleado_repo.get_barberos()
        ]

    def obtener_por_barberia(
        self, id_barberia: int
    ) -> List[EmpleadoResponse]:
        """Obtiene empleados asociados a una barbería."""
        return [
            EmpleadoResponse.model_validate(e)
            for e in self._empleado_repo.get_by_barberia(id_barberia)
        ]

    def obtener_por_tipo(
        self, tipo: TipoEmpleado
    ) -> List[EmpleadoResponse]:
        """Obtiene empleados filtrados por tipo."""
        return [
            EmpleadoResponse.model_validate(e)
            for e in self._empleado_repo.get_by_tipo(tipo.value)
        ]

    # ---------------------------------------------------------------
    #  UPDATE
    # ---------------------------------------------------------------
    def actualizar_empleado(self, id_usuario: int, datos: EmpleadoUpdate) -> Optional[EmpleadoResponse]:
        empleado = self._repo.get_by_id(id_usuario)
        if not empleado:
            return None

        # Actualizar los campos del empleado
        # Se ignora id_usuario del payload: la identidad la da el path.
        update_data = datos.model_dump(exclude_unset=True)
        update_data.pop("id_usuario", None)
        for key, value in update_data.items():
            setattr(empleado, key, value)

        self._db.commit()
        self._db.refresh(empleado)
        return EmpleadoResponse.model_validate(empleado)


    # ---------------------------------------------------------------
    #  DELETE
    # ---------------------------------------------------------------
    def eliminar_empleado(self, id_usuario: int) -> bool:
        """Elimina un empleado"""
        # Solo eliminamos el empleado, no el usuario (puede seguir siendo cliente)
        empleado = self._empleado_repo.get_by_id(id_usuario)
        if empleado:
            self._empleado_repo.delete(empleado)
            return True
        return False

    # ---------------------------------------------------------------
    #  MÉTODOS ADICIONALES
    # ---------------------------------------------------------------
    def verificar_credenciales(self, nombre_usuario: str, contraseña: str) -> Optional[EmpleadoResponse]:
        """
        Verifica las credenciales de un empleado.
        Retorna el empleado si las credenciales son correctas, None en caso contrario.
        """
        usuario = self._usuario_repo.get_by_usuario(nombre_usuario)
        if not usuario:
            return None
            
        # Verificar contraseña
        if self.pwd_context.verify(contraseña, usuario.contraseña):
            # Obtener el empleado asociado
            empleado = self._empleado_repo.get_empleado_por_usuario(usuario.id_usuario)
            if empleado:
                return EmpleadoResponse.model_validate(empleado)
        return None

    def cambiar_estado(self, id_: int, nuevo_estado: EstadoEmpleado) -> Optional[Empleado]:
        empleado = self._empleado_repo.get_by_id(id_)
        if not empleado:
            return None
        empleado.estado = nuevo_estado
        self._db.commit()
        self._db.refresh(empleado)
        return empleado