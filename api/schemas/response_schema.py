from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AskRequest(BaseModel):
    question: str


class ResponseBase(BaseModel):
    """Base schema for response data."""

    question: str
    answer: str
    # context_used: List[str]
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None


class ResponseCreate(ResponseBase):
    """Schema for creating a new response."""

    pass


class Response(ResponseBase):
    """Schema for response data with database fields."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
