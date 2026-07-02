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
    is_active: Optional[bool] = None

class RejectBody(BaseModel):
    reason: str
