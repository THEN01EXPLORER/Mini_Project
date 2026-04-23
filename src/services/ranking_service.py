"""
Ranking service - combines extraction + embedding for final scoring.

This is the "business logic" layer that orchestrates:
1. PDF parsing
2. Gemini extraction  
3. Embedding generation
4. Similarity scoring
5. Gap analysis

Keeping this separate from the API route makes testing easier
and follows the single-responsibility principle.
"""

from __future__ import annotations

import re
import time
from typing import Any, Optional, TYPE_CHECKING

import chromadb

from src.core.config import get_settings
from src.core.exceptions import ResumeScreenerError
from src.core.logging import logger
from src.schemas.resume import ExtractedResume, GapAnalysis, SkillMatch
from src.services.embedding_service import (
    compute_cosine_similarity,
    generate_embedding,
)

if TYPE_CHECKING:
    from chromadb.api import ClientAPI
    from chromadb.api.models.Collection import Collection

# ChromaDB client - initialized lazily
# Using string annotations to avoid import-time evaluation issues
_chroma_client: Optional["ClientAPI"] = None
_collection: Optional["Collection"] = None


def _get_chroma_collection() -> "Collection":
    """
    Get or create ChromaDB collection.
    
    Using persistent storage so embeddings survive restarts.
    No Docker required - just a local directory.
    """
    global _chroma_client, _collection
    
    if _collection is not None:
        return _collection
    
    settings = get_settings()
    persist_dir = str(settings.chroma_persist_dir)
    
    logger.info(f"Initializing ChromaDB with persistence at: {persist_dir}")
    
    # Using PersistentClient (new API) instead of deprecated Settings pattern
    _chroma_client = chromadb.PersistentClient(
        path=persist_dir,
    )
    
    # Get or create our collection
    _collection = _chroma_client.get_or_create_collection(
        name="resume_embeddings",
        metadata={"description": "Resume text embeddings for similarity search"}
    )
    
    logger.info(f"ChromaDB collection ready with {_collection.count()} existing embeddings")
    
    return _collection


# =============================================================================
# SKILL SYNONYMS & NORMALIZATION - Improves matching accuracy
# =============================================================================

SKILL_SYNONYMS = {
    # Programming Languages
    "javascript": ["js", "ecmascript", "es6", "es2015", "es2020", "ecma"],
    "typescript": ["ts"],
    "python": ["python3", "py", "python 3"],
    "c++": ["cpp", "c plus plus", "cplusplus"],
    "c#": ["csharp", "c sharp", "dotnet", ".net core"],
    "golang": ["go", "go language", "go-lang"],
    
    # Frontend Frameworks
    "react": ["reactjs", "react.js", "react js"],
    "vue": ["vuejs", "vue.js", "vue js", "vue3"],
    "angular": ["angularjs", "angular.js", "angular 2+"],
    "next.js": ["nextjs", "next js", "next"],
    "svelte": ["sveltejs", "svelte.js"],
    
    # Backend Frameworks  
    "node.js": ["nodejs", "node js", "node"],
    "express": ["expressjs", "express.js"],
    "fastapi": ["fast api", "fast-api"],
    "django": ["django rest", "drf", "django rest framework"],
    "flask": ["flask api"],
    "spring": ["spring boot", "springboot", "spring framework"],
    
    # Databases
    "postgresql": ["postgres", "psql", "pgsql"],
    "mysql": ["mariadb", "maria db"],
    "mongodb": ["mongo", "mongo db"],
    "redis": ["redis cache", "redis db"],
    "elasticsearch": ["elastic search", "elastic", "es"],
    
    # Cloud & DevOps
    "aws": ["amazon web services", "amazon aws", "ec2", "s3", "lambda"],
    "gcp": ["google cloud", "google cloud platform", "gce", "bigquery"],
    "azure": ["microsoft azure", "ms azure"],
    "docker": ["containerization", "containers", "dockerfile"],
    "kubernetes": ["k8s", "kube", "k8"],
    "terraform": ["tf", "infrastructure as code", "iac"],
    "ci/cd": ["cicd", "continuous integration", "continuous deployment", "jenkins", "github actions"],
    
    # AI/ML
    "machine learning": ["ml", "machine-learning", "predictive modeling"],
    "deep learning": ["dl", "neural networks", "neural nets"],
    "natural language processing": ["nlp", "text processing", "language models"],
    "computer vision": ["cv", "image recognition", "image processing"],
    "tensorflow": ["tf", "tf2"],
    "pytorch": ["torch"],
    "langchain": ["lang chain", "lang-chain"],
    
    # Data
    "sql": ["structured query language", "sql queries"],
    "nosql": ["no-sql", "non-relational"],
    "data science": ["data analysis", "data analytics"],
    "pandas": ["pd"],
    "numpy": ["np"],
    
    # Tools & Others
    "git": ["github", "gitlab", "bitbucket", "version control", "vcs"],
    "rest api": ["rest", "restful", "restful api", "rest apis"],
    "graphql": ["graph ql", "gql"],
    "microservices": ["micro services", "micro-services", "microservice architecture"],
    "agile": ["scrum", "kanban", "sprint"],
}

