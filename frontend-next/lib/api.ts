// Resume screening API types and hooks
import { getToken } from './auth';

// Helper to get auth headers
function getAuthHeaders(): HeadersInit {
    const token = getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export interface ExtractedResume {
    candidate_name: string | null;
    email: string | null;
    phone: string | null;
    location: string | null;
    total_experience_years: number | null;
    education: string[];
    technical_skills: string[];
    soft_skills: string[];
    work_experiences: string[];
    certifications: string[];
    summary: string | null;
}

export interface GapAnalysis {
    matched_skills: string[];
    missing_skills: string[];
    experience_match: boolean;
    education_match: boolean;
    summary: string;
    recommendations: string[];
}

export interface ScreeningResult {
    similarity_score: number;
    extracted_data: ExtractedResume;
    gap_analysis: GapAnalysis;
    processing_time_ms: number;
    fairness_score: number;
    fairness_issues: string[];
}

export interface CandidateResult {
    rank: number;
    candidate_name: string | null;
    filename: string;
    similarity_score: number;
    skill_match_count: number;
    missing_skills: string[];
    experience_years: number | null;
    fairness_score: number;
    summary: string;
}

export interface BatchRankingResult {
    job_description_fairness: {
        is_fair: boolean;
        issues: string[];
        fairness_score: number;
    };
    candidates: CandidateResult[];
    total_processed: number;
    processing_time_ms: number;
}

export interface ScreeningResponse {
    success: boolean;
    result?: ScreeningResult;
    error?: {
        type: string;
        message: string;
    };
}

export interface RankingResponse {
    success: boolean;
    result?: BatchRankingResult;
    error?: {
        type: string;
        message: string;
    };
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function screenResume(
    file: File,
    jobDescription: string
): Promise<ScreeningResult> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("job_description", jobDescription);

    const response = await fetch(`${API_URL}/api/v1/screen`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: formData,
    });

    const data: ScreeningResponse = await response.json();

    if (!data.success || !data.result) {
        throw new Error(data.error?.message || "Analysis failed");
    }

    return data.result;
}

export async function rankResumes(
    files: File[],
    jobDescription: string
): Promise<BatchRankingResult> {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    formData.append("job_description", jobDescription);

    const response = await fetch(`${API_URL}/api/v1/rank`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: formData,
    });

    const data: RankingResponse = await response.json();

    if (!data.success || !data.result) {
        throw new Error(data.error?.message || "Ranking failed");
    }

    return data.result;
}
