"""
Pytest configuration and shared fixtures
"""
import os
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from api.database.database import Base, get_db
from api.app import app


# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test database engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    Create a fresh database for each test.
    """
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    db = TestSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Drop tables
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with dependency overrides.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def temp_vector_store_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for vector stores.
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def temp_pdf_uploads_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for PDF uploads.
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def mock_openai_key(monkeypatch):
    """
    Mock OpenAI API key for testing.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    yield "test-openai-key"


@pytest.fixture(scope="function")
def sample_pdf_content() -> bytes:
    """
    Create a minimal valid PDF content for testing.
    """
    # Minimal PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
400
%%EOF"""
    return pdf_content


@pytest.fixture(scope="function")
def sample_pdf_file(tmp_path: Path, sample_pdf_content: bytes) -> Path:
    """
    Create a sample PDF file for testing.
    """
    pdf_file = tmp_path / "test_document.pdf"
    pdf_file.write_bytes(sample_pdf_content)
    return pdf_file


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, temp_vector_store_dir, temp_pdf_uploads_dir):
    """
    Setup test environment variables.
    """
    monkeypatch.setenv("VECTOR_STORE_BASE_DIR", str(temp_vector_store_dir))
    monkeypatch.setenv("PDF_UPLOADS_DIR", str(temp_pdf_uploads_dir))
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    yield
    # Cleanup happens automatically via fixtures

