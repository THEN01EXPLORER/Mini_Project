"""
Gemini API service for structured resume extraction.

Why tenacity for retries instead of manual retry loops?
1. Exponential backoff is tricky to implement correctly
2. Jitter prevents thundering herd when multiple requests retry together
3. Retry conditions are declarative, not buried in if-else spaghetti
4. I've debugged too many infinite retry loops at 3 AM

This module handles all Gemini API interactions with proper resilience.
"""

import json
from typing import Any

import google.generativeai as genai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from src.core.config import get_settings
from src.core.exceptions import GeminiAPIError
from src.core.logging import logger
from src.schemas.resume import ExtractedResume


# Initialize Gemini client at module level
# (will be configured on first use)
_client_configured = False


def _ensure_client_configured() -> None:
    """Lazily configure Gemini client on first use."""
    global _client_configured
    if not _client_configured:
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        _client_configured = True
        logger.info(f"Gemini client configured for model: {settings.gemini_model}")


# The extraction prompt - carefully crafted to get consistent, accurate JSON output
# Note: Gemini Flash is surprisingly good at following JSON schemas
# IMPORTANT: Double braces {{ }} are used to escape literal braces in .format()
EXTRACTION_PROMPT = """
You are an expert resume parser for a hiring system. Extract structured information with HIGH ACCURACY.

CRITICAL RULES FOR EXTRACTION (Follow these in order):
1. **THE "EXPLICIT MENTION" RULE (Fixes Hallucinations):**
   - Look for an explicit summary statement first (e.g., "Over 8 years of experience", "5+ years in Python").
   - If found, use this number immediately as `total_experience_years`. Do NOT attempt to calculate dates manually if this exists.

2. **THE "STUDENT" RULE (Fixes "Exp Unknown" / "48y exp"):**
   - Check the "Education" section. If the graduation year is in the future (e.g., > 2025) OR if the current title is "Student", strictly set `total_experience_years` to 0.0.
   - Internships do NOT count towards `total_experience_years` for students.

3. **THE "PRESENT" DATE RULE (Fixes Math Errors):**
   - If you must calculate experience from dates:
   - Treat "Present", "Current", or "Now" as the year 2026.
   - Formula: (End Year - Start Year).
   - Do NOT sum up overlapping dates.

4. **SKILL EXTRACTION:**
   - Extract EVERY technical skill, tool, framework, and technology mentioned.
   - Normalize skill names (e.g., "ReactJS" -> "React").

Respond with ONLY a valid JSON object:

{{
    "candidate_name": "string or null",
    "email": "string or null",
    "phone": "string or null",
    "location": "string or null",
    "technical_skills": ["skill1", "skill2", ...],
    "soft_skills": ["skill1", "skill2", ...],
    "is_student": boolean,
    "total_experience_years": number or null (0.0 for students),
    "extraction_reasoning": "string (Explain how you derived the years)",
    "work_history": [
        {{
            "title": "string",
            "company": "string or null",
            "duration_months": number or null,
            "key_technologies": ["tech1", "tech2", ...]
        }}
    ],
    "education": [
        {{
            "degree": "string",
            "field": "string or null",
            "institution": "string or null",
            "graduation_year": number or null
        }}
    ],
    "certifications": ["cert1", "cert2", ...],
    "projects": [
        {{
            "name": "string",
            "technologies": ["tech1", "tech2", ...]
        }}
    ]
}}

Resume text:
---
{resume_text}
---
"""


class GeminiRateLimitError(Exception):
    """Raised when Gemini returns 429 Too Many Requests."""
    pass


def _should_retry(exception: Exception) -> bool:
    """Determine if we should retry based on exception type."""
    # Retry on rate limits and transient errors
    if isinstance(exception, GeminiRateLimitError):
        return True
    # Also retry on generic API errors (might be transient)
    if isinstance(exception, genai.types.BlockedPromptException):
        return False  # Don't retry content policy violations
    return True


