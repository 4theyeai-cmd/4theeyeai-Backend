from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CompanyDocumentBase(BaseModel):
    company_name: str
    file_name: str
    description: Optional[str] = None


class CompanyDocumentCreate(CompanyDocumentBase):
    pass


class CompanyDocument(CompanyDocumentBase):
    id: int
    file_path: str
    vector_store_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuestionRequest(BaseModel):
    company_name: str
    question: str
    session_id: Optional[str] = None


class QuestionResponse(BaseModel):
    answer: str
    company_name: str
    sources: Optional[list] = None
    confidence_score: Optional[float] = None
