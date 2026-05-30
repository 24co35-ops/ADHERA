from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

class FeedbackCreate(BaseModel):
    medicine_id: str
    description: str
    severity: int
    occurred_at: str = datetime.now(timezone.utc).isoformat()
