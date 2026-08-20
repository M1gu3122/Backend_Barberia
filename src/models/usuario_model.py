"""
Modelo de Usuario para la Barbería
Representa a cualquier persona del sistema (cliente o empleado).
"""

from enum import Enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum as SAEnum, DateTime
from sqlalchemy.orm import relationship
from src.config.database import Base


class EstadoUsuario(str, Enum):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"


class Usuario(Base):
    """
    Tabla 'usuario': Clientes, barberos, recepcionistas,
    Un usuario PUEDE tener un perfil de empleado (relación 1:1 opcional).
    """
    __tablename__ = "usuario"

    id_usuario = Column(Integer, primary_key=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    usuario = Column(String(50), nullable=False, unique=True)
    contraseña = Column(String(255), nullable=False)
    correo = Column(String(100), nullable=False, unique=True)
    telefono = Column(String(20))
    estado = Column(
        SAEnum(
            EstadoUsuario,
            values_callable=lambda enum_cls: [e.value for e in enum_cls]
        ),
        default=EstadoUsuario.ACTIVO,
        nullable=False,
    )
    reset_token = Column(String(255), nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)

    # --- Relaciones ---
    # Perfil de empleado (opcional: solo si el usuario es empleado)
    
    # Relación 1:1 con Empleado (opcional)
    empleado = relationship(
        "Empleado",
        back_populates="usuario",
        uselist=False,      # Relación 1:1 (no lista)
        cascade="all, delete-orphan"
    )

    # Relación 1:N con Citas
    citas = relationship(
        "Cita",
        back_populates="cliente",
        foreign_keys="Cita.id_cliente",
        cascade="all, delete-orphan"
    )
    
    # Relación 1:N con Notificaciones
    notificaciones = relationship(
        "Notificacion",
        back_populates="usuario",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Usuario(id={self.id_usuario}, "
            f"usuario='{self.usuario}', "
            f"nombre='{self.nombres} {self.apellidos}')>"
        )

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"

    @property
    def es_empleado(self) -> bool:
        """Verifica si este usuario tiene perfil de empleado"""
        return self.empleado is not None

    @property
    def tipo_usuario(self) -> str:
        """Obtiene el tipo de usuario (cliente, empleado o administrador)"""
        if self.es_empleado:
            return self.empleado.tipo_empleado
        return "Cliente"
