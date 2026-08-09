"""
Repositorio para la tabla Usuario.
Gestiona usuarios base (clientes y base para empleados).
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.models.usuario_model import Usuario
from src.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate

# add: Añadir el nuevo usuario a la sesión de base de datos (estado pending)
# commit: Confirmar los cambios en la base de datos (transacción SQL)
# refresh: Actualizar el objeto con los valores generados por la BD (como ID autoincremental)


#usuario = Usuario(**usuario_data.model_dump())
# Equivale a escribir:
#
# Usuario(
#     nombres=usuario_data.nombres,
#     apellidos=usuario_data.apellidos,
#     usuario=usuario_data.usuario,
#     contraseña=usuario_data.contraseña,
#     correo=usuario_data.correo,
#     telefono=usuario_data.telefono
# )
# Modelo esperado por SQLAlchemy

class UsuarioRepository:
    """Repositorio para operaciones CRUD de Usuarios."""

    def __init__(self, db: Session):
        self._db = db

    # =========================================================
    # Métodos CRUD básicos
    # =========================================================

    def get_by_id(self, id_: int) -> Optional[Usuario]:  # Puede devolver None
        """Obtiene un usuario por su ID."""
        return self._db.query(Usuario).filter(Usuario.id_usuario == id_).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """
        Obtiene todos los usuarios con paginación.

        Args:
            skip: Cantidad de registros a omitir.
            limit: Cantidad máxima de registros a devolver.
        """
        return (
            self._db.query(Usuario)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
    def get_by_correo(self, correo: str) -> Optional[Usuario]:
        """Obtiene un usuario por su correo electrónico."""
        return self._db.query(Usuario).filter(Usuario.correo == correo).first()

    def create(self, usuario_data: UsuarioCreate) -> Usuario:
        """Crea un nuevo usuario."""
        # Crear instancia de modelo Usuario usando los datos proporcionados
        # model_dump() convierte el objeto Pydantic a diccionario para su uso como kwargs
        usuario = Usuario(**usuario_data.model_dump())
        self._db.add(usuario)
        self._db.commit()
        self._db.refresh(usuario)
        return usuario

    def update(self, id_: int, updates: UsuarioUpdate) -> Optional[Usuario]:
        """Actualiza un usuario existente."""
        usuario = self._db.query(Usuario).filter(Usuario.id_usuario == id_).first()
        if not usuario:
            return None

        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(usuario, key, value)

        self._db.commit()
        self._db.refresh(usuario)
        return usuario

    def delete(self, id_: int) -> bool:
        """Elimina un usuario por ID."""
        usuario = self._db.query(Usuario).filter(Usuario.id_usuario == id_).first()
        if not usuario:
            return False

        self._db.delete(usuario)
        self._db.commit()
        return True

    # =========================================================
    # Métodos de búsqueda personalizados
    # =========================================================

    def get_by_usuario(self, usuario: str) -> Optional[Usuario]:
        """Busca un usuario por su nombre de usuario."""
        return self._db.query(Usuario).filter(Usuario.usuario == usuario).first()

    # def get_by_correo(self, correo: str) -> Optional[Usuario]:
    #     """Busca un usuario por su correo electrónico."""
    #     return self._db.query(Usuario).filter(Usuario.correo == correo).first()

    def search(self, termino: str) -> List[Usuario]:
        """Busca usuarios por nombre, apellido, usuario o correo."""
        return (
            self._db.query(Usuario)
            .filter(
                or_(
                    Usuario.nombres.ilike(f"%{termino}%"),
                    Usuario.apellidos.ilike(f"%{termino}%"),
                    Usuario.usuario.ilike(f"%{termino}%"),
                    Usuario.correo.ilike(f"%{termino}%"),
                )
            )
            .all()
        )

    def get_clientes(self) -> List[Usuario]:
        """Obtiene usuarios que NO son empleados (solo clientes)."""
        from src.models.empleado_model import Empleado

        return (
            self._db.query(Usuario)
            .outerjoin(Empleado, Usuario.id_usuario == Empleado.id_usuario)
            .filter(Empleado.id_usuario.is_(None))
            .all()
        )

    def exists(self, id_: int) -> bool:
        """Verifica si un usuario existe."""
        return self.get_by_id(id_) is not None

    def exists_usuario(self, usuario: str) -> bool:
        """Verifica si un nombre de usuario ya existe."""
        return self.get_by_usuario(usuario) is not None

    def exists_correo(self, correo: str) -> bool:
        """Verifica si un correo ya existe."""
        return self.get_by_correo(correo) is not None

    # =========================================================
    # Métodos de búsqueda avanzada
    # =========================================================

    # def get_by_tipo_usuario(self, tipo: str) -> List[Usuario]:
    #     """Obtiene usuarios por tipo (cliente, empleado, etc.)"""
    #     from src.models.empleado import Empleado
        
    #     if tipo == "cliente":
    #         # Clientes son usuarios que no son empleados
    #         return self.get_clientes()
    #     elif tipo == "empleado":
    #         # Empleados son usuarios con perfil en la tabla Empleado
    #         return (
    #             self._db.query(Usuario)
    #             .join(Empleado, Usuario.id_usuario == Empleado.id_usuario)
    #             .all()
    #         )
    #     else:
    #         return []

    def get_usuarios_por_rango_fecha(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[Usuario]:
        """Obtiene usuarios creados en un rango de fechas"""
        # Asumiendo que tienes un campo de creación
        return self._db.query(Usuario).filter(
            Usuario.fecha_creacion >= fecha_inicio,
            Usuario.fecha_creacion <= fecha_fin
        ).all()


