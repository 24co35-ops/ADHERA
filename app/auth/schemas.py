from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    date_of_birth: Optional[date] = None
    contact_number: Optional[str] = None
    timezone: str = "UTC"
    specialization: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    mfa_required: Optional[bool] = None
    partial_token: Optional[str] = None

class MfaCode(BaseModel):
    code: str

class MfaConfirm(BaseModel):
    partial_token: str
    code: str

class RefreshRequest(BaseModel):
    refresh_token: str

