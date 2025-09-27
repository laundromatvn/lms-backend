from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings


def get_tzinfo() -> ZoneInfo:
    return ZoneInfo(settings.TIMEZONE_NAME)


def iso_now_local() -> str:
    return datetime.now(get_tzinfo()).isoformat()
