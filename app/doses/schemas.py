from pydantic import BaseModel
from typing import Optional

class DoseStatus(BaseModel):
    status: str
    correction_note: Optional[str] = None
