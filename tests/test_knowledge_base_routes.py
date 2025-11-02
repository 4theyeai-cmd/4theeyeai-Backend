"""
Tests for Knowledge Base API routes
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestKnowledgeBaseUpload:
    """Tests for PDF upload endpoint"""

    def test_upload_pdf_success(
        self, client: TestClient, sample_pdf_file, mock_openai_key
    ):
        """Test successful PDF upload"""
        with open(sample_pdf_file, "rb") as f:
            files = {"file": ("test_document.pdf", f, "application/pdf")}
            data = {"company_name": "TestCompany", "description": "Test description"}
            
            response = client.post(
                "/api/v1/knowledge-base/upload",
                files=files,
                data=data
            )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["company_name"] == "TestCompany"
        assert response_data["file_name"] == "test_document.pdf"
        assert "vector_store_path" in response_data
        assert response_data["file_path"] is not None

    def test_upload_non_pdf_file(self, client: TestClient, tmp_path):
        """Test upload with non-PDF file"""
        # Create a text file instead of PDF
        text_file = tmp_path / "test.txt"
        text_file.write_text("This is not a PDF")
        
        with open(text_file, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            data = {"company_name": "TestCompany"}
            
            response = client.post(
                "/api/v1/knowledge-base/upload",
                files=files,
                data=data
            )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "PDF" in response.json()["detail"]

    def test_upload_missing_company_name(self, client: TestClient, sample_pdf_file):
        """Test upload without company name"""
        with open(sample_pdf_file, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            
            response = client.post(
                "/api/v1/knowledge-base/upload",
                files=files
            )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upload_invalid_pdf_content(self, client: TestClient, tmp_path):
        """Test upload with invalid PDF content"""
        invalid_pdf = tmp_path / "invalid.pdf"
        invalid_pdf.write_bytes(b"This is not a valid PDF file")
        
        with open(invalid_pdf, "rb") as f:
            files = {"file": ("invalid.pdf", f, "application/pdf")}
            data = {"company_name": "TestCompany"}
            
            response = client.post(
                "/api/v1/knowledge-base/upload",
                files=files,
                data=data
            )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid PDF" in response.json()["detail"]


class TestKnowledgeBaseQuestion:
    """Tests for question answering endpoint"""

    def test_ask_question_without_knowledge_base(
        self, client: TestClient, mock_openai_key
    ):
        """Test asking question when no knowledge base exists"""
        data = {
            "company_name": "NonExistentCompany",
            "question": "What is your policy?",
        }
        
        response = client.post("/api/v1/knowledge-base/question", json=data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No knowledge base found" in response.json()["detail"]

    def test_ask_question_missing_fields(self, client: TestClient):
        """Test asking question with missing required fields"""
        # Missing company_name
        data = {"question": "What is your policy?"}
        response = client.post("/api/v1/knowledge-base/question", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing question
        data = {"company_name": "TestCompany"}
        response = client.post("/api/v1/knowledge-base/question", json=data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestKnowledgeBaseDocuments:
    """Tests for document management endpoints"""

    def test_get_company_documents_empty(self, client: TestClient):
        """Test getting documents for a company with no documents"""
        response = client.get("/api/v1/knowledge-base/documents/TestCompany")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_document_not_found(self, client: TestClient):
        """Test getting a non-existent document"""
        response = client.get("/api/v1/knowledge-base/document/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_delete_document_not_found(self, client: TestClient):
        """Test deleting a non-existent document"""
        response = client.delete("/api/v1/knowledge-base/document/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_company_knowledge_base(self, client: TestClient):
        """Test deleting all documents for a company"""
        response = client.delete("/api/v1/knowledge-base/company/TestCompany")
        
        # Should succeed even if company doesn't exist
        assert response.status_code == status.HTTP_200_OK
        assert "deleted" in response.json()["message"].lower()

