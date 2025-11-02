from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from api.database.database import get_db
from api.services.knowledge_base_service import KnowledgeBaseService
from api.services.company_document_service import CompanyDocumentService
from api.schemas.company_document_schema import (
    CompanyDocument,
    QuestionRequest,
    QuestionResponse,
)

router = APIRouter()

knowledge_base_service = KnowledgeBaseService()
company_document_service = CompanyDocumentService()


@router.post("/knowledge-base/upload", response_model=CompanyDocument)
async def upload_pdf(
    company_name: str = Form(...),
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF file for a company and process it into vector database.

    Args:
        company_name: Name of the company
        file: PDF file to upload
        description: Optional description
        db: Database session
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="File must be a PDF (.pdf)")

        # Read file content
        file_content = await file.read()

        # Validate PDF content (basic check)
        if not file_content.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="Invalid PDF file format")

        # Save file
        file_path = company_document_service.save_uploaded_file(
            file_content=file_content,
            company_name=company_name,
            file_name=file.filename,
        )

        # Process PDF and create vector store
        vector_store_info = knowledge_base_service.upload_and_process_pdf(
            file_path=file_path, company_name=company_name, description=description
        )

        # Create database record
        db_document = company_document_service.create_document_record(
            db=db,
            company_name=company_name,
            file_name=file.filename,
            file_path=file_path,
            vector_store_path=vector_store_info.get("vector_store_path"),
            description=description,
        )

        return db_document

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-base/question", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """
    Ask a question based on company's knowledge base.

    Args:
        request: Question request with company_name and question
        db: Database session
    """
    try:
        # Check if knowledge base exists for company
        if not knowledge_base_service.check_company_knowledge_base_exists(
            request.company_name
        ):
            raise HTTPException(
                status_code=404,
                detail=f"No knowledge base found for company: {request.company_name}. Please upload a PDF first.",
            )

        # Get answer from knowledge base
        result = knowledge_base_service.answer_question(
            company_name=request.company_name, question=request.question
        )

        return QuestionResponse(
            answer=result.get("answer", "پاسخی یافت نشد."),
            company_name=request.company_name,
            sources=result.get("sources"),
            confidence_score=result.get("confidence_score"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/knowledge-base/documents/{company_name}", response_model=List[CompanyDocument]
)
async def get_company_documents(company_name: str, db: Session = Depends(get_db)):
    """Get all documents for a company."""
    try:
        documents = company_document_service.get_documents_by_company(
            db=db, company_name=company_name
        )
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/document/{document_id}", response_model=CompanyDocument)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get a document by ID."""
    try:
        document = company_document_service.get_document_by_id(
            db=db, document_id=document_id
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge-base/document/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document and its associated vector store."""
    try:
        success = company_document_service.delete_document(
            db=db, document_id=document_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"message": "Document deleted successfully", "document_id": document_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge-base/company/{company_name}")
async def delete_company_knowledge_base(
    company_name: str, db: Session = Depends(get_db)
):
    """Delete all documents and vector store for a company."""
    try:
        # Get all documents for company
        documents = company_document_service.get_documents_by_company(
            db=db, company_name=company_name
        )

        # Delete all documents
        for document in documents:
            company_document_service.delete_document(db=db, document_id=document.id)

        # Delete vector store
        knowledge_base_service.delete_company_knowledge_base(company_name)

        return {
            "message": f"All documents and knowledge base deleted for company: {company_name}",
            "company_name": company_name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
