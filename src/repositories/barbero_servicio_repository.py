# src/repositories/barbero_servicio.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import distinct, func

from src.models.barbero_servicio_model import BarberoServicio
from src.models.usuario_model import Usuario
from src.models.empleado_model import Empleado, TipoEmpleado, EstadoEmpleado
from src.models.servicio_model import Servicio, EstadoServicio
from src.schemas.barbero_servicio_schema import BarberoServicioCreate, BarberoServicioUpdate
from src.repositories.base_repository import Repository


class BarberoServicioRepository(Repository[BarberoServicio]):
    def __init__(self, db: Session):
        super().__init__(BarberoServicio, db)

    def get_by_barbero(self, id_usuario: int) -> List[BarberoServicio]:
        """Obtiene todos los servicios asociados a un barbero."""
        return self._session.query(BarberoServicio).filter(BarberoServicio.id_usuario == id_usuario).all()

    def get_by_servicio(self, id_servicio: int) -> List[BarberoServicio]:
        """Obtiene todos los barberos asociados a un servicio."""
        return self._session.query(BarberoServicio).filter(BarberoServicio.id_servicio == id_servicio).all()

    def get_by_barbero_and_servicio(self, id_usuario: int, id_servicio: int) -> Optional[BarberoServicio]:
        """Obtiene una relación específica por barbero y servicio."""
        return self._session.query(BarberoServicio).filter(
            BarberoServicio.id_usuario == id_usuario,
            BarberoServicio.id_servicio == id_servicio
        ).first()

    def create(self, data: BarberoServicioCreate) -> BarberoServicio:
        """Crea una nueva relación barbero-servicio."""
        barbero_servicio = BarberoServicio(**data.model_dump())
        self._session.add(barbero_servicio)
        self._session.commit()
        self._session.refresh(barbero_servicio)
        return barbero_servicio

    def delete_by_barbero_and_servicio(self, id_usuario: int, id_servicio: int) -> bool:
        """Elimina una relación específica."""
        barbero_servicio = self.get_by_barbero_and_servicio(id_usuario, id_servicio)
        if barbero_servicio:
            self._session.delete(barbero_servicio)
            self._session.commit()
            return True
        return False

    def get_barberos_con_todos_los_servicios(self, ids_servicio: List[int]) -> List[dict]:
        """Obtiene los barberos (empleados activos tipo 'Barbero') que pueden
        realizar TODOS los servicios indicados (corte principal + adicionales).

        Equivale a:
        SELECT u.id_usuario, u.nombres, u.apellidos
        FROM barbero_servicio bs
        INNER JOIN usuario u ON u.id_usuario = bs.id_usuario
        INNER JOIN empleado e ON e.id_usuario = bs.id_usuario
        INNER JOIN servicio s ON s.id_servicio = bs.id_servicio
        WHERE e.tipo_empleado = 'Barbero'
          AND e.estado = 'Activo'
          AND s.estado_servicio = 'Activo'
          AND bs.id_servicio IN (:ids)
        GROUP BY u.id_usuario, u.nombres, u.apellidos
        HAVING COUNT(DISTINCT bs.id_servicio) = :cantidad
        """
        if not ids_servicio:
            return []

        rows = (
            self._session.query(
                Usuario.id_usuario,
                Usuario.nombres,
                Usuario.apellidos,
            )
            .join(BarberoServicio, BarberoServicio.id_usuario == Usuario.id_usuario)
            .join(Empleado, Empleado.id_usuario == BarberoServicio.id_usuario)
            .join(Servicio, Servicio.id_servicio == BarberoServicio.id_servicio)
            .filter(
                Empleado.tipo_empleado == TipoEmpleado.BARBERO,
                Empleado.estado == EstadoEmpleado.ACTIVO,
                Servicio.estado_servicio == EstadoServicio.ACTIVO,
                BarberoServicio.id_servicio.in_(ids_servicio),
            )
            .group_by(Usuario.id_usuario, Usuario.nombres, Usuario.apellidos)
            .having(func.count(distinct(BarberoServicio.id_servicio)) == len(ids_servicio))
            .all()
        )

        return [
            {
                "id_usuario": id_usuario,
                "nombres": nombres,
                "apellidos": apellidos,
            }
            for id_usuario, nombres, apellidos in rows
        ]

    def puede_realizar_todos(self, id_usuario: int, ids_servicio: List[int]) -> bool:
        """Regla 9: verifica que un barbero tiene asociados TODOS los servicios
        indicados. Devuelve True solo si la cantidad de coincidencias
        (sin duplicados) es igual a la cantidad de servicios pedidos."""
        if not ids_servicio:
            return False

        count = (
            self._session.query(func.count(distinct(BarberoServicio.id_servicio)))
            .filter(
                BarberoServicio.id_usuario == id_usuario,
                BarberoServicio.id_servicio.in_(ids_servicio),
            )
            .scalar()
        )
        return count == len(ids_servicio)
