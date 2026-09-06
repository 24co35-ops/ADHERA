from typing import List, Optional

from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    document_name: str
    snippet: str
    score: Optional[float] = None


class SuggestedFeedback(BaseModel):
    medicine_id: Optional[str] = None
    medicine_name: str
    possible_side_effect: str
    severity: int = 2


class ChatQueryRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User question to the medical assistant")


class ChatQueryResponse(BaseModel):
    id: str
    role: str = "assistant"
    content: str
    sources: List[SourceCitation] = []
    suggested_feedback: Optional[SuggestedFeedback] = None
    created_at: str


class ChatMessageResponse(BaseModel):
    id: str
    user_id: str
    role: str
    content: str
    sources: List[SourceCitation] = []
    suggested_feedback: Optional[SuggestedFeedback] = None
    created_at: str


class IngestResponse(BaseModel):
    documents_ingested: int
    chunks_created: int
    status: str