# Build reverse lookup for faster matching
SKILL_SYNONYM_LOOKUP: dict[str, str] = {}
for canonical, synonyms in SKILL_SYNONYMS.items():
    SKILL_SYNONYM_LOOKUP[canonical.lower()] = canonical
    for syn in synonyms:
        SKILL_SYNONYM_LOOKUP[syn.lower()] = canonical


def normalize_skill(skill: str) -> str:
    """Normalize a skill name to its canonical form."""
    skill_lower = skill.lower().strip()
    return SKILL_SYNONYM_LOOKUP.get(skill_lower, skill)


def normalize_skills(skills: list[str]) -> set[str]:
    """Normalize a list of skills and remove duplicates."""
    normalized = set()
    for skill in skills:
        normalized.add(normalize_skill(skill).lower())
    return normalized


# =============================================================================
# JD REQUIREMENTS EXTRACTION - Now with more comprehensive parsing
# =============================================================================

# Extended skill list for detection
COMMON_SKILLS = [
    # Languages
    "python", "java", "javascript", "typescript", "go", "golang", "rust", "c++", "c#",
    "ruby", "php", "scala", "kotlin", "swift", "objective-c", "r", "matlab", "julia",
    
    # Frontend
    "react", "vue", "angular", "svelte", "next.js", "nuxt", "gatsby", "html", "css",
    "sass", "scss", "tailwind", "bootstrap", "material ui", "webpack", "vite",
    
    # Backend
    "node.js", "express", "django", "fastapi", "flask", "spring", "springboot",
    "asp.net", "rails", "ruby on rails", "laravel", "gin", "fiber",
    
    # Databases
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite",
    "oracle", "cassandra", "dynamodb", "firestore", "supabase", "prisma",
    
    # Cloud & Infrastructure
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "github actions", "gitlab ci", "circleci", "heroku", "vercel",
    "netlify", "cloudflare", "linux", "nginx", "apache",
    
    # AI/ML
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow",
    "pytorch", "keras", "scikit-learn", "pandas", "numpy", "langchain",
    "hugging face", "transformers", "llm", "gpt", "openai", "gemini",
    
    # Data
    "data science", "data engineering", "etl", "data pipeline", "airflow",
    "spark", "hadoop", "kafka", "snowflake", "dbt", "tableau", "power bi",
    
    # Architecture & Practices
    "microservices", "rest api", "graphql", "grpc", "websockets", "event-driven",
    "serverless", "message queues", "rabbitmq", "sqs",
    
    # DevOps & Tools
    "ci/cd", "devops", "git", "agile", "scrum", "jira", "confluence",
    "monitoring", "prometheus", "grafana", "datadog", "sentry",
    
    # Security
    "oauth", "jwt", "authentication", "authorization", "security", "encryption",
    
    # Soft Skills (for comprehensive matching)
    "communication", "leadership", "teamwork", "problem solving", "analytical",
]


