"""
Servicio base genérico para toda la lógica de negocio.
---------------------------------------------------
Proporciona métodos comunes que todos los servicios pueden reutilizar,
como la gestión de errores, validaciones genéricas y helpers de respuesta.
"""

from typing import TypeVar, Generic, Optional, List
from sqlalchemy.orm import Session

from src.repositories.base_repository import Repository


T = TypeVar("T")


class BaseService(Generic[T]):

    def __init__(self, db: Session, repository: Repository[T]):
        """
        Inicializa el servicio base.

        :param db: Sesión de SQLAlchemy (inyectada por FastAPI).
        :param repository: Instancia del repositorio específico del dominio.
        """
        self._db = db
        self._repo = repository

    # ---------------------------------------------------------------
    #  Métodos CRUD genéricos (reutilizables por todos los servicios)
    # ---------------------------------------------------------------

    def listar_todos(self) -> List[T]:
        """Devuelve todos los registros del modelo."""
        return self._repo.get_all()

    def obtener_por_id(self, id_: int) -> Optional[T]:
        """Obtiene un registro por su ID."""
        return self._repo.get_by_id(id_)

    def crear(self, datos: T) -> T:
        """Crea un nuevo registro."""
        return self._repo.create(datos)

    def actualizar(self, id_: int, datos: T) -> Optional[T]:
        """Actualiza un registro existente."""
        return self._repo.update(datos)

    def eliminar(self, id_: int) -> bool:
        """Elimina un registro por ID."""
        obj = self._repo.get_by_id(id_)
        if obj:
            self._repo.delete(obj)
            return True
        return False

    def existe(self, id_: int) -> bool:
        """Verifica si un registro existe."""
        return self._repo.exists(id_)

    # ---------------------------------------------------------------
    #  Validaciones comunes (reutilizables por todos los servicios)
    # ---------------------------------------------------------------

    def validar_no_nulo(self, valor: any, nombre: str) -> None:
        """Valida que un valor no sea None."""
        if valor is None:
            raise ValueError(f"El campo '{nombre}' no puede ser nulo")

    def validar_no_vacio(self, valor: str, nombre: str) -> None:
        """Valida que una cadena no esté vacía."""
        if not valor or not valor.strip():
            raise ValueError(f"El campo '{nombre}' no puede estar vacío")

    def validar_positivo(self, valor: float, nombre: str) -> None:
        """Valida que un número sea positivo."""
        if valor <= 0:
            raise ValueError(
                f"El campo '{nombre}' debe ser mayor a 0"
            )

    def validar_mayor_que(self, valor: int, minimo: int, nombre: str) -> None:
        """Valida que un valor sea mayor o igual a un mínimo."""
        if valor < minimo:
            raise ValueError(
                f"El campo '{nombre}' debe ser mayor o igual a {minimo}"
            )
