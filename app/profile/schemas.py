from pydantic import BaseModel, Field
from typing import Optional

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    contact_number: Optional[str] = None
    timezone: Optional[str] = None

class EmergencyContact(BaseModel):
    full_name: str
    relationship: str
    email: str
    verified: bool = False
