from datetime import date
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class MedicineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    dosage_amount: Optional[Decimal] = Field(None, gt=0, le=Decimal("9999.99"))
    dosage_unit: Optional[str] = None
    route: str
    frequency_type: str
    start_date: date
    end_date: Optional[date] = None
    instructions: Optional[str] = Field(None, max_length=1000)
    recurrence_params: Optional[dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "dosage" in data and data.get("dosage_amount") is None:
                data["dosage_amount"] = data["dosage"]
            if "unit" in data and data.get("dosage_unit") is None:
                data["dosage_unit"] = data["unit"]
        return data


class MedicineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    dosage_amount: Optional[Decimal] = Field(None, gt=0, le=Decimal("9999.99"))
    dosage_unit: Optional[str] = None
    is_active: Optional[bool] = None
    instructions: Optional[str] = Field(None, max_length=1000)

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "dosage" in data and data.get("dosage_amount") is None:
                data["dosage_amount"] = data["dosage"]
            if "unit" in data and data.get("dosage_unit") is None:
                data["dosage_unit"] = data["unit"]
        return data


class ReminderCreate(BaseModel):
    dose_label: str
    dose_time_utc: Optional[str] = None
    timezone: str = "UTC"
    recurrence_type: Optional[str] = None
    recurrence_params: Optional[dict[str, Any]] = None
    advance_notify: bool = False

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if ("scheduled_time" in data or "dose_time" in data) and data.get("dose_time_utc") is None:
                data["dose_time_utc"] = data.get("scheduled_time") or data.get("dose_time")
            if "frequency_type" in data and data.get("recurrence_type") is None:
                data["recurrence_type"] = data["frequency_type"]
        return data


class ReminderUpdate(BaseModel):
    dose_label: Optional[str] = None
    dose_time_utc: Optional[str] = None
    timezone: Optional[str] = None
    recurrence_type: Optional[str] = None
    recurrence_params: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None
    advance_notify: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if ("scheduled_time" in data or "dose_time" in data) and data.get("dose_time_utc") is None:
                data["dose_time_utc"] = data.get("scheduled_time") or data.get("dose_time")
            if "frequency_type" in data and data.get("recurrence_type") is None:
                data["recurrence_type"] = data["frequency_type"]
        return data
