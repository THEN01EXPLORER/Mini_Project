"""
API response schemas.

Consistent response format across all endpoints.
Every response has success/error structure for easy client handling.
"""

from typing import Annotated, Any

from pydantic import BaseModel, Field

from src.schemas.resume import ExtractedResume, GapAnalysis


class ErrorDetail(BaseModel):
    """Structured error information."""
    
    type: str = Field(description="Error class name")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] | None = Field(default=None)


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    success: bool = Field(default=False)
    error: ErrorDetail


class ScreeningResult(BaseModel):
    """
    Full screening result for a single resume.
    
    This is what recruiters actually care about:
    1. How good is the match? (similarity_score)
    2. What did we find? (extracted_data)
    3. What's missing? (gap_analysis)
    """
    
    # Overall match score - normalized to 0-1 range
    # Higher is better, but we don't use percentages because
    # 0.85 sounds more technical than "85%" 
    similarity_score: Annotated[
        float,
        Field(ge=0.0, le=1.0, description="Cosine similarity between resume and JD")
    ]
    
    # What we extracted from the resume
    extracted_data: ExtractedResume
    
    # Gap analysis - the "value add" over just a score
    gap_analysis: GapAnalysis
    
    # Fairness analysis - ensures unbiased screening
    fairness_score: Annotated[
        float,
        Field(ge=0.0, le=100.0, description="Fairness score (0-100, higher is better)")
    ] = 100.0
    
    fairness_issues: list[str] = Field(
        default_factory=list,
        description="List of potential fairness/bias issues detected"
    )
    
    # Processing metadata - useful for debugging
    processing_time_ms: Annotated[
        int,
        Field(ge=0, description="Total processing time in milliseconds")
    ]


class ScreeningResponse(BaseModel):
    """
    API response for POST /api/v1/screen
    
    We always return success: true/false at the top level
    so clients can do a simple check before parsing the rest.
    """
    
    success: bool = Field(default=True)
    result: ScreeningResult | None = Field(default=None)
    error: ErrorDetail | None = Field(default=None)
    
    # Metadata
    model_version: str = Field(
        default="1.0.0",
        description="API version for client compatibility checks"
    )


class APIResponse(BaseModel):
    """Generic API response wrapper."""
    
    success: bool = Field(default=True)
    result: dict[str, Any] | list[Any] | None = Field(default=None)
    error: ErrorDetail | None = Field(default=None)
    model_version: str = "1.0.0"
