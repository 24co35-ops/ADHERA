from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    contact_number: Optional[str] = None
    timezone: Optional[str] = None
    date_of_birth: Optional[date] = None
    blood_group: Optional[str] = None

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_groups = {'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'}
        if v not in valid_groups:
            raise ValueError("Invalid blood group format.")
        return v

class EmergencyContact(BaseModel):
    full_name: str
    relationship: str
    email: str
    verified: bool = False

class PushKeys(BaseModel):
    auth: str
    p256dh: str

class PushSubscriptionCreate(BaseModel):
    endpoint: str
    keys: PushKeys

