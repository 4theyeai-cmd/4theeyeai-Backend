from sqlalchemy.orm import Session
from typing import List, Optional
from api.models.trip_model import Trip, Passenger
from api.schemas.trip_schema import TripCreate, TripUpdate
from api.services.date_converter import convert_to_standard_date


def create_trip(db: Session, trip_data: TripCreate) -> Trip:
    # Convert travelDate to standard format
    standardized_date = convert_to_standard_date(trip_data.travelDate)

    db_trip = Trip(
        airportName=trip_data.airportName,
        travelDate=standardized_date,
        flightNumber=trip_data.flightNumber,
        travelType=trip_data.travelType,
        flightType=trip_data.flightType or "class_a",
        passengerCount=trip_data.passengerCount,
        additionalInfo=trip_data.additionalInfo,
        buyerPhone=trip_data.buyerPhone,
        buyerEmail=trip_data.buyerEmail,
        orderId=trip_data.orderId,
    )
    db.add(db_trip)
    db.flush()  # تا trip_id برای مسافران داشته باشیم
    for p in trip_data.passengers:
        db_passenger = Passenger(
            trip_id=db_trip.id,
            name=p.name,
            lastName=p.lastName,
            nationalId=p.nationalId,
            passportNumber=p.passportNumber,
            luggageCount=p.luggageCount,
            passengerType=p.passengerType,
            gender=p.gender,
            nationality=p.nationality or "ایرانی",
        )
        db.add(db_passenger)
    db.commit()
    db.refresh(db_trip)
    return db_trip


def get_trip(db: Session, trip_id: str) -> Optional[Trip]:
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if trip and trip.travelDate:
        # Convert travelDate to standard format for frontend datepicker
        original_date = str(trip.travelDate)
        converted_date = convert_to_standard_date(original_date)
        if converted_date:
            trip.travelDate = converted_date  # type: ignore
    return trip


def update_trip(db: Session, trip_id: str, trip_update: TripUpdate) -> Optional[Trip]:
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        return None

    # Update only provided fields
    update_data = trip_update.dict(exclude_unset=True)

    # Handle passengers update separately
    passengers_data = update_data.pop("passengers", None)

    # Handle date conversion if travelDate is being updated
    if "travelDate" in update_data:
        update_data["travelDate"] = convert_to_standard_date(update_data["travelDate"])

    # Update the trip object
    for field, value in update_data.items():
        setattr(trip, field, value)

    # Update passengers if provided
    if passengers_data is not None:
        # Delete existing passengers
        db.query(Passenger).filter(Passenger.trip_id == trip_id).delete()

        # Add new passengers
        for p in passengers_data:
            db_passenger = Passenger(
                trip_id=trip.id,
                name=p.name,
                lastName=p.lastName,
                nationalId=p.nationalId,
                passportNumber=p.passportNumber,
                luggageCount=p.luggageCount,
                passengerType=p.passengerType,
                gender=p.gender,
                nationality=p.nationality or "ایرانی",
            )
            db.add(db_passenger)

    db.commit()
    db.refresh(trip)
    return trip
