"""
Unit tests for KnowledgeBaseService
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from api.services.knowledge_base_service import KnowledgeBaseService


class TestKnowledgeBaseService:
    """Tests for KnowledgeBaseService"""

    @pytest.fixture
    def service(self, temp_vector_store_dir, mock_openai_key):
        """Create a KnowledgeBaseService instance"""
        with patch.dict("os.environ", {"VECTOR_STORE_BASE_DIR": str(temp_vector_store_dir)}):
            service = KnowledgeBaseService()
            # Mock embeddings and LLM to avoid actual API calls
            service.embeddings = Mock()
            service.llm = Mock()
            return service

    def test_get_vector_store_path(self, service: KnowledgeBaseService):
        """Test getting vector store path"""
        path = service.get_vector_store_path("Test Company")
        assert isinstance(path, Path)
        assert "Test_Company" in str(path)

    def test_get_vector_store_path_normalization(self, service: KnowledgeBaseService):
        """Test that company name is normalized for filesystem"""
        path1 = service.get_vector_store_path("Test/Company")
        path2 = service.get_vector_store_path("Test Company")
        
        assert "Test_Company" in str(path1)
        assert "Test_Company" in str(path2)

    @patch("api.services.knowledge_base_service.PyPDFLoader")
    @patch("api.services.knowledge_base_service.RecursiveCharacterTextSplitter")
    @patch("api.services.knowledge_base_service.Chroma")
    def test_upload_and_process_pdf_success(
        self,
        mock_chroma,
        mock_splitter,
        mock_loader,
        service: KnowledgeBaseService,
        sample_pdf_file,
    ):
        """Test successful PDF processing"""
        # Setup mocks
        mock_doc1 = MagicMock()
        mock_doc1.page_content = "Test content page 1"
        mock_doc2 = MagicMock()
        mock_doc2.page_content = "Test content page 2"
        
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [mock_doc1, mock_doc2]
        mock_loader.return_value = mock_loader_instance
        
        mock_splitter_instance = Mock()
        mock_splitter_instance.split_documents.return_value = [
            mock_doc1,
            mock_doc2,
        ]
        mock_splitter.return_value = mock_splitter_instance
        
        mock_vector_store = Mock()
        mock_chroma.from_documents.return_value = mock_vector_store
        
        # Execute
        result = service.upload_and_process_pdf(
            str(sample_pdf_file), "TestCompany", "Test description"
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["document_count"] == 2
        assert result["chunk_count"] == 2
        assert "vector_store_path" in result
        mock_loader_instance.load.assert_called_once()
        mock_chroma.from_documents.assert_called_once()

    @patch("api.services.knowledge_base_service.PyPDFLoader")
    def test_upload_and_process_pdf_empty(self, mock_loader, service: KnowledgeBaseService, sample_pdf_file):
        """Test processing empty PDF"""
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = []
        mock_loader.return_value = mock_loader_instance
        
        with pytest.raises(Exception) as exc_info:
            service.upload_and_process_pdf(str(sample_pdf_file), "TestCompany")
        
        assert "empty" in str(exc_info.value).lower()

    def test_check_company_knowledge_base_exists(
        self, service: KnowledgeBaseService, temp_vector_store_dir
    ):
        """Test checking if knowledge base exists"""
        company_name = "TestCompany"
        
        # Should not exist initially
        assert not service.check_company_knowledge_base_exists(company_name)
        
        # Create directory to simulate existence
        vector_store_path = service.get_vector_store_path(company_name)
        vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # Should exist now
        assert service.check_company_knowledge_base_exists(company_name)

    @patch("api.services.knowledge_base_service.Chroma")
    @patch("api.services.knowledge_base_service.RetrievalQA")
    def test_answer_question_success(
        self,
        mock_qa_chain,
        mock_chroma,
        service: KnowledgeBaseService,
        temp_vector_store_dir,
    ):
        """Test answering a question"""
        company_name = "TestCompany"
        question = "What is your policy?"
        
        # Create vector store directory
        vector_store_path = service.get_vector_store_path(company_name)
        vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # Setup mocks
        mock_vector_store = Mock()
        mock_retriever = Mock()
        mock_vector_store.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vector_store
        
        mock_qa_instance = Mock()
        mock_result = {
            "result": "This is a test answer",
            "source_documents": [
                MagicMock(
                    page_content="Source content 1",
                    metadata={"page": 1}
                ),
                MagicMock(
                    page_content="Source content 2",
                    metadata={"page": 2}
                ),
            ],
        }
        mock_qa_instance.invoke.return_value = mock_result
        mock_qa_chain.from_chain_type.return_value = mock_qa_instance
        
        # Execute
        result = service.answer_question(company_name, question)
        
        # Assert
        assert result["answer"] == "This is a test answer"
        assert len(result["sources"]) == 2
        assert result["confidence_score"] == 0.8
        mock_qa_instance.invoke.assert_called_once_with({"query": question})

    def test_answer_question_no_knowledge_base(self, service: KnowledgeBaseService):
        """Test answering question when knowledge base doesn't exist"""
        with pytest.raises(Exception) as exc_info:
            service.answer_question("NonExistentCompany", "What is your policy?")
        
        assert "No knowledge base found" in str(exc_info.value)

    def test_delete_company_knowledge_base(
        self, service: KnowledgeBaseService, temp_vector_store_dir
    ):
        """Test deleting company knowledge base"""
        company_name = "TestCompany"
        vector_store_path = service.get_vector_store_path(company_name)
        vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # Should exist before deletion
        assert vector_store_path.exists()
        
        # Delete
        result = service.delete_company_knowledge_base(company_name)
        
        # Should be deleted
        assert result is True
        assert not vector_store_path.exists()

    def test_delete_nonexistent_knowledge_base(self, service: KnowledgeBaseService):
        """Test deleting non-existent knowledge base"""
        result = service.delete_company_knowledge_base("NonExistentCompany")
        assert result is False

