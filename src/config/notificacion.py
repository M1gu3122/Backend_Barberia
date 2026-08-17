import os
from dotenv import load_dotenv

load_dotenv()


#obtiene datos del env y crea una clase global

# CONFIGURACION DE ENVIOS DE CORREOS 
class EmailConfig:
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "info.barberia.noreply@gmail.com")
    MAIL_PASSWORD=  os.getenv("MAIL_PASSWORD")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "info.barberia.noreply@gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME","Barberia")
    MAIL_STARTTLS: bool = os.getenv(" MAIL_STARTTLS", "True") == "True"
    MAIL_SSL_TLS: bool = os.getenv("MAIL_SSL_TLS", "False") == "True"
    
    
emailConfig = EmailConfig()