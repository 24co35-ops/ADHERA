from pydantic import BaseModel
from typing import Optional

class AssignmentCreate(BaseModel):
    patient_id: str
    provider_id: str
    note: Optional[str] = None

class AssignmentUpdate(BaseModel):
    status: str
    note: Optional[str] = None

class UserUpdate(BaseModel):
    is_active: bool
