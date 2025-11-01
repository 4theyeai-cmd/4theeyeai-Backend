from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from api.database.database import get_db
from api.schemas.message_schema import MessageCreate, Message
from api.services.message_service import save_messages
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/messages/batch", response_model=List[Message])
def create_messages(
    messages: List[MessageCreate],
    db: Session = Depends(get_db),
):
    try:
        saved_messages = save_messages(db, messages)
        return saved_messages
    except IntegrityError as e:
        logger.error(f"Database integrity error: {str(e)}")
        # Try to rollback and retry with individual message handling
        db.rollback()
        try:
            saved_messages = save_messages(db, messages)
            return saved_messages
        except Exception as retry_error:
            logger.error(f"Retry failed: {str(retry_error)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to save messages due to duplicate IDs: {str(e)}",
            )
    except Exception as e:
        logger.error(f"Unexpected error saving messages: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to save messages: {str(e)}"
        )
