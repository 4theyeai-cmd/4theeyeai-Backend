from pydantic import BaseModel, Field
from typing import List, Optional
from api.schemas.message_schema import MessageSender


class Passenger(BaseModel):
    name: str
    lastName: str
    nationalId: str
    passportNumber: str
    luggageCount: int
    passengerType: str
    gender: str
    nationality: str = "ایرانی"  # ایرانی، غیر ایرانی، دیپلمات


class MessageInput(BaseModel):
    id: Optional[str] = None
    text: str
    sender: Optional[MessageSender] = None


class ExtractInfoRequest(BaseModel):
    messages: List[MessageInput]


class ExtractInfoResponse(BaseModel):
    airportName: str
    travelType: str  # "arrival" or "departure"
    travelDate: str
    flightNumber: str = ""
    passengerCount: int
    passengers: List[Passenger]
    additionalInfo: Optional[str] = None


class MessageRequest(BaseModel):
    id: str
    text: str
    sender: MessageSender
