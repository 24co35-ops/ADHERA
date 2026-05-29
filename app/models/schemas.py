from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import date


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters")
    full_name: str = Field(min_length=1, max_length=200)
    role: str = Field(pattern="^(patient|provider)$")
    date_of_birth: Optional[date] = None
    contact_number: Optional[str] = Field(default=None, max_length=30)
    timezone: str = Field(default="UTC", max_length=60)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    date_of_birth: Optional[date] = None
    contact_number: Optional[str] = Field(default=None, max_length=30)
    timezone: Optional[str] = Field(default=None, max_length=60)


class EmergencyContactBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    relationship: str = Field(min_length=1, max_length=100)
    email: EmailStr


class EmergencyContact(EmergencyContactBase):
    id: str
    user_id: str
    verified: bool


# ---------------------------------------------------------------------------
# Medicines
# ---------------------------------------------------------------------------

class MedicineBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    dosage_amount: float = Field(gt=0)
    dosage_unit: str = Field(pattern="^(mg|ml|units)$")
    route: str = Field(pattern="^(oral|topical|injection|inhaled|other)$")
    frequency_type: str = Field(pattern="^(daily|weekday|alternate|prn)$")
    recurrence_params: Optional[dict] = None
    start_date: date
    end_date: Optional[date] = None
    instructions: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: Optional[date], info) -> Optional[date]:
        if v is not None and "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be on or after start_date")
        return v


class MedicineCreate(MedicineBase):
    pass


class MedicineUpdate(BaseModel):
    """All fields optional for PATCH requests."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    dosage_amount: Optional[float] = Field(default=None, gt=0)
    dosage_unit: Optional[str] = Field(default=None, pattern="^(mg|ml|units)$")
    route: Optional[str] = Field(default=None, pattern="^(oral|topical|injection|inhaled|other)$")
    frequency_type: Optional[str] = Field(default=None, pattern="^(daily|weekday|alternate|prn)$")
    recurrence_params: Optional[dict] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    instructions: Optional[str] = Field(default=None, max_length=1000)


class Medicine(MedicineBase):
    id: str
    user_id: str
    is_active: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------

class ReminderBase(BaseModel):
    dose_label: str = Field(pattern="^(morning|afternoon|evening|night)$")
    dose_time_utc: str = Field(pattern=r"^\d{2}:\d{2}:\d{2}$", description="HH:MM:SS in UTC")
    timezone: str = Field(max_length=60)
    recurrence_type: str
    recurrence_params: Optional[dict] = None


class ReminderCreate(ReminderBase):
    medicine_id: str


class Reminder(ReminderBase):
    id: str
    medicine_id: str
    user_id: str
    is_active: bool
    warning: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Doses
# ---------------------------------------------------------------------------

class DoseStatus(BaseModel):
    status: str = Field(pattern="^(taken|missed|snoozed)$")
    scheduled_utc: str = Field(description="ISO 8601 datetime string")
    correction_note: Optional[str] = Field(default=None, max_length=500)


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

class FeedbackCreate(BaseModel):
    medicine_id: str
    description: str = Field(min_length=1, max_length=2000)
    severity: int = Field(ge=1, le=4)
    occurred_at: str = Field(description="ISO 8601 datetime string")


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------

class AssignmentCreate(BaseModel):
    patient_id: str
    provider_id: str
    note: Optional[str] = Field(default=None, max_length=500)
