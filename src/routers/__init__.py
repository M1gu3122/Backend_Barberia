"""
Routers package initialization
"""
from . import auth_router
from . import barberia_router
from . import cita_router
from . import empleado_router
from . import notificacion_router
from . import servicio_router
from . import usuario_router
from . import barbero_servicio_router
from . import horario_barberia_router
from . import servicio_adicional_router
from . import fecha_no_laboral_router
from . import dashboard_router

__all__ = [
    "auth_router",
    "barberia_router",
    "cita_router",
    "empleado_router",
    "notificacion_router",
    "servicio_router",
    "usuario_router",
    "barbero_servicio_router",
    "horario_barberia_router",
    "servicio_adicional_router",
    "fecha_no_laboral_router",
    "dashboard_router",
]