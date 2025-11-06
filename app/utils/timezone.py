from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings


def get_tzinfo() -> ZoneInfo:
    return ZoneInfo(settings.TIMEZONE_NAME)


def iso_now_local() -> str:
    return datetime.now(get_tzinfo()).isoformat()


def to_utc(dt: datetime) -> datetime:
    """
    Convert a datetime to UTC.
    If the datetime is timezone-naive, assume it's in the local timezone (Vietnam).
    If the datetime is timezone-aware, convert it to UTC.
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # If timezone-naive, assume it's in Vietnam timezone
        local_tz = get_tzinfo()
        dt = dt.replace(tzinfo=local_tz)
    
    # Convert to UTC
    return dt.astimezone(timezone.utc)


def to_local(dt: datetime) -> datetime:
    """
    Convert a UTC datetime to local timezone (Vietnam).
    If the datetime is timezone-naive, assume it's already in UTC.
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # If timezone-naive, assume it's UTC
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to local timezone
    local_tz = get_tzinfo()
    return dt.astimezone(local_tz)
