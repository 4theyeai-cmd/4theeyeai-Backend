from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PassportDataBase(BaseModel):
    passport_number: str
    full_name: str
    nationality: str = "ایرانی"
    date_of_birth: str
    place_of_birth: str
    date_of_issue: str
    date_of_expiry: str
    issuing_authority: str


class PassportDataCreate(PassportDataBase):
    pass


class PassportData(PassportDataBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
