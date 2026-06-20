from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Optional

def calculate_age(dob: date | str | None) -> Optional[int]:
    """Calculate age from date_of_birth in a birthday-aware manner."""
    if not dob:
        return None
    if isinstance(dob, str):
        try:
            # Handle ISO timestamp or just date strings
            dob = date.fromisoformat(dob.split("T")[0])
        except ValueError:
            return None
    elif isinstance(dob, datetime):
        dob = dob.date()
    
    today = date.today()
    try:
        birthday_this_year = dob.replace(year=today.year)
    except ValueError:
        # Handle leap years/Feb 29
        birthday_this_year = dob.replace(year=today.year, day=dob.day - 1)
        
    age = today.year - dob.year
    if today < birthday_this_year:
        age -= 1
    return age


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
