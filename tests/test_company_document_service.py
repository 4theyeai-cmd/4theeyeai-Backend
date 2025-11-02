"""
Unit tests for CompanyDocumentService
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from api.services.company_document_service import CompanyDocumentService
from api.models.company_document_model import CompanyDocument


class TestCompanyDocumentService:
    """Tests for CompanyDocumentService"""

    @pytest.fixture
    def service(self, temp_pdf_uploads_dir):
        """Create a CompanyDocumentService instance"""
        with patch.dict("os.environ", {"PDF_UPLOADS_DIR": str(temp_pdf_uploads_dir)}):
            return CompanyDocumentService()

    def test_save_uploaded_file(
        self, service: CompanyDocumentService, sample_pdf_content: bytes
    ):
        """Test saving uploaded file"""
        file_path = service.save_uploaded_file(
            sample_pdf_content, "TestCompany", "test.pdf"
        )

        assert isinstance(file_path, str)
        assert Path(file_path).exists()
        assert Path(file_path).read_bytes() == sample_pdf_content
        assert "TestCompany" in file_path

    def test_save_uploaded_file_normalizes_company_name(
        self, service: CompanyDocumentService, sample_pdf_content: bytes
    ):
        """Test that company name is normalized for filesystem"""
        file_path = service.save_uploaded_file(
            sample_pdf_content, "Test/Company", "test.pdf"
        )

        assert "Test_Company" in file_path
        assert "/" not in file_path.split("Test")[1]

    def test_create_document_record(self, service: CompanyDocumentService, test_db):
        """Test creating document record in database"""
        document = service.create_document_record(
            db=test_db,
            company_name="TestCompany",
            file_name="test.pdf",
            file_path="/path/to/test.pdf",
            vector_store_path="/path/to/vector_store",
            description="Test description",
        )

        assert isinstance(document, CompanyDocument)
        assert document.id is not None
        assert document.company_name == "TestCompany"
        assert document.file_name == "test.pdf"
        assert document.vector_store_path == "/path/to/vector_store"
        assert document.description == "Test description"

    def test_get_documents_by_company(self, service: CompanyDocumentService, test_db):
        """Test getting documents for a company"""
        # Create test documents
        doc1 = service.create_document_record(
            db=test_db,
            company_name="CompanyA",
            file_name="doc1.pdf",
            file_path="/path/to/doc1.pdf",
        )
        doc2 = service.create_document_record(
            db=test_db,
            company_name="CompanyA",
            file_name="doc2.pdf",
            file_path="/path/to/doc2.pdf",
        )
        doc3 = service.create_document_record(
            db=test_db,
            company_name="CompanyB",
            file_name="doc3.pdf",
            file_path="/path/to/doc3.pdf",
        )

        # Get documents for CompanyA
        documents = service.get_documents_by_company(test_db, "CompanyA")

        assert len(documents) == 2
        assert all(doc.company_name == "CompanyA" for doc in documents)

    def test_get_document_by_id(self, service: CompanyDocumentService, test_db):
        """Test getting document by ID"""
        # Create a document
        created_doc = service.create_document_record(
            db=test_db,
            company_name="TestCompany",
            file_name="test.pdf",
            file_path="/path/to/test.pdf",
        )

        # Get it by ID
        doc_id = int(created_doc.id)  # type: ignore
        retrieved_doc = service.get_document_by_id(test_db, doc_id)

        assert retrieved_doc is not None
        assert retrieved_doc.id == created_doc.id
        assert retrieved_doc.company_name == "TestCompany"

    def test_get_document_by_id_not_found(
        self, service: CompanyDocumentService, test_db
    ):
        """Test getting non-existent document"""
        document = service.get_document_by_id(test_db, 99999)
        assert document is None

    @patch("api.services.company_document_service.os.path.exists")
    @patch("api.services.company_document_service.os.remove")
    @patch("api.services.company_document_service.shutil.rmtree")
    def test_delete_document_success(
        self,
        mock_rmtree,
        mock_remove,
        mock_exists,
        service: CompanyDocumentService,
        test_db,
    ):
        """Test deleting a document"""
        # Create a document
        doc = service.create_document_record(
            db=test_db,
            company_name="TestCompany",
            file_name="test.pdf",
            file_path="/path/to/test.pdf",
            vector_store_path="/path/to/vector_store",
        )

        # Get document ID
        doc_id: int = int(doc.id)

        # Mock file system operations
        mock_exists.return_value = True

        # Delete
        result = service.delete_document(test_db, doc_id)

        assert result is True
        mock_remove.assert_called_once_with("/path/to/test.pdf")
        mock_rmtree.assert_called_once_with("/path/to/vector_store")

        # Verify document is deleted from DB
        deleted_doc = service.get_document_by_id(test_db, doc_id)
        assert deleted_doc is None

    def test_delete_document_not_found(self, service: CompanyDocumentService, test_db):
        """Test deleting non-existent document"""
        result = service.delete_document(test_db, 99999)
        assert result is False
