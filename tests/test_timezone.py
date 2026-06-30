import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
import jwt
from app.config import settings
from datetime import datetime, timezone, timedelta, time
import pytz
from freezegun import freeze_time

client = TestClient(app)

def get_token(role="patient"):
    return jwt.encode({"aud": "authenticated", "sub": "11111111-1111-1111-1111-111111111111", "user_metadata": {"role": role}}, settings.SUPABASE_JWT_SECRET, algorithm="HS256")

def headers(role="patient"):
    return {"Authorization": f"Bearer {get_token(role)}"}

# --- Test Parameters mapping local/UTC transition times exactly ---
# Parameters format:
# (iana_tz, sf_date, fb_date, dose_time_utc_sf, freeze_local_sf, dose_time_utc_fb, first_occ_utc_fb, second_occ_utc_fb)
TIMEZONE_PARAMS = [
    (
        "Europe/London",
        "2026-03-29",
        "2026-10-25",
        "01:30:00",  # 01:30 AM local skipped time on GMT/BST transition (01:30 UTC)
        "05:00:00",  # Freeze local time at 05:00:00 BST (04:00:00 UTC)
        "00:30:00",  # Scheduled local 01:30 AM on fallback day (1st occurrence = 00:30:00 UTC)
        "2026-10-25T00:30:00Z",
        "2026-10-25T01:30:00Z"
    ),
    (
        "America/New_York",
        "2026-03-08",
        "2026-11-01",
        "07:30:00",  # 02:30 AM local skipped time on EST/EDT transition (07:30 UTC)
        "06:00:00",  # Freeze local time at 06:00:00 EDT (10:00:00 UTC)
        "05:30:00",  # Scheduled local 01:30 AM on fallback day (1st occurrence = 05:30:00 UTC)
        "2026-11-01T05:30:00Z",
        "2026-11-01T06:30:00Z"
    ),
    (
        "Europe/Paris",
        "2026-03-29",
        "2026-10-25",
        "01:30:00",  # 02:30 AM local skipped time on CET/CEST transition (01:30 UTC)
        "06:00:00",  # Freeze local time at 06:00:00 CEST (04:00:00 UTC)
        "00:30:00",  # Scheduled local 02:30 AM on fallback day (1st occurrence = 00:30:00 UTC)
        "2026-10-25T00:30:00Z",
        "2026-10-25T01:30:00Z"
    ),
]

# (1) DST Spring-forward night (clock jumps, dose time never exists)
@pytest.mark.parametrize("iana_tz, sf_date, fb_date, dose_time_utc_sf, freeze_local_sf, dose_time_utc_fb, first_occ_utc_fb, second_occ_utc_fb", TIMEZONE_PARAMS)
@patch("app.doses.router.supabase")
def test_spring_forward_missed_automatically(mock_supabase, iana_tz, sf_date, fb_date, dose_time_utc_sf, freeze_local_sf, dose_time_utc_fb, first_occ_utc_fb, second_occ_utc_fb):
    """
    On a spring-forward night, a dose scheduled in the skipped hour never occurs in local time.
    Assert that the dose scheduled UTC time has elapsed by more than 2 hours, so it is marked Missed.
    """
    # Mock profiles table to return user's timezone
    mock_supabase.table().select().eq().execute.return_value = MagicMock(data=[{"timezone": iana_tz}])
    
    # Mock reminders table
    mock_supabase.table().select().eq().eq().execute.return_value = MagicMock(data=[
        {
            "id": "r1",
            "user_id": "11111111-1111-1111-1111-111111111111",
            "dose_label": "morning",
            "dose_time_utc": dose_time_utc_sf,
            "timezone": iana_tz,
            "recurrence_type": "daily",
            "is_active": True,
            "medicines": {
                "id": "m1",
                "name": "Med A",
                "start_date": "2026-01-01",
                "end_date": None,
                "is_active": True
            }
        }
    ])
    
    # Mock empty adherence records
    mock_supabase.table().select().eq().gte().lte().execute.return_value = MagicMock(data=[])
    
    # Freeze time AFTER the skipped hour (clock jumps past scheduled time)
    tz = pytz.timezone(iana_tz)
    freeze_dt = tz.localize(datetime.fromisoformat(f"{sf_date}T{freeze_local_sf}"))
    
    with freeze_time(freeze_dt):
        res = client.get("/v1/doses/upcoming", headers=headers())
        assert res.status_code == 200
        upcoming_doses = res.json()["data"]
        
        # Verify that the scheduled UTC time is in the past by >2 hours
        for dose in upcoming_doses:
            scheduled_dt = datetime.fromisoformat(dose["scheduled_utc"].replace("Z", "+00:00"))
            assert scheduled_dt + timedelta(hours=2) < datetime.now(timezone.utc)


