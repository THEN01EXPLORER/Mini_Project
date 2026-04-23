"""
ScreenerEngine - The Core Logic for Resume Screening AI.

This module implements the "2-Layer System" architecture:
Layer 1: Deterministic Information Extraction (Gemini + Pydantic)
Layer 2: Constraint & Similarity Scoring (FAISS + Logic)

Tech Stack:
- LangChain: For orchestration and prompt management
- Google Gemini: For reasoning and extraction
- FAISS: For vector similarity search
- Pydantic: For robust data validation
"""

import os
from typing import List, Optional
import math

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

# --- Layer 1: Data Models (Pydantic) ---

class ExtractedResumeData(BaseModel):
    """Structured data extracted from a resume text."""
    anonymized_id: str = Field(description="A unique hash or ID for the candidate, removing PII like name/email.")
    total_years_experience: float = Field(description="Total professional years of experience found in the resume.")
    degree_level: str = Field(description="Highest degree obtained: 'Bachelor', 'Master', 'PhD', or 'None'.")
    skills_list: List[str] = Field(description="List of technical and soft skills extracted.")
    summary: str = Field(description="A 2-sentence summary of the candidate's profile.")

class JobRequirements(BaseModel):
    """Structured requirements extracted from a Job Description."""
    required_years_experience: float = Field(description="Minimum years of experience required.")
    required_degree: str = Field(description="Minimum degree required: 'Bachelor', 'Master', 'PhD', or 'None'.")
    key_skills: List[str] = Field(description="List of must-have skills for the role.")

class ScreeningResult(BaseModel):
    """Final output of the screening process."""
    final_score: float = Field(description="Final match score (0-100).")
    is_qualified: bool = Field(description="Whether the candidate met hard constraints.")
    extracted_data: ExtractedResumeData
    explanation: str = Field(description="Reasoning for the score.")

# --- The Screener Engine Class ---