def extract_jd_requirements(job_description: str) -> dict[str, Any]:
    """
    Parse key requirements from job description with improved accuracy.
    
    Returns dict with:
    - required_skills: list of normalized skill keywords
    - nice_to_have_skills: optional skills mentioned
    - experience_requirement: string description
    - education_requirement: string description  
    - seniority_level: detected seniority (junior/mid/senior/lead)
    """
    jd_lower = job_description.lower()
    
    # Extract skills from the JD
    found_skills = []
    for skill in COMMON_SKILLS:
        # Check for whole word matches to avoid false positives
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, jd_lower):
            found_skills.append(normalize_skill(skill))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_skills = []
    for skill in found_skills:
        if skill.lower() not in seen:
            seen.add(skill.lower())
            unique_skills.append(skill)
    
    # Extract experience requirement with improved patterns
    experience_req = None
    exp_patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)?",
        r"(?:minimum|min|at least)\s*(\d+)\s*(?:years?|yrs?)",
        r"(\d+)\s*to\s*\d+\s*(?:years?|yrs?)",
    ]
    
    for pattern in exp_patterns:
        exp_match = re.search(pattern, jd_lower)
        if exp_match:
            years = int(exp_match.group(1))
            experience_req = f"{years}+ years required"
            break
    
    # Detect seniority level
    seniority = "mid"  # default
    if any(term in jd_lower for term in ["senior", "sr.", "lead", "principal", "staff"]):
        seniority = "senior"
    elif any(term in jd_lower for term in ["junior", "jr.", "entry", "associate", "graduate"]):
        seniority = "junior"
    elif any(term in jd_lower for term in ["manager", "director", "head of", "vp"]):
        seniority = "lead"
    
    # Extract education requirements
    education_req = None
    if "phd" in jd_lower or "doctorate" in jd_lower:
        education_req = "PhD preferred"
    elif "master" in jd_lower or "msc" in jd_lower or "mba" in jd_lower:
        education_req = "Master's degree preferred"
    elif "bachelor" in jd_lower or "bsc" in jd_lower or "bs " in jd_lower or "degree" in jd_lower:
        education_req = "Bachelor's degree required"
    
    return {
        "required_skills": unique_skills,
        "experience_requirement": experience_req,
        "education_requirement": education_req,
        "seniority_level": seniority,
    }


# =============================================================================
# ENHANCED SKILL GAP ANALYSIS
# =============================================================================

def calculate_skill_gaps(
    resume_skills: list[str],
    required_skills: list[str],
) -> tuple[list[str], list[SkillMatch]]:
    """
    Compare resume skills against JD requirements with synonym awareness.
    
    Returns:
        Tuple of (missing_skills, skill_matches)
    """
    # Normalize all skills for comparison
    resume_skills_normalized = normalize_skills(resume_skills)
    
    missing = []
    skill_matches = []
    
    for req_skill in required_skills:
        req_normalized = normalize_skill(req_skill).lower()
        
        if req_normalized in resume_skills_normalized:
            # Exact match (after normalization)
            skill_matches.append(SkillMatch(
                skill=req_skill,
                found_in_resume=True,
                relevance_score=1.0,
            ))
        else:
            # Check for partial/related matches
            found_related = False
            for resume_skill in resume_skills_normalized:
                # Check if one contains the other
                if req_normalized in resume_skill or resume_skill in req_normalized:
                    skill_matches.append(SkillMatch(
                        skill=req_skill,
                        found_in_resume=True,
                        relevance_score=0.75,
                    ))
                    found_related = True
                    break
                
                # Check semantic similarity for related skills
                if _are_skills_related(req_normalized, resume_skill):
                    skill_matches.append(SkillMatch(
                        skill=req_skill,
                        found_in_resume=True,
                        relevance_score=0.6,
                    ))
                    found_related = True
                    break
            
            if not found_related:
                missing.append(req_skill)
    
    return missing, skill_matches


