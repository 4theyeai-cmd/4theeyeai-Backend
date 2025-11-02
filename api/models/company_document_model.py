from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from api.database.database import Base


class CompanyDocument(Base):
    __tablename__ = "company_documents"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True, nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    vector_store_path = Column(
        String, nullable=True
    )  # Path to vector store for this company
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
