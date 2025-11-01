from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List

from api.database.database import get_db
from api.services.passport_service import PassportService
from api.schemas.passport_schema import PassportData, PassportDataCreate

router = APIRouter()
passport_service = PassportService()


@router.post("/passport/upload", response_model=PassportData)
async def upload_passport(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and process passport image."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Read image data
        image_data = await file.read()

        # Process passport image
        passport_data = passport_service.process_passport_image(image_data)

        # Save to database
        db_passport = passport_service.save_passport_data(db, passport_data)

        return db_passport
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/passport/{passport_number}", response_model=PassportData)
async def get_passport(passport_number: str, db: Session = Depends(get_db)):
    """Get passport data by passport number."""
    passport = passport_service.get_passport_by_number(db, passport_number)
    if not passport:
        raise HTTPException(status_code=404, detail="Passport not found")
    return passport
