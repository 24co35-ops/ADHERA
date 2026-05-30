from datetime import datetime
from zoneinfo import ZoneInfo

def format_utc_to_iana(dt: datetime | str | None, iana_tz: str) -> str | None:
    """Format a UTC datetime to a specific IANA timezone for display."""
    if not dt:
        return None
    if isinstance(dt, str):
        # Handle ISO strings
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            return dt
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        
    try:
        local_dt = dt.astimezone(ZoneInfo(iana_tz))
        return local_dt.isoformat()
    except Exception:
        return dt.isoformat()
