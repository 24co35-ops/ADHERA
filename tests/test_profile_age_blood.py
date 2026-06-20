import pytest
from datetime import date, datetime
from app.core.utils import calculate_age
from app.profile.schemas import ProfileUpdate
from pydantic import ValidationError

def test_calculate_age_basic():
    # Birthday has occurred this year
    dob = date(2000, 1, 1)
    # Patch date.today to always be 2026-06-20 (since today's date in test environment is 2026-06-20)
    # The actual code calls date.today() which will evaluate against current system time (2026-06-20).
    # Since 2000-01-01 is before June 20, age is 2026 - 2000 = 26.
    assert calculate_age(dob) == 26

def test_calculate_age_birthday_not_occurred():
    # Birthday has not occurred yet this year (2026-12-31)
    dob = date(2000, 12, 31)
    assert calculate_age(dob) == 25

def test_calculate_age_leap_year():
    # Leap year birthday Feb 29
    dob = date(2000, 2, 29)
    assert calculate_age(dob) == 26

def test_calculate_age_string():
    # Date string format
    assert calculate_age("2000-01-01") == 26
    # ISO datetime string
    assert calculate_age("2000-12-31T08:00:00Z") == 25
    # Invalid string format
    assert calculate_age("invalid-date") is None

def test_calculate_age_none():
    assert calculate_age(None) is None

def test_profile_update_schema_validation():
    # Valid blood groups
    for bg in ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', None]:
        update = ProfileUpdate(blood_group=bg)
        assert update.blood_group == bg

    # Invalid blood groups
    for bg in ['C+', 'a+', 'A', '', 'O/+', 'AB++']:
        with pytest.raises(ValidationError):
            ProfileUpdate(blood_group=bg)

def test_profile_update_optional_fields():
    # Confirm fields are not required and can be omitted
    update = ProfileUpdate()
    assert update.blood_group is None
    assert update.full_name is None