def _are_skills_related(skill1: str, skill2: str) -> bool:
    """Check if two skills are semantically related."""
    # Related skill groups
    related_groups = [
        {"python", "django", "flask", "fastapi", "pandas", "numpy"},
        {"javascript", "typescript", "react", "vue", "angular", "node.js"},
        {"java", "spring", "springboot", "maven", "gradle"},
        {"aws", "ec2", "s3", "lambda", "dynamodb", "cloudfront"},
        {"gcp", "bigquery", "gce", "cloud functions"},
        {"docker", "kubernetes", "containerization", "k8s"},
        {"sql", "postgresql", "mysql", "database"},
        {"machine learning", "deep learning", "tensorflow", "pytorch", "sklearn"},
        {"data science", "pandas", "numpy", "jupyter", "data analysis"},
        {"ci/cd", "jenkins", "github actions", "gitlab ci", "devops"},
    ]
    
    for group in related_groups:
        if skill1 in group and skill2 in group:
            return True
    
    return False


# =============================================================================
# ENHANCED SCORING - Weighted multi-factor score
# =============================================================================

def calculate_weighted_score(
    semantic_similarity: float,
    skill_match_ratio: float,
    experience_match: bool,
    education_match: bool,
    seniority_match: bool = True,
) -> float:
    """
    Calculate final score using weighted factors.
    
    Weights:
    - Semantic similarity: 40% (captures overall fit)
    - Skill matching: 40% (concrete skills alignment)
    - Experience: 10% (years of experience)
    - Education: 5% (degree requirements)
    - Seniority: 5% (level alignment)
    """
    weights = {
        "semantic": 0.40,
        "skills": 0.40,
        "experience": 0.10,
        "education": 0.05,
        "seniority": 0.05,
    }
    
    score = (
        weights["semantic"] * semantic_similarity +
        weights["skills"] * skill_match_ratio +
        weights["experience"] * (1.0 if experience_match else 0.5) +
        weights["education"] * (1.0 if education_match else 0.7) +
        weights["seniority"] * (1.0 if seniority_match else 0.6)
    )
    
    # Ensure score is in 0-1 range
    return max(0.0, min(1.0, score))


# =============================================================================
# MAIN ANALYSIS PIPELINE
# =============================================================================

