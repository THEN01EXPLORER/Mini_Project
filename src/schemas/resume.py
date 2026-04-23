"""
Resume and extraction schemas.

These Pydantic models define the structure of data flowing through the system.
Using strict typing because silent data corruption is worse than loud failures.
"""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


class Education(BaseModel):
    model_config = ConfigDict(extra='ignore')
    """Single education entry from a resume."""
    
    degree: str = Field(description="Degree name (e.g., 'Bachelor of Science')")
    field: str | None = Field(default=None, description="Field of study")
    institution: str | None = Field(default=None, description="School/university name")
    graduation_year: int | None = Field(default=None, ge=1950, le=2030)


class WorkExperience(BaseModel):
    model_config = ConfigDict(extra='ignore')
    """Single work experience entry."""
    
    title: str = Field(description="Job title")
    company: str | None = Field(default=None, description="Company name")
    duration_months: int | None = Field(
        default=None, 
        ge=0,
        description="Total duration in months (approximate)"
    )
    # Not storing descriptions - we extract skills directly instead
    # because raw descriptions are too noisy for matching


class ExtractedResume(BaseModel):
    model_config = ConfigDict(extra='ignore')
    """
    Structured data extracted from a resume via Gemini.
    
    Fields are intentionally kept flat-ish because deeply nested
    structures are harder to work with in vector similarity later.
    """
    
    # Contact (we don't store PII long-term, but need it for validation)
    candidate_name: str | None = Field(default=None, description="Full name if found")
    
    # Skills - the core of what we match against JD
    technical_skills: Annotated[
        list[str],
        Field(default_factory=list, description="Programming languages, frameworks, tools")
    ]
    soft_skills: Annotated[
        list[str],
        Field(default_factory=list, description="Communication, leadership, etc.")
    ]
    
    # Experience
    is_student: bool = Field(
        default=False,
        description="True if currently a student or graduating in future"
    )
    
    extraction_reasoning: str | None = Field(
        default=None,
        description="Explanation of how years of experience were calculated"
    )

    total_experience_years: float | None = Field(
        default=None,
        ge=0,
        description="Total years of work experience"
    )
    work_history: Annotated[
        list[WorkExperience],
        Field(default_factory=list)
    ]
    
    # Education
    education: Annotated[
        list[Education],
        Field(default_factory=list)
    ]
    
    # Raw text for embedding - we keep this because embeddings work
    # better on full context than on extracted keywords alone
    raw_text_cleaned: str = Field(
        default="",
        description="Cleaned resume text for embedding generation"
    )


class SkillMatch(BaseModel):
    """
    Represents how a candidate skill matches a JD requirement.
    
    We explicitly track match strength because "Python" in resume
    doesn't necessarily mean "5 years Python" in JD requirement.
    """
    
    skill: str
    found_in_resume: bool
    relevance_score: Annotated[
        float,
        Field(ge=0.0, le=1.0, description="Semantic similarity to JD requirement")
    ]


class GapAnalysis(BaseModel):
    """
    Analysis of what the candidate is missing compared to the JD.
    
    This is the "human touch" output - instead of just a score,
    we explain WHY the candidate might not be a fit.
    """
    
    missing_skills: Annotated[
        list[str],
        Field(default_factory=list, description="Skills required by JD but not in resume")
    ]
    partial_matches: Annotated[
        list[SkillMatch],
        Field(default_factory=list, description="Skills with weak/partial matches")
    ]
    experience_gap: str | None = Field(
        default=None,
        description="Description of experience mismatch (e.g., 'JD requires 5 years, candidate has 2')"
    )
    education_gap: str | None = Field(
        default=None,
        description="Description of education mismatch if any"
    )
    
    # Summary for recruiters who don't want to read the details
    summary: str = Field(
        default="",
        description="One-paragraph gap analysis summary"
    )
