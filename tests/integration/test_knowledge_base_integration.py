"""
Integration tests for Knowledge Base functionality
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pathlib import Path


@pytest.mark.integration
class TestKnowledgeBaseIntegration:
    """Integration tests for knowledge base workflow"""

    def test_full_workflow_upload_and_query(
        self, client: TestClient, sample_pdf_file, mock_openai_key
    ):
        """Test complete workflow: upload PDF and ask question"""
        company_name = "IntegrationTestCompany"
        
        # Step 1: Upload PDF
        with open(sample_pdf_file, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            data = {"company_name": company_name}
            
            upload_response = client.post(
                "/api/v1/knowledge-base/upload",
                files=files,
                data=data
            )
        
        assert upload_response.status_code == status.HTTP_200_OK
        upload_data = upload_response.json()
        document_id = upload_data["id"]
        
        # Step 2: Verify document exists
        get_doc_response = client.get(f"/api/v1/knowledge-base/document/{document_id}")
        assert get_doc_response.status_code == status.HTTP_200_OK
        
        # Step 3: Get all documents for company
        docs_response = client.get(
            f"/api/v1/knowledge-base/documents/{company_name}"
        )
        assert docs_response.status_code == status.HTTP_200_OK
        docs = docs_response.json()
        assert len(docs) == 1
        assert docs[0]["company_name"] == company_name
        
        # Step 4: Delete document
        delete_response = client.delete(
            f"/api/v1/knowledge-base/document/{document_id}"
        )
        assert delete_response.status_code == status.HTTP_200_OK
        
        # Step 5: Verify document is deleted
        get_deleted_response = client.get(
            f"/api/v1/knowledge-base/document/{document_id}"
        )
        assert get_deleted_response.status_code == status.HTTP_404_NOT_FOUND

    def test_multiple_uploads_same_company(
        self, client: TestClient, sample_pdf_file, tmp_path, mock_openai_key
    ):
        """Test uploading multiple PDFs for the same company"""
        company_name = "MultiDocCompany"
        
        # Upload first PDF
        with open(sample_pdf_file, "rb") as f:
            files1 = {"file": ("doc1.pdf", f, "application/pdf")}
            response1 = client.post(
                "/api/v1/knowledge-base/upload",
                files=files1,
                data={"company_name": company_name}
            )
            assert response1.status_code == status.HTTP_200_OK
        
        # Create another PDF file
        pdf2 = tmp_path / "doc2.pdf"
        pdf2.write_bytes(sample_pdf_file.read_bytes())
        
        # Upload second PDF
        with open(pdf2, "rb") as f:
            files2 = {"file": ("doc2.pdf", f, "application/pdf")}
            response2 = client.post(
                "/api/v1/knowledge-base/upload",
                files=files2,
                data={"company_name": company_name}
            )
            assert response2.status_code == status.HTTP_200_OK
        
        # Verify both documents exist
        docs_response = client.get(
            f"/api/v1/knowledge-base/documents/{company_name}"
        )
        assert docs_response.status_code == status.HTTP_200_OK
        docs = docs_response.json()
        assert len(docs) == 2

    def test_company_knowledge_base_deletion(
        self, client: TestClient, sample_pdf_file, mock_openai_key
    ):
        """Test deleting all documents for a company"""
        company_name = "DeleteTestCompany"
        
        # Upload a document
        with open(sample_pdf_file, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            upload_response = client.post(
                "/api/v1/knowledge-base/upload",
                files=files,
                data={"company_name": company_name}
            )
            assert upload_response.status_code == status.HTTP_200_OK
        
        # Verify document exists
        docs_before = client.get(
            f"/api/v1/knowledge-base/documents/{company_name}"
        ).json()
        assert len(docs_before) == 1
        
        # Delete all documents for company
        delete_response = client.delete(
            f"/api/v1/knowledge-base/company/{company_name}"
        )
        assert delete_response.status_code == status.HTTP_200_OK
        
        # Verify documents are deleted
        docs_after = client.get(
            f"/api/v1/knowledge-base/documents/{company_name}"
        ).json()
        assert len(docs_after) == 0