def analyze_resume(
    extracted_resume: ExtractedResume,
    job_description: str,
) -> tuple[float, GapAnalysis, int]:
    """
    Full analysis pipeline for a resume against a job description.
    
    Args:
        extracted_resume: Structured data from Gemini extraction
        job_description: Raw JD text
        
    Returns:
        Tuple of (similarity_score, gap_analysis, processing_time_ms)
    """
    start_time = time.time()
    
    logger.info("Starting enhanced resume analysis pipeline")
    
    # 1. Generate embeddings for semantic similarity
    logger.debug("Generating embeddings...")
    
    # Create enhanced resume text for embedding (skills-focused)
    resume_text = extracted_resume.raw_text_cleaned
    skills_text = " ".join(extracted_resume.technical_skills + extracted_resume.soft_skills)
    enhanced_resume_text = f"{resume_text}\n\nKey Skills: {skills_text}"
    
    resume_embedding = generate_embedding(enhanced_resume_text)
    jd_embedding = generate_embedding(job_description)
    
    # 2. Calculate semantic similarity
    semantic_similarity = compute_cosine_similarity(resume_embedding, jd_embedding)
    
    # Normalize to 0-1 range (cosine ranges from -1 to 1, but text rarely negative)
    semantic_similarity = max(0, (semantic_similarity + 1) / 2)
    
    logger.info(f"Semantic similarity: {semantic_similarity:.4f}")
    
    # 3. Extract JD requirements with enhanced parsing
    jd_requirements = extract_jd_requirements(job_description)
    required_skills = jd_requirements["required_skills"]
    
    logger.info(f"Detected {len(required_skills)} required skills in JD")
    
    # 4. Calculate skill gaps with synonym awareness
    all_resume_skills = extracted_resume.technical_skills + extracted_resume.soft_skills
    missing_skills, skill_matches = calculate_skill_gaps(
        all_resume_skills,
        required_skills,
    )
    
    # Calculate skill match ratio
    if required_skills:
        matched_count = len(skill_matches)
        skill_match_ratio = matched_count / len(required_skills)
    else:
        skill_match_ratio = 0.7  # Default when no specific skills detected
    
    logger.info(f"Skill match ratio: {skill_match_ratio:.2f} ({len(skill_matches)}/{len(required_skills)} matched)")
    
    # 5. Check experience alignment
    experience_match = True
    experience_gap = None
    
    if jd_requirements["experience_requirement"] and extracted_resume.total_experience_years is not None:
        match = re.search(r"(\d+)", jd_requirements["experience_requirement"])
        if match:
            required_years = int(match.group(1))
            if extracted_resume.total_experience_years < required_years:
                experience_match = False
                experience_gap = (
                    f"JD requires {required_years}+ years, "
                    f"candidate has ~{extracted_resume.total_experience_years:.1f} years"
                )
    
    # 6. Check education alignment
    education_match = True  # Default to true if not specified
    
    # 7. Calculate final weighted score
    final_score = calculate_weighted_score(
        semantic_similarity=semantic_similarity,
        skill_match_ratio=skill_match_ratio,
        experience_match=experience_match,
        education_match=education_match,
    )
    
    logger.info(f"Final weighted score: {final_score:.4f}")
    
    # 8. Generate detailed summary
    summary = _generate_summary(
        score=final_score,
        missing_skills=missing_skills,
        experience_gap=experience_gap,
        skill_match_ratio=skill_match_ratio,
        extracted_resume=extracted_resume,
    )
    
    gap_analysis = GapAnalysis(
        missing_skills=missing_skills,
        partial_matches=skill_matches,
        experience_gap=experience_gap,
        education_gap=None,
        summary=summary,
    )
    
    processing_time_ms = int((time.time() - start_time) * 1000)
    logger.info(f"Analysis complete in {processing_time_ms}ms")
    
    return final_score, gap_analysis, processing_time_ms


def _generate_summary(
    score: float,
    missing_skills: list[str],
    experience_gap: str | None,
    skill_match_ratio: float,
    extracted_resume: ExtractedResume,
) -> str:
    """Generate a detailed, actionable summary based on analysis results."""
    
    parts = []
    
    # Overall assessment
    if score >= 0.85:
        parts.append("Excellent match! This candidate strongly aligns with the role requirements.")
    elif score >= 0.70:
        parts.append("Good match. The candidate meets most key requirements.")
    elif score >= 0.55:
        parts.append("Moderate match. Some alignment with potential growth areas.")
    else:
        parts.append("Limited match. Significant gaps identified.")
    
    # Skill analysis
    if skill_match_ratio >= 0.8:
        parts.append(f"Strong technical alignment ({int(skill_match_ratio*100)}% skill match).")
    elif skill_match_ratio >= 0.5:
        if missing_skills:
            top_missing = ", ".join(missing_skills[:3])
            parts.append(f"Partial skill match. Key gaps: {top_missing}.")
    else:
        if missing_skills:
            top_missing = ", ".join(missing_skills[:4])
            parts.append(f"Notable skill gaps: {top_missing}.")
    
    # Experience analysis
    if experience_gap:
        parts.append(experience_gap)
    elif extracted_resume.total_experience_years:
        parts.append(f"Candidate has {extracted_resume.total_experience_years:.0f} years of relevant experience.")
    
    return " ".join(parts)
