from pydantic import BaseModel, Field


class WellnessSessionCreate(BaseModel):
    pattern_name: str = Field(..., min_length=1, max_length=50, description="Name of breathing pattern (e.g., Calm, Focus, Custom)")
    duration_seconds: int = Field(..., ge=10, le=7200, description="Total duration of completed breathing session in seconds")


class WellnessSessionResponse(BaseModel):
    id: str
    user_id: str
    pattern_name: str
    duration_seconds: int
    completed_at: str
