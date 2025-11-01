from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from typing import List
from api.models.message_model import Message
from api.schemas.message_schema import MessageCreate
from datetime import datetime


def save_messages(db: Session, messages: List[MessageCreate]):
    if not messages:
        return []

    # Prepare data for bulk upsert
    message_data = []
    for msg in messages:
        message_data.append(
            {
                "id": msg.id,
                "sender": msg.sender.value,
                "content": msg.text,
                "created_at": datetime.utcnow(),
            }
        )

    # Use PostgreSQL ON CONFLICT for efficient upsert
    stmt = insert(Message).values(message_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "sender": stmt.excluded.sender,
            "content": stmt.excluded.content,
            "created_at": stmt.excluded.created_at,
        },
    )

    db.execute(stmt)
    db.commit()

    # Return the saved messages
    message_ids = [msg.id for msg in messages]
    saved_messages = db.query(Message).filter(Message.id.in_(message_ids)).all()
    return saved_messages