@retry(
    # Stop after 7 attempts (initial + 6 retries) to give quota time to reset
    stop=stop_after_attempt(7),
    
    # Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s
    wait=wait_exponential(multiplier=1, min=2, max=30),
    
    # Only retry on specific exceptions
    retry=retry_if_exception_type((GeminiRateLimitError, Exception)),
    
    # Don't retry immediately on success
    reraise=True,
)
def _call_gemini_with_retry(prompt: str) -> str:
    """
    Call Gemini API with automatic retry on failures.
    
    The @retry decorator handles:
    - 429 rate limit errors with exponential backoff
    - Transient network failures
    - Temporary API outages
    
    Args:
        prompt: Full prompt to send to Gemini
        
    Returns:
        Raw response text from Gemini
        
    Raises:
        GeminiAPIError: After all retries exhausted
    """
    _ensure_client_configured()
    settings = get_settings()
    
    try:
        model = genai.GenerativeModel(settings.gemini_model)
        response = model.generate_content(prompt)
        
        # Check for safety blocks
        if not response.parts:
            raise GeminiAPIError(
                "Gemini returned empty response (possibly blocked by safety filters)",
                details={"prompt_preview": prompt[:200]}
            )
        
        return response.text
        
    except genai.types.BlockedPromptException as e:
        # Don't retry content policy violations
        raise GeminiAPIError(
            "Prompt blocked by Gemini safety filters",
            details={"error": str(e)}
        )
        
    except Exception as e:
        error_str = str(e).lower()
        
        # Detect rate limiting
        if "429" in error_str or "quota" in error_str or "rate" in error_str:
            # Escape braces to prevent loguru KeyError
            safe_error = str(e).replace('{', '{{').replace('}', '}}')
            logger.warning(f"Gemini rate limited, will retry: {safe_error}")
            raise GeminiRateLimitError(str(e))
        
        # Other errors - log and re-raise for retry
        safe_error = str(e).replace('{', '{{').replace('}', '}}')
        logger.error(f"Gemini API error: {safe_error}")
        raise


def _parse_json_response(response_text: str) -> dict[str, Any]:
    """
    Parse JSON from Gemini response.
    
    Gemini sometimes wraps JSON in markdown code blocks,
    so we handle that gracefully.
    """
    text = response_text.strip()
    
    # Remove markdown code block if present
    if text.startswith("```"):
        # Find the end of the code block
        lines = text.split("\n")
        # Skip first line (```json) and last line (```)
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON response: {e}")
        logger.debug(f"Raw response: {response_text[:500]}")
        raise GeminiAPIError(
            "Failed to parse structured data from Gemini response",
            details={"parse_error": str(e)}
        )


def _safe_extract_work_history(items: Any) -> list[dict]:
    """Safely extract work history items."""
    if not isinstance(items, list):
        return []
    result = []
    for w in items:
        if not isinstance(w, dict):
            continue
        try:
            result.append({
                "title": str(w.get("title", "Unknown")),
                "company": str(w.get("company")) if w.get("company") else None,
                "duration_months": int(w.get("duration_months")) if w.get("duration_months") else None,
            })
        except Exception:
            continue
    return result


def _safe_extract_education(items: Any) -> list[dict]:
    """Safely extract education items."""
    if not isinstance(items, list):
        return []
    result = []
    for e in items:
        if not isinstance(e, dict):
            continue
        try:
            result.append({
                "degree": str(e.get("degree", "Unknown")),
                "field": str(e.get("field")) if e.get("field") else None,
                "institution": str(e.get("institution")) if e.get("institution") else None,
                "graduation_year": int(e.get("graduation_year")) if e.get("graduation_year") else None,
            })
        except Exception:
            continue
    return result


def extract_resume_data(resume_text: str) -> ExtractedResume:
    """
    Extract structured data from resume text using Gemini.
    
    Args:
        resume_text: Cleaned text content from PDF
        
    Returns:
        ExtractedResume with parsed fields
        
    Raises:
        GeminiAPIError: If extraction fails after retries
    """
    if not resume_text or len(resume_text.strip()) < 50:
        raise GeminiAPIError(
            "Resume text too short for meaningful extraction",
            details={"text_length": len(resume_text) if resume_text else 0}
        )
    
    logger.info(f"Extracting structured data from resume ({len(resume_text)} chars)")
    
    # Build prompt
    prompt = EXTRACTION_PROMPT.format(resume_text=resume_text[:8000])  # Truncate very long resumes
    
    try:
        # Call Gemini (with retries)
        response_text = _call_gemini_with_retry(prompt)
        
        # Parse JSON response
        data = _parse_json_response(response_text)
        logger.info(f"DEBUG: Parsed Gemini Data: {json.dumps(data, indent=2)}")
        
        # Validate against our Pydantic model
        extracted = ExtractedResume(
            candidate_name=data.get("candidate_name"),
            technical_skills=data.get("technical_skills", []),
            soft_skills=data.get("soft_skills", []),
            total_experience_years=data.get("total_experience_years"),
            is_student=data.get("is_student", False),
            extraction_reasoning=data.get("extraction_reasoning"),
            work_history=_safe_extract_work_history(data.get("work_history", [])),
            education=_safe_extract_education(data.get("education", [])),
            raw_text_cleaned=resume_text,
        )
        
        logger.info(
            f"Extracted: {len(extracted.technical_skills)} technical skills, "
            f"{len(extracted.work_history)} jobs, "
            f"{extracted.total_experience_years or 'unknown'} years experience"
        )
        
        return extracted
        
    except GeminiAPIError:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.exception(f"Unexpected error during extraction: {e}")
        raise GeminiAPIError(
            f"Resume extraction failed: {repr(e)}",
            details={"error_type": type(e).__name__}
        )
