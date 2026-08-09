from fastapi import FastAPI
from src.routers import barberia_router, cita_router, empleado_router, notificacion_router, servicio_router, usuario_router
from src.models import barberia_model, barbero_servicio_model, cita_model, cita_servicio_model, empleado_model, notificacion_model, servicio_barberia_model, servicio_model, usuario_model
from src.config.database import Base, engine


# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Barbería API",
    description="API para gestión de una barbería",
    version="1.0.0"
)
#C:\Users\mglmo\Downloads\barberia_db.sql

# Incluir los routers
app.include_router(usuario_router.router)
app.include_router(cita_router.router)
app.include_router(empleado_router.router)
app.include_router(barberia_router.router)
app.include_router(servicio_router.router)
app.include_router(notificacion_router.router)


@app.get("/")
async def root():
    """
    Endpoint raíz de la API.
    
    Retorna un mensaje de bienvenida para los usuarios que acceden a la API.
    
    Returns:
        dict: Mensaje de bienvenida
    """
    return {"message": "Hey, bienvenido a la API de Barbería"}