class ScreenerEngine:
    def __init__(self, google_api_key: Optional[str] = None):
        """Initialize the engine with Gemini and Embeddings."""
        self.api_key = google_api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment.")

        # Initialize LLM (Gemini 1.5 Flash is efficient for this)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key,
            temperature=0.0, # Deterministic output
            convert_system_message_to_human=True
        )

        # Initialize Embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.api_key
        )

        # Parsers
        self.resume_parser = PydanticOutputParser(pydantic_object=ExtractedResumeData)
        self.jd_parser = PydanticOutputParser(pydantic_object=JobRequirements)

    def _extract_resume_data(self, resume_text: str) -> ExtractedResumeData:
        """Layer 1: Extract structured data from resume using Gemini."""
        prompt = PromptTemplate(
            template="""
            You are an expert Resume Parser. Your goal is to extract structured data for fair hiring.
            
            INSTRUCTIONS:
            1. Anonymize the candidate (generate a hash ID like 'CAND-123' if not present).
            2. Calculate total years of experience precisely based on work history dates.
            3. Normalize degree to: 'Bachelor', 'Master', 'PhD', or 'None'.
            4. Extract all technical skills.
            5. Provide a brief 2-sentence summary.
            
            RESUME TEXT:
            {resume_text}
            
            OUTPUT FORMAT:
            {format_instructions}
            """,
            input_variables=["resume_text"],
            partial_variables={"format_instructions": self.resume_parser.get_format_instructions()}
        )

        chain = prompt | self.llm | self.resume_parser
        return chain.invoke({"resume_text": resume_text})

    def _extract_jd_requirements(self, jd_text: str) -> JobRequirements:
        """Extract hard constraints from JD."""
        prompt = PromptTemplate(
            template="""
            Extract the minimum requirements from this Job Description.
            
            JOB DESCRIPTION:
            {jd_text}
            
            OUTPUT FORMAT:
            {format_instructions}
            """,
            input_variables=["jd_text"],
            partial_variables={"format_instructions": self.jd_parser.get_format_instructions()}
        )
        
        chain = prompt | self.llm | self.jd_parser
        return chain.invoke({"jd_text": jd_text})

    def _calculate_vector_similarity(self, resume_text: str, jd_text: str) -> float:
        """Compute Cosine Similarity using FAISS."""
        # Create vector store with just the JD
        vector_store = FAISS.from_texts([jd_text], self.embeddings)
        
        # Search for the Resume in the JD space (conceptually checking semantic overlap)
        # FAISS returns L2 distance by default, but we can standard usage for similarity
        # Or simpler: embed both and dot product.
        
        resume_vec = self.embeddings.embed_query(resume_text)
        jd_vec = self.embeddings.embed_query(jd_text)
        
        # Manual Cosine Similarity
        dot_product = sum(a*b for a, b in zip(resume_vec, jd_vec))
        norm_a = math.sqrt(sum(a*a for a in resume_vec))
        norm_b = math.sqrt(sum(b*b for b in jd_vec))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        similarity = dot_product / (norm_a * norm_b)
        return max(0.0, min(1.0, similarity)) # Clamp 0-1

    def screen_resume(self, resume_text: str, jd_text: str) -> ScreeningResult:
        """
        Main Entry Point: The 2-Layer Screening Process.
        """
        # --- Layer 1: Information Extraction ---
        resume_data = self._extract_resume_data(resume_text)
        jd_constraints = self._extract_jd_requirements(jd_text)
        
        # --- Layer 2: Constraint & Similarity Scorer ---
        
        score_penalty = 1.0 # Multiplier (1.0 = no penalty)
        explanation_prefix = ""
        is_qualified = True
        
        # 1. Constraint Check (Experience)
        if resume_data.total_years_experience < jd_constraints.required_years_experience:
            score_penalty *= 0.4 # Hard penalty: Max possible score becomes 40%
            is_qualified = False
            explanation_prefix = f"Does not meet experience requirement ({resume_data.total_years_experience} vs {jd_constraints.required_years_experience} years). "

        # 2. Constraint Check (Degree) - simplified logic
        degree_hierarchy = {"None": 0, "Bachelor": 1, "Master": 2, "PhD": 3}
        cand_deg_val = degree_hierarchy.get(resume_data.degree_level, 0)
        req_deg_val = degree_hierarchy.get(jd_constraints.required_degree, 0)
        
        if cand_deg_val < req_deg_val:
            score_penalty *= 0.8 # Mild penalty for degree mismatch
            explanation_prefix += f"Degree level ({resume_data.degree_level}) is below required ({jd_constraints.required_degree}). "

        # 3. Vector Similarity (Content Match)
        similarity_score = self._calculate_vector_similarity(resume_text, jd_text)
        
        # 4. Final Score Calculation
        # Base score from similarity (0-100) * Penalty Multiplier
        final_raw_score = similarity_score * 100 * score_penalty
        final_score = round(final_raw_score, 1)
        
        # 5. Generate Explanation via LLM (Rubric-based)
        explanation_prompt = PromptTemplate(
            template="""
            Explain this candidate's score ({score}/100) for the role.
            Constraint Issues: {constraints}
            Likely fit: {qualified}
            
            Resume Summary: {summary}
            Required Skills: {skills}
            
            Write a professional 2-sentence justification for the hiring manager.
            """,
            input_variables=["score", "constraints", "qualified", "summary", "skills"]
        )
        
        explanation_chain = explanation_prompt | self.llm
        explanation = explanation_chain.invoke({
            "score": final_score,
            "constraints": explanation_prefix if explanation_prefix else "None",
            "qualified": "Yes" if is_qualified else "No",
            "summary": resume_data.summary,
            "skills": ", ".join(jd_constraints.key_skills)
        }).content

        return ScreeningResult(
            final_score=final_score,
            is_qualified=is_qualified,
            extracted_data=resume_data,
            explanation=explanation
        )

# --- Usage Example (if run directly) ---
if __name__ == "__main__":
    # Mock Data
    resume_txt = "Jane Doe. Software Engineer with 3 years in Python and AWS. Bachelors in CS."
    jd_txt = "Senior Python Dev. 5+ years experience required. Masters preferred."
    
    try:
        engine = ScreenerEngine()
        result = engine.screen_resume(resume_txt, jd_txt)
        print(result.model_dump_json(indent=2))
    except Exception as e:
        print(f"Error: {e}")
