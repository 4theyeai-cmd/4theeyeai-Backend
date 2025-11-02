import os
import logging
import shutil
from typing import Optional, List
from pathlib import Path
from sqlalchemy.orm import Session
from api.models.company_document_model import CompanyDocument

logger = logging.getLogger(__name__)


class CompanyDocumentService:
    """Service for managing company documents in the database."""

    def __init__(self):
        self.uploads_dir = Path(os.getenv("PDF_UPLOADS_DIR", "./pdf_uploads"))
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        logger.info("CompanyDocumentService initialized")

    def save_uploaded_file(
        self, file_content: bytes, company_name: str, file_name: str
    ) -> str:
        """
        Save uploaded PDF file to disk.

        Args:
            file_content: File content as bytes
            company_name: Name of the company
            file_name: Original file name

        Returns:
            Path to saved file
        """
        try:
            # Create company directory
            safe_company_name = company_name.replace(" ", "_").replace("/", "_")
            company_dir = self.uploads_dir / safe_company_name
            company_dir.mkdir(parents=True, exist_ok=True)

            # Save file
            file_path = company_dir / file_name
            with open(file_path, "wb") as f:
                f.write(file_content)

            logger.info(f"Saved file: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Error saving file: {str(e)}", exc_info=True)
            raise Exception(f"Error saving file: {str(e)}")

    def create_document_record(
        self,
        db: Session,
        company_name: str,
        file_name: str,
        file_path: str,
        vector_store_path: Optional[str] = None,
        description: Optional[str] = None,
    ) -> CompanyDocument:
        """
        Create a document record in the database.

        Args:
            db: Database session
            company_name: Name of the company
            file_name: Original file name
            file_path: Path to saved file
            vector_store_path: Path to vector store
            description: Optional description

        Returns:
            Created CompanyDocument instance
        """
        try:
            db_document = CompanyDocument(
                company_name=company_name,
                file_name=file_name,
                file_path=file_path,
                vector_store_path=vector_store_path,
                description=description,
            )
            db.add(db_document)
            db.commit()
            db.refresh(db_document)
            return db_document
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating document record: {str(e)}", exc_info=True)
            raise Exception(f"Error creating document record: {str(e)}")

    def get_documents_by_company(
        self, db: Session, company_name: str
    ) -> List[CompanyDocument]:
        """Get all documents for a company."""
        try:
            return (
                db.query(CompanyDocument)
                .filter(CompanyDocument.company_name == company_name)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}", exc_info=True)
            raise Exception(f"Error getting documents: {str(e)}")

    def get_document_by_id(
        self, db: Session, document_id: int
    ) -> Optional[CompanyDocument]:
        """Get a document by ID."""
        try:
            return (
                db.query(CompanyDocument)
                .filter(CompanyDocument.id == document_id)
                .first()
            )
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}", exc_info=True)
            raise Exception(f"Error getting document: {str(e)}")

    def delete_document(self, db: Session, document_id: int) -> bool:
        """Delete a document record and its file."""
        try:
            document = self.get_document_by_id(db, document_id)
            if not document:
                return False

            # Delete file if exists
            if os.path.exists(document.file_path):
                os.remove(document.file_path)

            # Delete vector store if exists
            if document.vector_store_path and os.path.exists(
                document.vector_store_path
            ):
                shutil.rmtree(document.vector_store_path)

            # Delete database record
            db.delete(document)
            db.commit()

            logger.info(f"Deleted document: {document_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting document: {str(e)}", exc_info=True)
            raise Exception(f"Error deleting document: {str(e)}")
