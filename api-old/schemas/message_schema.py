from pydantic import BaseModel, Field
from typing import List
from enum import Enum
from datetime import datetime


class MessageSender(str, Enum):
    CLIENT = "CLIENT"
    AVATAR = "AVATAR"


class MessageBase(BaseModel):
    sender: MessageSender


class MessageCreate(MessageBase):
    id: str = Field(...)
    text: str


class Message(MessageBase):
    id: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
