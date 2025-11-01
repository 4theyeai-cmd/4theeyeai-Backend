from pydantic import BaseModel
from typing import List, Optional, Literal


class PassengerBase(BaseModel):
    name: str
    lastName: str
    nationalId: str
    passportNumber: str
    luggageCount: int
    passengerType: str
    gender: str
    nationality: str = "iranian"


class PassengerCreate(PassengerBase):
    pass


class Passenger(PassengerBase):
    id: str

    class Config:
        orm_mode = True


class TripBase(BaseModel):
    airportName: str
    travelDate: str
    flightNumber: str
    travelType: Literal["departure", "arrival"]
    flightType: Optional[Literal["class_a", "class_b"]] = "class_a"
    passengerCount: int
    additionalInfo: str = ""
    buyerPhone: Optional[str] = None
    buyerEmail: Optional[str] = None
    orderId: Optional[str] = None


class TripCreate(TripBase):
    passengers: List[PassengerCreate]


class TripUpdate(BaseModel):
    airportName: Optional[str] = None
    travelDate: Optional[str] = None
    flightNumber: Optional[str] = None
    travelType: Optional[Literal["departure", "arrival"]] = None
    flightType: Optional[Literal["class_a", "class_b"]] = None
    passengerCount: Optional[int] = None
    additionalInfo: Optional[str] = None
    buyerPhone: Optional[str] = None
    buyerEmail: Optional[str] = None
    orderId: Optional[str] = None
    passengers: Optional[List[PassengerCreate]] = None


class Trip(TripBase):
    id: str
    passengers: List[Passenger]

    class Config:
        orm_mode = True
