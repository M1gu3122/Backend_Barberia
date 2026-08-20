"""
Zona horaria centralizada de la aplicación.

Regla del proyecto:
    Zona horaria de negocio : America/Bogota
    API (fecha-hora)        : ISO 8601 con offset -05:00
    MariaDB DATE/TIME       : sin zona horaria
    MariaDB DATETIME        : hora local de Colombia sin tzinfo
    JWT                     : UTC
"""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

BOGOTA_TZ: ZoneInfo = ZoneInfo("America/Bogota")
UTC = timezone.utc


def ahora_bogota() -> datetime:
    """Hora actual en America/Bogota (aware)."""
    return datetime.now(BOGOTA_TZ)


def hoy_bogota() -> date:
    """Fecha actual (solo date) en America/Bogota."""
    return ahora_bogota().date()


def a_bogota(dt: datetime) -> datetime:
    """Normaliza un datetime a America/Bogota (aware).

    - Si llega naive, se interpreta como hora local de Colombia.
    - Si llega aware, se convierte con astimezone().
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=BOGOTA_TZ)
    return dt.astimezone(BOGOTA_TZ)


def a_bd(dt: datetime) -> datetime:
    """Prepara un datetime para almacenarlo en MariaDB DATETIME.

    Convierte a America/Bogota y elimina el tzinfo.
    """
    return a_bogota(dt).replace(tzinfo=None)


def desde_bd(dt: datetime) -> datetime:
    """Interpreta un DATETIME naive de MariaDB como hora de Colombia (aware)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=BOGOTA_TZ)
    return dt.astimezone(BOGOTA_TZ)


def serializar_bogota(dt: datetime) -> datetime:
    """Normaliza un datetime para responder por API: aware en America/Bogota."""
    return a_bogota(dt)