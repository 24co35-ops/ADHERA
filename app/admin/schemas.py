from typing import Optional

from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    patient_id: str
    provider_id: str
    note: Optional[str] = None

class AssignmentUpdate(BaseModel):
    status: str
    note: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    contact_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    blood_group: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None

class RejectBody(BaseModel):
    reason: str

class InviteUser(BaseModel):
    email: str
    role: str # 'provider' or 'patient'
    full_name: Optional[str] = None

class StatusChange(BaseModel):
    is_active: bool
    reason: str  # mandatory — written to audit_log
