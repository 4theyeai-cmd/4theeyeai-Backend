import os
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from dotenv import load_dotenv

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from api.database.database import engine, Base, get_db
from api.routes.response_routes import router as response_router
from api.routes.passport_routes import router as passport_router
from api.routes.message_routes import router as message_routes
from api.routes.trip_routes import router as trip_routes
from api.routes import extract_info_routes
from api.services.openai_service import OpenAIService
from api.services.google_sheets_service import GoogleSheetsService

from api.routes.assistant_routes import router as assistant_routes

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    os.environ["OPENAI_API_KEY"] = api_key

# Load environment variables
load_dotenv(override=True)

# Validate required environment variables
REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
    "KNOWLEDGE_SHEET_ID",
    "POSTGRES_PASSWORD",  # Added PostgreSQL password requirement
    "EXTERNAL_EXTRACTINFO_SERVICE_URL",  # Added external service URL requirement
]  # Removed POSTGRES_PASSWORD
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]

if missing_vars:
    raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")

# Initialize FastAPI app
app = FastAPI(
    title="Airport AI Assistant",
    description="An AI-powered assistant that answers questions based on predefined information",
    version="1.0.0",
    redirect_slashes=False,
)

origins = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "https://4theyeai.ir").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # موقت برای dev/Swagger – production حذف کن
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://62.60.213.42:3000",  # IP عمومی سرور
        "https://4theyeai.ir",  # domain production
        "http://4theyeai.ir",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# # CORS Middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Try to create DB tables, but don't fail if database is not available
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")
except Exception as e:
    logger.warning(f"Could not initialize database: {e}")
    logger.info("Application will continue without persistent database")

# Include API routes
app.include_router(response_router, prefix="/api/v1", tags=["responses"])
app.include_router(passport_router, prefix="/api/v1", tags=["passport"])
app.include_router(message_routes, prefix="/api/v1", tags=["messages"])
app.include_router(trip_routes, prefix="/api/v1", tags=["trip"])
app.include_router(extract_info_routes.router, prefix="/api/v1", tags=["extract-info"])
app.include_router(assistant_routes, prefix="/api/v1/aiassistant", tags=["aiassistant"])


@app.get("/")
async def root():
    """Check application and services status."""
    status = {
        "status": "running",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "connections": {
            "database": "checking...",
            "openai": "checking...",
            "google_sheets": "checking...",
        },
    }

    # DB connection test
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        status["connections"]["database"] = "connected"
    except Exception as e:
        status["connections"]["database"] = f"not available: {e}"

    # OpenAI test
    try:
        _ = OpenAIService()
        status["connections"]["openai"] = "configured"
    except Exception as e:
        status["connections"]["openai"] = f"error: {e}"

    # Google Sheets test
    try:
        sheets_service = GoogleSheetsService()
        sheets_service.get_sheet_data()
        status["connections"]["google_sheets"] = "connected"
    except Exception as e:
        status["connections"]["google_sheets"] = f"error: {e}"

    return status
