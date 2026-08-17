from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import Optional
from src.config.notificacion import emailConfig

# Configuración de conexión para envío de correos
mail_conf = ConnectionConfig(
    MAIL_USERNAME=emailConfig.MAIL_USERNAME,
    MAIL_PASSWORD=emailConfig.MAIL_PASSWORD,
    MAIL_FROM=emailConfig.MAIL_FROM,
    MAIL_PORT=emailConfig.MAIL_PORT,
    MAIL_SERVER=emailConfig.MAIL_SERVER,
    MAIL_STARTTLS=emailConfig.MAIL_STARTTLS,
    MAIL_SSL_TLS=emailConfig.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fm = FastMail(mail_conf)
scheduler = AsyncIOScheduler()


def start_scheduler():
    """Inicia el scheduler de notificaciones programadas."""
    if not scheduler.running:
        scheduler.start()


async def send_notification(
    # parametros 
    subject: str,      
    recipients: list[str],
    body: str,
    subtype: str = "plain"
) -> bool:
    """
    Función global para enviar notificaciones por correo.
    - subject: asunto del correo
    - recipients: lista de destinatarios
    - body: contenido del mensaje
    - subtype: "plain" o "html"
    """

    try:
        message = MessageSchema(
            subject=subject,
            recipients=recipients, # type: ignore
            body=body,
            subtype=subtype # type: ignore
        )


        await fm.send_message(message)
        return True

    except Exception as e:
        print(f"[ERROR] Falló el envío de correo a {recipients}: {e}")
        return False
    
# programacion de envios de correos 
def schedule_notification(
    subject: str,
    recipients: list[str],
    body: str,
    run_date,  # fecha/hora de ejecución
    job_id: Optional[str] = None, # identificador (string para APScheduler)
    subtype: str = "plain"):
    try: 
        scheduler.add_job(
            send_notification,
            "date", # tipo de programación: ejecución única en fecha/hora
            run_date=run_date,
            args=[subject, recipients, body, subtype],
            id= job_id,
            replace_existing=True    # si ya existe, lo reemplaza
        )
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo programar el correo para {recipients}: {e}")
        return False