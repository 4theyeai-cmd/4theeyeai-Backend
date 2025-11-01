import pytesseract  # type: ignore
from PIL import Image  # type: ignore
import io
from typing import Dict, Optional
from api.models.passport_model import PassportData
from sqlalchemy.orm import Session


class PassportService:
    def __init__(self):
        # Configure pytesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = r'path_to_tesseract'
        pass

    def process_passport_image(self, image_data: bytes) -> Dict[str, str]:
        """Process passport image and extract text using OCR."""
        try:
            # Convert bytes to image
            image = Image.open(io.BytesIO(image_data))

            # Extract text from image
            text = pytesseract.image_to_string(image)

            # Parse the extracted text to get passport information
            passport_data = self._parse_passport_text(text)

            return passport_data
        except Exception as e:
            raise Exception(f"Error processing passport image: {str(e)}")

    def _parse_passport_text(self, text: str) -> Dict[str, str]:
        """Parse the OCR text to extract passport information."""
        # This is a basic implementation. You might need to enhance it based on your specific passport format
        lines = text.split("\n")
        passport_data = {
            "passport_number": "",
            "full_name": "",
            "nationality": "ایرانی",
            "date_of_birth": "",
            "place_of_birth": "",
            "date_of_issue": "",
            "date_of_expiry": "",
            "issuing_authority": "",
        }

        # Add your parsing logic here based on the passport format
        # This is just a placeholder implementation
        for line in lines:
            if "PASSPORT" in line:
                passport_data["passport_number"] = line.split()[-1]
            elif "Name" in line:
                passport_data["full_name"] = line.split("Name")[-1].strip()
            # Add more parsing logic for other fields

        return passport_data

    def save_passport_data(
        self, db: Session, passport_data: Dict[str, str]
    ) -> PassportData:
        """Save passport data to database."""
        try:
            # Set default nationality if empty
            if not passport_data.get("nationality"):
                passport_data["nationality"] = "ایرانی"

            db_passport = PassportData(**passport_data)
            db.add(db_passport)
            db.commit()
            db.refresh(db_passport)
            return db_passport
        except Exception as e:
            db.rollback()
            raise Exception(f"Error saving passport data: {str(e)}")

    def get_passport_by_number(
        self, db: Session, passport_number: str
    ) -> Optional[PassportData]:
        """Retrieve passport data by passport number."""
        return (
            db.query(PassportData)
            .filter(PassportData.passport_number == passport_number)
            .first()
        )
