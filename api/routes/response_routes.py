from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from api.database.database import get_db
from api.models.response_model import Response
from api.schemas.response_schema import ResponseCreate, Response as ResponseSchema
from api.services.openai_service import OpenAIService
from api.services.google_sheets_service import GoogleSheetsService
import uuid

router = APIRouter()
openai_service = OpenAIService()
sheets_service = GoogleSheetsService()


@router.post("/ask", response_model=ResponseSchema)
async def ask_question(
    question: str,
    user_id: Optional[str] = Header(None),
    session_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Ask a question and get an AI response."""
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        # Get knowledge base from Google Sheets
        knowledge_base = sheets_service.format_knowledge_for_prompt()
        print("knowledge_base:", knowledge_base)

        # Get response from OpenAI
        ai_response = openai_service.get_response(question, knowledge_base)
        print("ai_response:", ai_response)
        if not ai_response["answer"]:
            raise HTTPException(
                status_code=500,
                detail=ai_response["error_message"] or "Failed to generate response",
            )

        # Create response record
        db_response = Response(
            question=question,
            answer=ai_response["answer"],
            # context_used=sheets_service.get_knowledge_base(),
            confidence_score=ai_response["confidence_score"],
            error_message=ai_response["error_message"],
            user_id=user_id,
            session_id=session_id,
        )

        db.add(db_response)
        db.commit()
        db.refresh(db_response)

        return db_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/responses", response_model=List[ResponseSchema])
async def get_responses(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all responses with filtering options."""
    query = db.query(Response)

    if user_id:
        query = query.filter(Response.user_id == user_id)
    if session_id:
        query = query.filter(Response.session_id == session_id)

    responses = (
        query.order_by(Response.created_at.desc()).offset(skip).limit(limit).all()
    )
    return responses


@router.get("/responses/{response_id}", response_model=ResponseSchema)
async def get_response(response_id: int, db: Session = Depends(get_db)):
    """Get a specific response by ID."""
    response = db.query(Response).filter(Response.id == response_id).first()
    if response is None:
        raise HTTPException(status_code=404, detail="Response not found")
    return response
