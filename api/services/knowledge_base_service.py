import os
import logging
import shutil
from typing import Optional, List, Dict
from pathlib import Path

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self):
        """Initialize the Knowledge Base Service with LangChain components."""
        self.base_dir = Path(os.getenv("VECTOR_STORE_BASE_DIR", "./vector_stores"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

        logger.info("KnowledgeBaseService initialized")

    def get_vector_store_path(self, company_name: str) -> Path:
        """Get the vector store path for a company."""
        # Normalize company name for filesystem
        safe_company_name = company_name.replace(" ", "_").replace("/", "_")
        return self.base_dir / safe_company_name

    def upload_and_process_pdf(
        self, file_path: str, company_name: str, description: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Upload and process a PDF file, storing it in vector database.

        Args:
            file_path: Path to the uploaded PDF file
            company_name: Name of the company
            description: Optional description

        Returns:
            Dictionary with vector_store_path and metadata
        """
        try:
            logger.info(f"Processing PDF for company: {company_name}")

            # Load PDF document
            loader = PyPDFLoader(file_path)
            documents = loader.load()

            if not documents:
                raise ValueError("PDF file is empty or could not be read")

            logger.info(f"Loaded {len(documents)} pages from PDF")

            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            splits = text_splitter.split_documents(documents)

            logger.info(f"Split PDF into {len(splits)} chunks")

            # Get vector store path for this company
            vector_store_path = self.get_vector_store_path(company_name)

            # Create or update vector store
            # If vector store exists, we'll delete and recreate it
            if vector_store_path.exists():
                logger.info(f"Removing existing vector store for {company_name}")
                shutil.rmtree(vector_store_path)

            # Create new vector store
            vector_store = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                persist_directory=str(vector_store_path),
            )

            logger.info(f"Vector store created at: {vector_store_path}")

            return {
                "vector_store_path": str(vector_store_path),
                "document_count": len(documents),
                "chunk_count": len(splits),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
            raise Exception(f"Error processing PDF: {str(e)}")

    def answer_question(self, company_name: str, question: str) -> Dict[str, any]:
        """
        Answer a question using the company's knowledge base.

        Args:
            company_name: Name of the company
            question: User's question

        Returns:
            Dictionary with answer and metadata
        """
        try:
            logger.info(f"Answering question for company: {company_name}")

            # Get vector store path
            vector_store_path = self.get_vector_store_path(company_name)

            if not vector_store_path.exists():
                raise ValueError(
                    f"No knowledge base found for company: {company_name}. "
                    "Please upload a PDF document first."
                )

            # Load existing vector store
            vector_store = Chroma(
                persist_directory=str(vector_store_path),
                embedding_function=self.embeddings,
            )

            # Create retrieval QA chain with custom prompt
            prompt_template = """Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context: {context}

Question: {question}

Answer in Persian (فارسی):"""

            PROMPT = PromptTemplate(
                template=prompt_template, input_variables=["context", "question"]
            )

            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
                chain_type_kwargs={"prompt": PROMPT},
                return_source_documents=True,
            )

            # Get answer
            result = qa_chain.invoke({"query": question})

            # Extract source documents
            source_docs = result.get("source_documents", [])
            sources = []
            if source_docs:
                for doc in source_docs[:3]:  # Top 3 sources
                    sources.append(
                        {
                            "page": doc.metadata.get("page", "unknown"),
                            "content": (
                                doc.page_content[:200] + "..."
                                if len(doc.page_content) > 200
                                else doc.page_content
                            ),
                        }
                    )

            return {
                "answer": result.get("result", "پاسخی یافت نشد."),
                "sources": sources,
                "confidence_score": 0.8,  # Placeholder, can be improved
            }

        except Exception as e:
            logger.error(f"Error answering question: {str(e)}", exc_info=True)
            raise Exception(f"Error answering question: {str(e)}")

    def delete_company_knowledge_base(self, company_name: str) -> bool:
        """
        Delete vector store for a company.

        Args:
            company_name: Name of the company

        Returns:
            True if deleted successfully
        """
        try:
            vector_store_path = self.get_vector_store_path(company_name)

            if vector_store_path.exists():
                shutil.rmtree(vector_store_path)
                logger.info(f"Deleted vector store for company: {company_name}")
                return True
            else:
                logger.warning(f"Vector store not found for company: {company_name}")
                return False

        except Exception as e:
            logger.error(f"Error deleting vector store: {str(e)}", exc_info=True)
            raise Exception(f"Error deleting vector store: {str(e)}")

    def check_company_knowledge_base_exists(self, company_name: str) -> bool:
        """Check if a knowledge base exists for a company."""
        vector_store_path = self.get_vector_store_path(company_name)
        return vector_store_path.exists()
