from pydantic import BaseModel
from typing import Optional, Any
from datetime import date

class MedicineCreate(BaseModel):
    name: str
    dosage_amount: float
    dosage_unit: str
    route: str
    frequency_type: str
    start_date: date
    end_date: Optional[date] = None
    instructions: Optional[str] = None
    recurrence_params: Optional[dict[str, Any]] = None

class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    dosage_amount: Optional[float] = None
    dosage_unit: Optional[str] = None
    is_active: Optional[bool] = None

class ReminderCreate(BaseModel):
    dose_label: str
    dose_time_utc: str
    timezone: str
    recurrence_type: str
    recurrence_params: Optional[dict[str, Any]] = None

class ReminderUpdate(BaseModel):
    dose_label: Optional[str] = None
    dose_time_utc: Optional[str] = None
    timezone: Optional[str] = None
    recurrence_type: Optional[str] = None
    recurrence_params: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None
