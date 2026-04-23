"""
Fairness service - detects potential bias in resume screening.

This module implements fairness checks to ensure the screening
process doesn't discriminate based on protected characteristics.

Why fairness matters:
1. Legal compliance (EEOC, GDPR)
2. Ethical AI practices
3. Better hiring outcomes through diverse talent
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from src.core.logging import logger
from src.schemas.resume import ExtractedResume


@dataclass
class FairnessReport:
    """Results of fairness analysis."""
    
    fairness_score: float  # 0-100, higher is better
    potential_issues: list[str]
    recommendations: list[str]
    bias_indicators_found: list[str]
    is_fair: bool  # True if score >= 80


# Protected characteristic indicators (we should NOT use these for scoring)
# These are used ONLY to detect if bias might be present
NAME_GENDER_INDICATORS = [
    # Common gendered name patterns (for detection, not discrimination)
]

# Age-related terms that might indicate bias
AGE_INDICATORS = [
    "years old", "age:", "dob:", "date of birth", "born in",
]

# Identity-related terms
IDENTITY_INDICATORS = [
    "married", "single", "children", "spouse", "religion",
    "nationality", "ethnicity", "race", "gender", "sex",
    "photo", "picture",
]

# Gap penalty terms (can unfairly penalize caregivers)
GAP_PENALTY_INDICATORS = [
    "career gap", "employment gap", "time off",
]


def analyze_fairness(
    extracted_resume: ExtractedResume,
    job_description: str,
    similarity_score: float,
) -> FairnessReport:
    """
    Analyze the screening process for potential fairness issues.
    
    This checks:
    1. Resume doesn't contain protected characteristics being used
    2. JD doesn't have biased requirements
    3. Scoring is based on relevant criteria only
    """
    issues = []
    recommendations = []
    bias_indicators = []
    
    resume_text = extracted_resume.raw_text_cleaned.lower()
    jd_lower = job_description.lower()
    
    # Check 1: Age-related indicators in JD
    for indicator in AGE_INDICATORS:
        if indicator in jd_lower:
            bias_indicators.append(f"JD contains age-related term: '{indicator}'")
            issues.append("Job description may contain age-related requirements")
    
    # Check 2: Identity indicators in JD that shouldn't be requirements
    for indicator in IDENTITY_INDICATORS:
        if indicator in jd_lower:
            bias_indicators.append(f"JD contains identity term: '{indicator}'")
            issues.append("Job description may reference personal identity characteristics")
    
    # Check 3: Check for "culture fit" (often a bias proxy)
    if "culture fit" in jd_lower or "cultural fit" in jd_lower:
        issues.append("'Culture fit' requirement detected - can be a proxy for bias")
        recommendations.append("Consider replacing 'culture fit' with specific, measurable traits")
    
    # Check 4: Unreasonable experience requirements
    exp_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", jd_lower)
    if exp_match:
        years_required = int(exp_match.group(1))
        if years_required > 10:
            issues.append(f"High experience requirement ({years_required}+ years) may exclude qualified candidates")
            recommendations.append("Consider if experience requirement is truly necessary for the role")
    
    # Check 5: "Recent graduate" or age-limiting terms
    if any(term in jd_lower for term in ["recent graduate", "new graduate", "fresh graduate"]):
        issues.append("'Recent graduate' requirement may discriminate by age")
        recommendations.append("Consider 'entry-level' instead of 'recent graduate'")
    
    # Check 6: School prestige bias
    prestigious_schools = ["ivy league", "oxbridge", "top-tier", "top university"]
    for school in prestigious_schools:
        if school in jd_lower:
            issues.append(f"Preference for '{school}' may introduce socioeconomic bias")
    
    # Check 7: Verify scoring is skills-based
    resume_skills = extracted_resume.technical_skills + extracted_resume.soft_skills
    if len(resume_skills) > 0 and similarity_score < 0.3:
        issues.append("Low score despite having skills - verify scoring is skills-based")
        recommendations.append("Review if score is based on relevant qualifications")
    
    # Calculate fairness score
    base_score = 100
    penalty_per_issue = 10
    fairness_score = max(0, base_score - len(issues) * penalty_per_issue)
    
    # Generate recommendations
    if not recommendations:
        if fairness_score >= 90:
            recommendations.append("No significant fairness concerns detected")
        else:
            recommendations.append("Review flagged items to ensure unbiased evaluation")
    
    # Add general best practices
    if fairness_score < 100:
        recommendations.append("Focus evaluation on demonstrated skills and relevant experience")
        recommendations.append("Apply consistent criteria across all candidates")
    
    logger.info(f"Fairness analysis: score={fairness_score}, issues={len(issues)}")
    
    return FairnessReport(
        fairness_score=fairness_score,
        potential_issues=issues,
        recommendations=recommendations,
        bias_indicators_found=bias_indicators,
        is_fair=fairness_score >= 80,
    )


def check_jd_fairness(job_description: str) -> dict[str, Any]:
    """
    Quick fairness check on just the job description.
    
    Returns a summary of potential bias issues.
    """
    jd_lower = job_description.lower()
    issues = []
    
    # Check for age indicators
    if any(term in jd_lower for term in AGE_INDICATORS):
        issues.append("Contains age-related requirements")
    
    # Check for identity indicators
    if any(term in jd_lower for term in IDENTITY_INDICATORS):
        issues.append("References personal identity characteristics")
    
    # Check for culture fit
    if "culture fit" in jd_lower:
        issues.append("Uses 'culture fit' (potential bias proxy)")
    
    # Check for unreasonable experience
    exp_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", jd_lower)
    if exp_match and int(exp_match.group(1)) > 10:
        issues.append(f"Very high experience requirement ({exp_match.group(1)}+ years)")
    
    is_fair = len(issues) == 0
    
    return {
        "is_fair": is_fair,
        "issues": issues,
        "fairness_score": max(0, 100 - len(issues) * 15),
    }
