from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from api.database.database import Base


class Response(Base):  # type: ignore
    """SQLAlchemy model for storing responses."""

    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    # context_used = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=True)
    error_message = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert the response to a dictionary."""
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            # "context_used": self.context_used,
            "confidence_score": self.confidence_score,
            "error_message": self.error_message,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
