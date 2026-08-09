"""
Modelo de Empleado para la Barbería
Extiende la información del usuario con datos laborales.
Relación 1:1 con Usuarios (id_usuario es PK y FK a la vez).
"""



from enum import Enum
from sqlalchemy import Column, Integer, ForeignKey, Date,Enum as SAEnum
from sqlalchemy.orm import relationship
from src.config.database import Base

class TipoEmpleado(str, Enum):
    BARBERO = "Barbero"
    RECEPCIONISTA = "Recepcionista"
    ADMINISTRADOR = "Administrador"


class EstadoEmpleado(str, Enum):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"


class Empleado(Base):
    """
    Tabla 'empleado': Información laboral de los usuarios que trabajan en la barbería.
    Relación 1:1 con Usuarios (shared primary key).
    """

    __tablename__ = "empleado"

    # Shared Primary Key = Foreign Key a usuarios
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)

    tipo_empleado = Column(
        SAEnum(
            TipoEmpleado,
            values_callable=lambda enum_cls: [e.value for e in enum_cls]
        ),
        nullable=False
    )

    estado = Column(
        SAEnum(
            EstadoEmpleado,
            values_callable=lambda enum_cls: [e.value for e in enum_cls]
        ),
        default=EstadoEmpleado.ACTIVO,
        nullable=False
    )

    fecha_contratacion = Column(Date, nullable=False)

    id_barberia = Column(Integer, ForeignKey("barberia.id_barberia"), nullable=False)
     

    # --- Relaciones ---
      # ✅ Corregido
    usuario = relationship(
        "Usuario", back_populates="empleado", uselist=False
    )

    # ✅ Corregido
    citas = relationship(
        "Cita",
        back_populates="barbero",  
        foreign_keys="Cita.id_barbero",
        cascade="all, delete-orphan",
    )
    
    # ✅ Corregido
    barbero_servicios = relationship(
        "BarberoServicio",
        back_populates="barbero",
        cascade="all, delete-orphan",
    )
    
    # ✅ Corregido
    barberia = relationship("Barberia", back_populates="empleados")

    def __repr__(self) -> str:
        return (
            f"<Empleado(id_usuario={self.id_usuario}, "
            f"tipo='{self.tipo_empleado.value}', "
            f"estado='{self.estado.value}')>"
        )

    @property
    def es_barbero(self) -> bool:
        return self.tipo_empleado == TipoEmpleado.BARBERO

    @property
    def esta_activo(self) -> bool:
        return self.estado == EstadoEmpleado.ACTIVO

    @property
    def nombre_completo(self) -> str:
        """Acceso directo al nombre del usuario asociado"""
        return self.usuario.nombre_completo if self.usuario else "Sin usuario"

    @property
    def nombre_tipo(self) -> str:
        """Obtiene el nombre descriptivo del tipo de empleado"""
        return self.tipo_empleado.value

    @property
    def nombre_barberia(self) -> str:
        """Obtiene el nombre de la barbería donde trabaja"""
        return self.barberia.nombre_barberia if self.barberia else "Sin barbería"
