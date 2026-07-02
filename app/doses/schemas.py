from typing import Optional

from pydantic import BaseModel


class DoseStatus(BaseModel):
    status: str
    correction_note: Optional[str] = None
