import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()


SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', 3306)}/{os.getenv('DB_NAME',
  'barberia_db')}"
)

# 2️⃣  Motor y sesión
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,  # True para ver el SQL en consola
    pool_pre_ping=True,
    pool_size=5,  # Tamaño de la pool
    max_overflow=10,  # Conexiones extra cuando la pool se agota
    pool_recycle=3600,  # Cierra conexiones idle > 1 h
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()  # Clase base para todos los modelos

# 3️⃣  Dependencia para FastAPI (puedes reutilizarla en routers)


def get_db():
    """Generador que entrega una sesión y la cierra al final.
    
    Esta función es utilizada como dependencia en los endpoints de FastAPI
    para proporcionar una sesión de base de datos única por solicitud.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
