"""
Resume screening endpoint.

POST /api/v1/screen - The main endpoint for resume screening.
Accepts a PDF file and job description, returns similarity score + gap analysis.
"""

import time
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.config import get_settings
from src.core.exceptions import InvalidFileError
from src.core.logging import logger
from src.schemas.response import ScreeningResponse, ScreeningResult, ErrorDetail
from src.services.pdf_parser import parse_pdf
from src.services.gemini_service import extract_resume_data
from src.services.ranking_service import analyze_resume
from src.services.ranking_service import analyze_resume
from src.services.fairness_service import analyze_fairness
from src.auth.dependencies import get_current_user
from src.auth.models import User


router = APIRouter(prefix="/api/v1", tags=["screening"])

# Rate limiter - uses IP address by default
limiter = Limiter(key_func=get_remote_address)


def validate_upload_file(file: UploadFile) -> None:
    """
    Validate uploaded file before processing.
    
    Checks:
    1. File has a filename
    2. Filename ends with .pdf (first line of defense)
    3. Content type looks like PDF
    
    Note: Magic byte validation happens later in parse_pdf()
    because we need to read the content first.
    """
    if not file.filename:
        raise InvalidFileError("No filename provided")
    
    if not file.filename.lower().endswith(".pdf"):
        raise InvalidFileError(
            f"File must be a PDF. Got: {file.filename}",
            details={"filename": file.filename}
        )
    
    # Content-type check (browsers usually set this)
    if file.content_type and "pdf" not in file.content_type.lower():
        logger.warning(
            f"Suspicious content-type: {file.content_type} for {file.filename}"
        )
        # Don't reject yet - let magic byte check be the final arbiter


@router.post(
    "/screen",
    response_model=ScreeningResponse,
    summary="Screen a resume against a job description",
    description="""
    Upload a PDF resume and provide a job description text.
    Returns a similarity score, extracted skills, and gap analysis.
    
    **Rate limited** to prevent abuse.
    """,
)
@limiter.limit("10/minute")  # Rate limit per IP
async def screen_resume(
    request: Request,  # Required by slowapi
    file: Annotated[
        UploadFile,
        File(description="Resume PDF file (max 10MB)")
    ],
    job_description: Annotated[
        str,
        Form(
            description="Job description text to match against",
            min_length=50,
            max_length=10000,
        )
    ],
) -> ScreeningResponse:
    """
    Screen a resume against a job description.
    
    Pipeline:
    1. Validate PDF file (extension + magic bytes)
    2. Extract text from PDF
    3. Use Gemini to extract structured data
    4. Generate embeddings for resume and JD
    5. Calculate similarity score
    6. Perform gap analysis
    
    Returns structured response with:
    - similarity_score (0-1)
    - extracted_data (skills, experience, education)
    - gap_analysis (missing skills, experience gaps)
    """
    start_time = time.time()
    
    logger.info(f"Screening request: file={file.filename}, jd_length={len(job_description)}")
    
    # Step 1: Basic validation
    validate_upload_file(file)
    
    # Step 2: Read file content
    content = await file.read()
    logger.debug(f"Read {len(content)} bytes from upload")
    
    # Step 3: Parse PDF (includes magic byte validation)
    resume_text = parse_pdf(content, filename=file.filename or "resume.pdf")
    
    # Step 4: Extract structured data via Gemini
    extracted_data = extract_resume_data(resume_text)
    
    # Step 5-6: Analyze resume (embeddings + similarity + gap analysis)
    similarity_score, gap_analysis, analysis_time_ms = analyze_resume(
        extracted_data,
        job_description,
    )
    
    total_time_ms = int((time.time() - start_time) * 1000)
    
    # Step 7: Fairness check
    fairness = analyze_fairness(extracted_data, job_description, similarity_score)
    
    logger.info(
        f"Screening complete: score={similarity_score:.3f}, "
        f"fairness={fairness.fairness_score}, "
        f"time={total_time_ms}ms, "
        f"candidate={extracted_data.candidate_name or 'Unknown'}"
    )
    
    return ScreeningResponse(
        success=True,
        result=ScreeningResult(
            similarity_score=similarity_score,
            extracted_data=extracted_data,
            gap_analysis=gap_analysis,
            processing_time_ms=total_time_ms,
            fairness_score=fairness.fairness_score,
            fairness_issues=fairness.potential_issues,
        ),
        model_version="1.0.0",
    )


@router.get(
    "/health",
    summary="Health check",
    description="Basic health check endpoint for monitoring",
)
async def health_check() -> dict:
    """Simple health check."""
    return {
        "status": "healthy",
        "service": "resume-screener",
        "version": "1.0.0",
    }
