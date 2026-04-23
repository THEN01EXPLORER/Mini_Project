"""
Resume Screener API - Main Application Entry Point.

This is the FastAPI application factory with:
- Lifespan event for model preloading (not reloaded per request)
- SlowAPI rate limiting (prevents API abuse)
- Custom exception handlers (clean error responses)
- CORS middleware (if needed for web frontends)

Run with: uvicorn src.main:app --reload
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.api.routes import screen_router, rank_router
from src.auth.routes import router as auth_router
from src.core.config import get_settings
from src.core.exceptions import (
    ResumeScreenerError,
    InvalidFileError,
    GeminiAPIError,
    resume_screener_error_handler,
    invalid_file_error_handler,
    gemini_api_error_handler,
    unhandled_exception_handler,
)
from src.core.logging import setup_logging, logger
from src.services.embedding_service import initialize_embedding_model
from src.database import init_db


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    
    Runs once at startup (before any requests) and once at shutdown.
    We use this to:
    1. Configure logging
    2. Load the embedding model INTO MEMORY (avoid per-request loading)
    
    Why lifespan instead of @app.on_event("startup")?
    - on_event is deprecated in FastAPI 0.100+
    - lifespan gives us proper async context management
    - Cleaner resource cleanup on shutdown
    """
    # === STARTUP ===
    settings = get_settings()
    
    # Configure logging first
    setup_logging(level=settings.log_level)
    logger.info("Resume Screener API starting up...")
    
    # Load embedding model into memory
    # This takes 2-5 seconds but only happens ONCE at startup
    logger.info("Loading embedding model (this may take a few seconds)...")
    try:
        initialize_embedding_model()
        logger.info("Embedding model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
    
    # Initialize database
    logger.info("Initializing user database...")
    init_db()
    logger.info("Database ready")
    
    logger.info("Resume Screener API ready for requests")
    
    yield  # Application runs here
    
    # === SHUTDOWN ===
    logger.info("Resume Screener API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Resume Screener API",
    description="""
    Production-grade Resume Screening & Ranking API.
    
    Upload a PDF resume and job description to get:
    - Similarity score (0-1)
    - Extracted skills and experience
    - Gap analysis showing what the candidate is missing
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# === MIDDLEWARE ===

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - fully permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Disabled to allow wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)


# === EXCEPTION HANDLERS ===
# Order matters - more specific handlers first

app.add_exception_handler(InvalidFileError, invalid_file_error_handler)
app.add_exception_handler(GeminiAPIError, gemini_api_error_handler)
app.add_exception_handler(ResumeScreenerError, resume_screener_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


# === ROUTES ===

app.include_router(auth_router)  # Auth routes (public)
app.include_router(screen_router)
app.include_router(rank_router)


# Root endpoint for quick verification
@app.get("/", tags=["root"])
async def root() -> dict:
    """Root endpoint with API info."""
    return {
        "service": "Resume Screener API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
