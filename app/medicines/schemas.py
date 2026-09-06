import re
from datetime import date
from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class MedicineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    dosage_amount: Decimal = Field(..., gt=Decimal("0"), le=Decimal("9999.99"))
    dosage_unit: Literal["mg", "ml", "units"]
    route: Literal["oral", "topical", "injection", "inhaled", "other"]
    frequency_type: Literal["daily", "weekday", "alternate", "prn"]
    start_date: date
    end_date: Optional[date] = None
    instructions: Optional[str] = Field(None, max_length=1000)
    recurrence_params: Optional[Any] = None

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # 1. Frequency / frequency_type normalization
            if "frequency" in data and data.get("frequency_type") is None:
                freq = str(data["frequency"]).strip().lower()
                if freq in ("once daily", "daily", "every day", "day"):
                    data["frequency_type"] = "daily"
                elif "week" in freq:
                    data["frequency_type"] = "weekday"
                elif "alt" in freq:
                    data["frequency_type"] = "alternate"
                elif "prn" in freq or "as needed" in freq:
                    data["frequency_type"] = "prn"
                else:
                    data["frequency_type"] = freq
            elif "frequency_type" in data and isinstance(data["frequency_type"], str):
                data["frequency_type"] = data["frequency_type"].strip().lower()

            # 2. Dosage parsing (if single dosage string or separate unit is provided)
            if "dosage" in data:
                raw_dosage = str(data["dosage"]).strip()
                if data.get("dosage_amount") is None:
                    match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)?", raw_dosage)
                    if match:
                        data["dosage_amount"] = match.group(1)
                        if match.group(2) and data.get("dosage_unit") is None:
                            unit_cand = match.group(2).lower()
                            if unit_cand in ("mg", "ml", "units", "unit"):
                                data["dosage_unit"] = "units" if unit_cand == "unit" else unit_cand
                    else:
                        data["dosage_amount"] = raw_dosage
            if "unit" in data and data.get("dosage_unit") is None:
                data["dosage_unit"] = data["unit"]

            # 3. Route normalization
            if "route" in data and isinstance(data["route"], str):
                r = data["route"].strip().lower()
                if r == "inhalation":
                    data["route"] = "inhaled"
                elif r == "drops":
                    data["route"] = "other"
                else:
                    data["route"] = r

            # 4. Dosage unit normalization
            if "dosage_unit" in data and isinstance(data["dosage_unit"], str):
                u = data["dosage_unit"].strip().lower()
                if u == "unit":
                    data["dosage_unit"] = "units"
                else:
                    data["dosage_unit"] = u

        return data

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: Optional[date], info) -> Optional[date]:
        if v is not None and "start_date" in info.data:
            start_date = info.data["start_date"]
            if start_date and v < start_date:
                raise ValueError("end_date must be on or after start_date")
        return v


class MedicineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    dosage_amount: Optional[Decimal] = Field(None, gt=Decimal("0"), le=Decimal("9999.99"))
    dosage_unit: Optional[Literal["mg", "ml", "units"]] = None
    route: Optional[Literal["oral", "topical", "injection", "inhaled", "other"]] = None
    frequency_type: Optional[Literal["daily", "weekday", "alternate", "prn"]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    instructions: Optional[str] = Field(None, max_length=1000)
    recurrence_params: Optional[Any] = None

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "frequency" in data and data.get("frequency_type") is None:
                freq = str(data["frequency"]).strip().lower()
                if freq in ("once daily", "daily", "every day", "day"):
                    data["frequency_type"] = "daily"
                elif "week" in freq:
                    data["frequency_type"] = "weekday"
                elif "alt" in freq:
                    data["frequency_type"] = "alternate"
                elif "prn" in freq or "as needed" in freq:
                    data["frequency_type"] = "prn"
                else:
                    data["frequency_type"] = freq
            elif "frequency_type" in data and isinstance(data["frequency_type"], str):
                data["frequency_type"] = data["frequency_type"].strip().lower()

            if "dosage" in data and data.get("dosage_amount") is None:
                raw_dosage = str(data["dosage"]).strip()
                match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)?", raw_dosage)
                if match:
                    data["dosage_amount"] = match.group(1)
                    if match.group(2) and data.get("dosage_unit") is None:
                        unit_cand = match.group(2).lower()
                        if unit_cand in ("mg", "ml", "units", "unit"):
                            data["dosage_unit"] = "units" if unit_cand == "unit" else unit_cand
                else:
                    data["dosage_amount"] = raw_dosage
            if "unit" in data and data.get("dosage_unit") is None:
                data["dosage_unit"] = data["unit"]

            if "route" in data and isinstance(data["route"], str):
                r = data["route"].strip().lower()
                if r == "inhalation":
                    data["route"] = "inhaled"
                elif r == "drops":
                    data["route"] = "other"
                else:
                    data["route"] = r

            if "dosage_unit" in data and isinstance(data["dosage_unit"], str):
                u = data["dosage_unit"].strip().lower()
                if u == "unit":
                    data["dosage_unit"] = "units"
                else:
                    data["dosage_unit"] = u

        return data


class ReminderCreate(BaseModel):
    dose_label: Literal["morning", "afternoon", "evening", "night"]
    dose_time_utc: Optional[str] = None
    timezone: str = "UTC"
    recurrence_type: Optional[Literal["daily", "weekday", "alternate", "prn"]] = "daily"
    recurrence_params: Optional[Any] = None
    advance_notify: bool = False

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "dose_label" in data and isinstance(data["dose_label"], str):
                data["dose_label"] = data["dose_label"].strip().lower()
            if ("scheduled_time" in data or "dose_time" in data) and data.get("dose_time_utc") is None:
                data["dose_time_utc"] = data.get("scheduled_time") or data.get("dose_time")
            if "frequency_type" in data and data.get("recurrence_type") is None:
                data["recurrence_type"] = data["frequency_type"]
            if "recurrence_type" in data and isinstance(data["recurrence_type"], str):
                data["recurrence_type"] = data["recurrence_type"].strip().lower()
            if "advance_notification_minutes" in data and "advance_notify" not in data:
                data["advance_notify"] = bool(data["advance_notification_minutes"] > 0)
        return data


class ReminderUpdate(BaseModel):
    dose_label: Optional[Literal["morning", "afternoon", "evening", "night"]] = None
    dose_time_utc: Optional[str] = None
    timezone: Optional[str] = None
    recurrence_type: Optional[Literal["daily", "weekday", "alternate", "prn"]] = None
    recurrence_params: Optional[Any] = None
    is_active: Optional[bool] = None
    advance_notify: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "dose_label" in data and isinstance(data["dose_label"], str):
                data["dose_label"] = data["dose_label"].strip().lower()
            if ("scheduled_time" in data or "dose_time" in data) and data.get("dose_time_utc") is None:
                data["dose_time_utc"] = data.get("scheduled_time") or data.get("dose_time")
            if "frequency_type" in data and data.get("recurrence_type") is None:
                data["recurrence_type"] = data["frequency_type"]
            if "recurrence_type" in data and isinstance(data["recurrence_type"], str):
                data["recurrence_type"] = data["recurrence_type"].strip().lower()
            if "advance_notification_minutes" in data and "advance_notify" not in data:
                data["advance_notify"] = bool(data["advance_notification_minutes"] > 0)
        return data