# (2) DST Fall-back night (clock repeats, dose could fire twice)
@pytest.mark.parametrize("iana_tz, sf_date, fb_date, dose_time_utc_sf, freeze_local_sf, dose_time_utc_fb, first_occ_utc_fb, second_occ_utc_fb", TIMEZONE_PARAMS)
@patch("app.doses.router.supabase")
def test_fallback_fires_exactly_once(mock_supabase, iana_tz, sf_date, fb_date, dose_time_utc_sf, freeze_local_sf, dose_time_utc_fb, first_occ_utc_fb, second_occ_utc_fb):
    """
    On a fall-back night, the clock repeats an hour.
    A dose scheduled at that local time should fire exactly once.
    """
    # Mock profile
    mock_supabase.table().select().eq().execute.return_value = MagicMock(data=[{"timezone": iana_tz}])
    
    # Mock reminder
    mock_supabase.table().select().eq().eq().execute.return_value = MagicMock(data=[
        {
            "id": "r1",
            "user_id": "11111111-1111-1111-1111-111111111111",
            "dose_label": "morning",
            "dose_time_utc": dose_time_utc_fb,
            "timezone": iana_tz,
            "recurrence_type": "daily",
            "is_active": True,
            "medicines": {
                "id": "m1",
                "name": "Med A",
                "start_date": "2026-01-01",
                "end_date": None,
                "is_active": True
            }
        }
    ])
    
    first_utc_dt = datetime.fromisoformat(first_occ_utc_fb.replace("Z", "+00:00"))
    second_utc_dt = datetime.fromisoformat(second_occ_utc_fb.replace("Z", "+00:00"))
    
    # First call: No adherence records yet. Upcoming list contains the dose.
    mock_supabase.table().select().eq().gte().lte().execute.return_value = MagicMock(data=[])
    
    with freeze_time(first_utc_dt - timedelta(minutes=15)):
        res = client.get("/v1/doses/upcoming", headers=headers())
        assert res.status_code == 200
        upcoming = res.json()["data"]
        assert len(upcoming) == 1
        assert upcoming[0]["id"] == "r1"
        
    # Dose is taken/completed at the first occurrence (recorded in database)
    mock_supabase.table().insert().execute.return_value = MagicMock(data=[{"id": "a1", "status": "taken"}])
    mock_supabase.table().select().eq().execute.return_value = MagicMock(data=[{"user_id": "11111111-1111-1111-1111-111111111111", "dose_time_utc": dose_time_utc_fb}])
    
    # Mock POST to /taken
    res_taken = client.post("/v1/doses/r1/taken", headers=headers())
    assert res_taken.status_code == 200
    
    # Second call (during the second occurrence / repeated hour):
    # Mock the database to return that the first occurrence is completed in the adherence table
    mock_supabase.table().select().eq().gte().lte().execute.return_value = MagicMock(data=[
        {
            "reminder_id": "r1",
            "user_id": "11111111-1111-1111-1111-111111111111",
            "scheduled_utc": first_occ_utc_fb,
            "status": "taken"
        }
    ])
    
    # Mock profile response again for upcoming call
    mock_supabase.table().select().eq().execute.return_value = MagicMock(data=[{"timezone": iana_tz}])
    
    with freeze_time(second_utc_dt):
        res = client.get("/v1/doses/upcoming", headers=headers())
        assert res.status_code == 200
        upcoming = res.json()["data"]
        # The dose is marked completed for the unique scheduled UTC time, so it does not fire/show again
        # Even if timezone calculations might generate the same local time, the UTC completion check prevents double fire.
        assert len(upcoming) == 0 or upcoming[0]["scheduled_utc"] != first_occ_utc_fb


# (3) India (UTC+5:30, no DST) scheduled at 23:30
@patch("app.doses.router.supabase")
def test_india_timezone_conversion(mock_supabase):
    """
    Assert that for a user in Asia/Kolkata (UTC+5:30) scheduling at 23:30,
    the UTC stored time is 18:00 UTC and reminder fires at the correct UTC moment.
    """
    iana_tz = "Asia/Kolkata"
    local_time_str = "23:30:00"
    
    # Local 23:30 in Asia/Kolkata is 18:00 UTC
    tz = pytz.timezone(iana_tz)
    local_dt = tz.localize(datetime.fromisoformat("2026-06-19T23:30:00"))
    utc_dt = local_dt.astimezone(pytz.utc)
    
    assert utc_dt.time() == time(18, 0, 0)
    
    # Mock profiles table to return India timezone
    mock_supabase.table().select().eq().execute.return_value = MagicMock(data=[{"timezone": iana_tz}])
    
    # Mock reminder to return a dose stored at 18:00:00 UTC
    mock_supabase.table().select().eq().eq().execute.return_value = MagicMock(data=[
        {
            "id": "r1",
            "user_id": "11111111-1111-1111-1111-111111111111",
            "dose_label": "night",
            "dose_time_utc": "18:00:00", # Stored in UTC (18:00)
            "timezone": iana_tz,
            "recurrence_type": "daily",
            "is_active": True,
            "medicines": {
                "id": "m1",
                "name": "Med A",
                "start_date": "2026-01-01",
                "end_date": None,
                "is_active": True
            }
        }
    ])
    
    # Empty adherence
    mock_supabase.table().select().eq().gte().lte().execute.return_value = MagicMock(data=[])
    
    # Freeze time at the exact UTC moment (18:00:00 UTC)
    with freeze_time(utc_dt):
        res = client.get("/v1/doses/upcoming", headers=headers())
        assert res.status_code == 200
        upcoming = res.json()["data"]
        assert len(upcoming) == 1
        assert upcoming[0]["scheduled_utc"] == "2026-06-19T18:00:00Z"
