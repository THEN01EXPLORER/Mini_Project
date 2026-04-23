"""
Batch ranking endpoint - compare multiple resumes against one job description.

This enables "transparent candidate rankings" as required by the project spec.
"""

from __future__ import annotations

import asyncio
import time
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from pydantic import BaseModel

from src.core.exceptions import ResumeScreenerError
from src.core.logging import logger
from src.schemas.response import APIResponse
from src.schemas.resume import ExtractedResume
from src.services.pdf_parser import parse_pdf
from src.services.gemini_service import extract_resume_data
from src.services.ranking_service import analyze_resume
from src.services.fairness_service import analyze_fairness, check_jd_fairness
from src.auth.dependencies import get_current_user
from src.auth.models import User
from fastapi import Depends

router = APIRouter(prefix="/api/v1", tags=["ranking"])


class CandidateResult(BaseModel):
    """Result for a single candidate in batch ranking."""
    
    rank: int
    candidate_name: str | None
    filename: str
    similarity_score: float
    skill_match_count: int
    missing_skills: list[str]
    experience_years: float | None
    fairness_score: float
    summary: str


class BatchRankingResult(BaseModel):
    """Result of batch resume ranking."""
    
    job_description_fairness: dict
    candidates: list[CandidateResult]
    total_processed: int
    processing_time_ms: int


@router.post("/rank")
async def rank_resumes(
    files: Annotated[list[UploadFile], File(description="Multiple resume PDFs")],
    job_description: Annotated[str, Form(description="Job description to match against")],
    current_user: User = Depends(get_current_user),
) -> APIResponse:
    """
    Rank multiple resumes against a job description.
    
    Upload 2-10 resume PDFs and get a ranked list of candidates
    with scores, skill matches, and fairness checks.
    """
    start_time = time.time()
    
    # Validate inputs
    if len(files) < 1:
        raise HTTPException(400, "At least 1 resume is required")
    
    if len(files) > 10:
        raise HTTPException(400, "Maximum 10 resumes per batch")
    
    if len(job_description.strip()) < 10:
        raise HTTPException(400, "Job description too short")
    
    logger.info(f"Batch ranking: {len(files)} resumes")
    
    # Check JD fairness first
    jd_fairness = check_jd_fairness(job_description)
    
    # helper for processing a single resume
    async def process_single_resume(file: UploadFile) -> dict:
        try:
            # Validate file type
            if not file.filename or not file.filename.lower().endswith('.pdf'):
                logger.warning(f"Skipping non-PDF file: {file.filename}")
                return None
            
            # Read file content (Async IO)
            content = await file.read()
            
            # Run blocking CPU/Network tasks in thread pool to avoid blocking event loop
            # 1. Parse PDF
            resume_text = await asyncio.to_thread(parse_pdf, content, file.filename)
            
            # 2. Extract Data (Gemini API - Blocking Network IO)
            extracted = await asyncio.to_thread(extract_resume_data, resume_text)
            
            # 3. Analyze (CPU bound)
            similarity_score, gap_analysis, _ = await asyncio.to_thread(
                analyze_resume, extracted, job_description
            )
            
            # 4. Fairness (CPU bound)
            fairness = analyze_fairness(extracted, job_description, similarity_score)
            
            all_skills = extracted.technical_skills + extracted.soft_skills
            
            return {
                "filename": file.filename,
                "candidate_name": extracted.candidate_name,
                "similarity_score": similarity_score,
                "skill_match_count": len(all_skills),
                "missing_skills": gap_analysis.missing_skills[:5],
                "experience_years": extracted.total_experience_years,
                "fairness_score": fairness.fairness_score,
                "summary": gap_analysis.summary,
            }
            
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {e}")
            return {
                "filename": file.filename or "unknown",
                "candidate_name": None,
                "similarity_score": 0.0,
                "skill_match_count": 0,
                "missing_skills": [],
                "experience_years": None,
                "fairness_score": 0.0,
                "summary": f"Error processing: {str(e)}",
            }

    # Limit concurrency to 5 (a balance between speed and free-tier rate limits)
    semaphore = asyncio.Semaphore(5)

    async def process_with_limit(file: UploadFile) -> dict:
        async with semaphore:
            return await process_single_resume(file)

    # Run all processing tasks in parallel (throttled)
    results = await asyncio.gather(*[process_with_limit(f) for f in files])
    
    # Filter out None results (skipped files)
    candidates = [r for r in results if r is not None]
    
    # Sort by similarity score (descending) and assign ranks
    candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    ranked_candidates = []
    for i, candidate in enumerate(candidates, 1):
        ranked_candidates.append(CandidateResult(
            rank=i,
            **candidate
        ))
    
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    result = BatchRankingResult(
        job_description_fairness=jd_fairness,
        candidates=ranked_candidates,
        total_processed=len(ranked_candidates),
        processing_time_ms=processing_time_ms,
    )
    
    logger.info(f"Batch ranking complete: {len(ranked_candidates)} candidates in {processing_time_ms}ms")
    
    return APIResponse(
        success=True,
        result=result.model_dump(),
    )
