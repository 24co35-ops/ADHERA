from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = Field(pattern="^(patient|provider)$")
    date_of_birth: Optional[date] = None
    contact_number: Optional[str] = None
    timezone: str = "UTC"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    contact_number: Optional[str] = None
    timezone: Optional[str] = None

class EmergencyContactBase(BaseModel):
    full_name: str
    relationship: str
    email: EmailStr

class EmergencyContact(EmergencyContactBase):
    id: str
    user_id: str
    verified: bool

# Medicines and Reminders
class MedicineBase(BaseModel):
    name: str
    dosage_amount: float
    dosage_unit: str = Field(pattern="^(mg|ml|units)$")
    route: str = Field(pattern="^(oral|topical|injection|inhaled|other)$")
    frequency_type: str = Field(pattern="^(daily|weekday|alternate|prn)$")
    recurrence_params: Optional[dict] = None
    start_date: date
    end_date: Optional[date] = None
    instructions: Optional[str] = None

class MedicineCreate(MedicineBase):
    pass

class Medicine(MedicineBase):
    id: str
    user_id: str
    is_active: bool

class ReminderBase(BaseModel):
    dose_label: str = Field(pattern="^(morning|afternoon|evening|night)$")
    dose_time_utc: str # HH:MM:SS
    timezone: str
    recurrence_type: str
    recurrence_params: Optional[dict] = None

class ReminderCreate(ReminderBase):
    medicine_id: str

class Reminder(ReminderBase):
    id: str
    medicine_id: str
    user_id: str
    is_active: bool

# Adherence and Feedback
class DoseStatus(BaseModel):
    status: str = Field(pattern="^(taken|missed|snoozed)$")
    correction_note: Optional[str] = None

class FeedbackCreate(BaseModel):
    medicine_id: str
    description: str = Field(max_length=2000)
    severity: int = Field(ge=1, le=4)
    occurred_at: str # ISO format

class AssignmentCreate(BaseModel):
    patient_id: str
    provider_id: str
    note: Optional[str] = None

