"""
Custom exceptions for the Resume Screener API.

Why custom exceptions instead of generic HTTPException everywhere?
1. Centralized error handling - one place to change error formats
2. Type safety - catch specific errors, not generic Exception
3. Better logging - we can log different errors differently
4. Client-friendly messages - hide internal details from API responses
"""

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from src.core.logging import logger


class ResumeScreenerError(Exception):
    """Base exception for all Resume Screener errors."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class InvalidFileError(ResumeScreenerError):
    """
    Raised when uploaded file fails validation.
    
    This catches both wrong extensions AND invalid magic bytes.
    Common attack: rename malware.exe to resume.pdf
    """
    pass


class PDFParsingError(ResumeScreenerError):
    """
    Raised when pdfplumber fails to extract text.
    
    Usually means corrupted PDF or scanned image without OCR.
    """
    pass


class GeminiAPIError(ResumeScreenerError):
    """
    Raised when Gemini API calls fail after all retries.
    
    This should only bubble up after tenacity exhausts retries,
    so if we see this, something is seriously wrong (quota, key, outage).
    """
    pass


class EmbeddingError(ResumeScreenerError):
    """Raised when embedding generation fails."""
    pass


# === FastAPI Exception Handlers ===
# These convert our custom exceptions into proper HTTP responses

async def resume_screener_error_handler(
    request: Request, 
    exc: ResumeScreenerError
) -> JSONResponse:
    """Handle all ResumeScreener exceptions with consistent format."""
    
    # Log the error with context - escape braces to prevent loguru KeyError
    safe_message = str(exc.message).replace('{', '{{').replace('}', '}}')
    logger.error(
        f"ResumeScreenerError: {safe_message}",
        extra={"details": exc.details, "path": request.url.path}
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
            }
        }
    )


async def invalid_file_error_handler(
    request: Request, 
    exc: InvalidFileError
) -> JSONResponse:
    """Handle file validation errors."""
    
    safe_message = str(exc.message).replace('{', '{{').replace('}', '}}')
    logger.warning(
        f"Invalid file upload attempt: {safe_message}",
        extra={"path": request.url.path}
    )
    
    return JSONResponse(
        status_code=415,  # Unsupported Media Type - more accurate than 400
        content={
            "success": False,
            "error": {
                "type": "InvalidFileError",
                "message": exc.message,
            }
        }
    )


async def gemini_api_error_handler(
    request: Request, 
    exc: GeminiAPIError
) -> JSONResponse:
    """Handle Gemini API failures."""
    
    # Escape braces to prevent loguru KeyError from Gemini's JSON error messages
    safe_message = str(exc.message).replace('{', '{{').replace('}', '}}')
    logger.error(
        f"Gemini API error after retries: {safe_message}",
        extra={"details": exc.details}
    )
    
    return JSONResponse(
        status_code=503,  # Service Unavailable - indicates upstream failure
        content={
            "success": False,
            "error": {
                "type": "GeminiAPIError",
                "message": "AI processing service temporarily unavailable",
                # Don't expose internal error details to clients
            }
        }
    )


async def unhandled_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """
    Catch-all for unhandled exceptions.
    
    This prevents stack traces from leaking to clients.
    We log the full error but return a generic message.
    """
    
    logger.exception(
        f"Unhandled exception on {request.url.path}",
        exc_info=exc
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "type": "InternalError",
                "message": "An unexpected error occurred. Please try again.",
            }
        }
    )
