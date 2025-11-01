from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from api.database.database import Base


class PassportData(Base):
    __tablename__ = "passport_data"

    id = Column(Integer, primary_key=True, index=True)
    passport_number = Column(String, index=True)
    full_name = Column(String)
    nationality = Column(String)
    date_of_birth = Column(String)
    place_of_birth = Column(String)
    date_of_issue = Column(String)
    date_of_expiry = Column(String)
    issuing_authority = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
