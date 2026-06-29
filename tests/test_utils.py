"""
Unit tests for app.core.utils — calculate_age and format_utc_to_iana.
"""
import pytest
from datetime import date, datetime
from app.core.utils import calculate_age, format_utc_to_iana


class TestCalculateAge:
    def test_none_returns_none(self):
        assert calculate_age(None) is None

    def test_date_object(self):
        dob = date(1990, 6, 15)
        result = calculate_age(dob)
        assert isinstance(result, int)
        assert result >= 34  # At least 34 years old

    def test_date_string(self):
        result = calculate_age("1990-06-15")
        assert isinstance(result, int)
        assert result >= 34

    def test_iso_timestamp_string(self):
        result = calculate_age("1990-06-15T00:00:00Z")
        assert isinstance(result, int)
        assert result >= 34

    def test_datetime_object(self):
        dob = datetime(1990, 6, 15)
        result = calculate_age(dob)
        assert isinstance(result, int)
        assert result >= 34

    def test_invalid_string_returns_none(self):
        assert calculate_age("not-a-date") is None

    def test_empty_string_returns_none(self):
        assert calculate_age("") is None

    def test_leap_day_dob(self):
        # Feb 29 DOB — should not raise
        result = calculate_age("2000-02-29")
        assert isinstance(result, int)

    def test_young_person(self):
        # Born this year — should be 0
        this_year = date.today().year
        dob = date(this_year, 1, 1)
        result = calculate_age(dob)
        assert result in (0, 1)  # 0 or 1 depending on whether birthday has passed

    def test_future_birthday_adjusts_age(self):
        # Someone born in December, current date is January
        # Age should be year_diff - 1
        dob = date(2000, 12, 31)
        today = date.today()
        result = calculate_age(dob)
        expected = today.year - 2000 - (1 if today < dob.replace(year=today.year) else 0)
        assert result == expected


class TestFormatUtcToIana:
    def test_none_returns_none(self):
        assert format_utc_to_iana(None, "Asia/Kolkata") is None

    def test_datetime_object_converts(self):
        dt = datetime(2024, 6, 15, 12, 0, 0)
        result = format_utc_to_iana(dt, "Asia/Kolkata")
        assert result is not None
        assert "2024" in result

    def test_iso_string_converts(self):
        result = format_utc_to_iana("2024-06-15T12:00:00Z", "Asia/Kolkata")
        assert result is not None
        assert "2024" in result

    def test_invalid_iso_returns_original(self):
        result = format_utc_to_iana("not-a-date", "Asia/Kolkata")
        assert result == "not-a-date"

    def test_invalid_timezone_falls_back(self):
        result = format_utc_to_iana("2024-06-15T12:00:00Z", "Invalid/Timezone")
        # Should not raise, returns isoformat of original
        assert result is not None

    def test_utc_timezone(self):
        result = format_utc_to_iana("2024-06-15T12:00:00Z", "UTC")
        assert "12:00" in result

    def test_aware_datetime_object(self):
        from zoneinfo import ZoneInfo
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        result = format_utc_to_iana(dt, "US/Eastern")
        assert result is not None
