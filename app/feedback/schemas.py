from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone


class FeedbackCreate(BaseModel):
    medicine_id: str
    description: str = Field(..., min_length=1, max_length=2000)
    severity: int
    occurred_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_not_future(cls, v: str) -> str:
        """Reject timestamps more than 60 seconds in the future to guard against clock skew."""
        try:
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError("occurred_at must be a valid ISO8601 datetime string")
        now = datetime.now(timezone.utc)
        if dt > now:
            raise ValueError("occurred_at must not be in the future")
        return v
