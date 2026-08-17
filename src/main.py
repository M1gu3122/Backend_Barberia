from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import auth_router, barberia_router, cita_router, empleado_router, notificacion_router, servicio_router, usuario_router,barbero_servicio_router, horario_barberia_router, servicio_adicional_router, fecha_no_laboral_router
from src.models import barberia_model, barbero_servicio_model, cita_model, cita_servicio_model, empleado_model, notificacion_model, servicio_barberia_model, servicio_model, usuario_model, horario_barberia_model, servicio_adicional_model, fecha_no_laboral_model
from src.config.database import Base, engine
from src.messaging.email import start_scheduler


# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Barbería API",
    description="API para gestión de una barbería",
    version="1.0.0"
)
origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#C:\Users\mglmo\Downloads\barberia_db.sql

# Incluir los routers
app.include_router(auth_router.router)
app.include_router(usuario_router.router)
app.include_router(cita_router.router)
app.include_router(empleado_router.router)
app.include_router(barberia_router.router)
app.include_router(servicio_router.router)
app.include_router(notificacion_router.router)
app.include_router(barbero_servicio_router.router)
app.include_router(horario_barberia_router.router)
app.include_router(servicio_adicional_router.router)
app.include_router(fecha_no_laboral_router.router)


@app.on_event("startup")
async def startup_event():
    """Inicia el scheduler de notificaciones al arrancar la aplicación."""
    start_scheduler()


@app.get("/")
async def root():
    """
    Endpoint raíz de la API.
    
    Retorna un mensaje de bienvenida para los usuarios que acceden a la API.
    
    Returns:
        dict: Mensaje de bienvenida
    """
    return {"message": "Hey, bienvenido a la API de Barbería"}
