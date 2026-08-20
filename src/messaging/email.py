from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
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

# Configuración de plantillas Jinja2
TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=True,
)


def render_template(template_name: str, **context) -> str:
    """Renderiza una plantilla HTML con el contexto dado."""
    template = jinja_env.get_template(template_name)
    return template.render(**context)


async def send_template_email(
    subject: str,
    recipients: list[str],
    template_name: str,
    context: dict,
) -> bool:
    """
    Envía un correo usando una plantilla HTML.
    - subject: asunto del correo
    - recipients: lista de destinatarios
    - template_name: nombre del archivo en templates/email/ (ej: "reset_password.html")
    - context: dict con variables para la plantilla
    """
    try:
        html_body = render_template(template_name, **context)
        message = MessageSchema(
            subject=subject,
            recipients=recipients,  # type: ignore
            body=html_body,
            subtype="html"
        )
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"[ERROR] Falló envío template {template_name} a {recipients}: {e}")
        return False


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


def start_auto_completar_citas():
    """
    Inicia el job periódico para auto-completar citas vencidas.
    Se ejecuta cada 5 minutos.
    """
    from src.services.cita_service import CitaService
    from src.config.database import SessionLocal

    def job():
        db = SessionLocal()
        try:
            service = CitaService(db)
            count = service.auto_completar_citas_vencidas()
            if count > 0:
                print(f"[AUTO-COMPLETAR] {count} citas actualizadas a COMPLETADA")
        except Exception as e:
            print(f"[ERROR] Error en auto_completar_citas_vencidas: {e}")
        finally:
            db.close()

    if not scheduler.running:
        scheduler.start()
    
    # Agregar job cada 5 minutos
    scheduler.add_job(
        job,
        "interval",
        minutes=5,
        id="auto_completar_citas",
        replace_existing=True
    )
    print("[SCHEDULER] Job auto_completar_citas iniciado (cada 5 min)")