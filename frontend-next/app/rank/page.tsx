"use client";

import { useState, useEffect } from "react";
import { MultiFileUpload } from "@/components/MultiFileUpload";
import { rankResumes, BatchRankingResult, CandidateResult } from "@/lib/api";

function AnimatedNumber({ value, suffix = "" }: { value: number; suffix?: string }) {
    const [display, setDisplay] = useState(0);
    useEffect(() => {
        const duration = 1200;
        const start = performance.now();
        const animate = (now: number) => {
            const p = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - p, 4);
            setDisplay(Math.round(value * eased));
            if (p < 1) requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
    }, [value]);
    return <>{display}{suffix}</>;
}

function MiniScoreRing({ score, size = 56 }: { score: number; size?: number }) {
    const r = (size - 8) / 2;
    const circ = 2 * Math.PI * r;
    const color = score >= 85 ? "#22c55e" : score >= 70 ? "#3b82f6" : score >= 50 ? "#eab308" : "#ef4444";

    return (
        <div className="relative" style={{ width: size, height: size }}>
            <svg width={size} height={size} className="-rotate-90">
                <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
                <circle
                    cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="4"
                    strokeLinecap="round" strokeDasharray={circ}
                    strokeDashoffset={circ - (score / 100) * circ}
                    className="transition-all duration-[1200ms] ease-out"
                    style={{ filter: `drop-shadow(0 0 6px ${color}40)` }}
                />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-bold" style={{ color }}>{score}%</span>
            </div>
        </div>
    );
}

function CandidateCard({ candidate, index }: { candidate: CandidateResult; index: number }) {
    const [expanded, setExpanded] = useState(false);
    const score = Math.round(candidate.similarity_score * 100);
    const isTop = candidate.rank <= 3;
    const medals = ["🥇", "🥈", "🥉"];

    return (
        <div
            className={`animate-slideUp group relative overflow-hidden rounded-2xl border transition-all duration-300 hover:shadow-lg cursor-pointer
                ${isTop ? "border-indigo-500/20 bg-gradient-to-br from-indigo-500/[0.03] to-purple-500/[0.03]" : "border-white/5 bg-white/[0.02]"}
                hover:border-indigo-500/30`}
            style={{ animationDelay: `${index * 80}ms` }}
            onClick={() => setExpanded(!expanded)}
        >
            {/* Rank badge */}
            <div className={`absolute left-0 top-0 flex h-9 w-9 items-center justify-center rounded-br-xl text-sm font-bold
                ${candidate.rank === 1 ? "bg-yellow-500/20 text-yellow-400" :
                    candidate.rank === 2 ? "bg-zinc-400/20 text-zinc-300" :
                        candidate.rank === 3 ? "bg-amber-700/20 text-amber-500" :
                            "bg-indigo-500/10 text-indigo-400"}`}>
                {candidate.rank <= 3 ? medals[candidate.rank - 1] : `#${candidate.rank}`}
            </div>

            {/* Main row */}
            <div className="flex items-center gap-4 p-5 pl-12">
                {/* Avatar */}
                <div className="relative shrink-0">
                    <div className={`absolute inset-0 rounded-xl blur-lg opacity-30 ${candidate.rank === 1 ? "bg-yellow-500" : "bg-indigo-500"}`} />
                    <div className={`relative flex h-12 w-12 items-center justify-center rounded-xl text-lg font-bold text-white
                        ${candidate.rank === 1 ? "bg-gradient-to-br from-yellow-500 to-amber-600" : "bg-gradient-to-br from-indigo-500 to-purple-600"}`}>
                        {(candidate.candidate_name || "?")[0].toUpperCase()}
                    </div>
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                    <h3 className="text-base font-bold text-white truncate">
                        {candidate.candidate_name || "Unknown Candidate"}
                    </h3>
                    <p className="text-xs text-zinc-500 truncate">{candidate.filename}</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                        <span className="rounded-md bg-white/5 px-2 py-0.5 text-[11px] text-zinc-400">
                            {candidate.experience_years ? `${candidate.experience_years}y exp` : "Exp N/A"}
                        </span>
                        <span className="rounded-md bg-green-500/10 px-2 py-0.5 text-[11px] text-green-400">
                            {candidate.skill_match_count} skills
                        </span>
                        {candidate.missing_skills.length > 0 && (
                            <span className="rounded-md bg-red-500/10 px-2 py-0.5 text-[11px] text-red-400">
                                {candidate.missing_skills.length} gaps
                            </span>
                        )}
                    </div>
                </div>

                {/* Score */}
                <div className="shrink-0 flex flex-col items-center gap-1">
                    <MiniScoreRing score={score} />
                </div>

                {/* Expand chevron */}
                <svg
                    className={`h-5 w-5 shrink-0 text-zinc-600 transition-transform duration-300 ${expanded ? "rotate-180" : ""}`}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
            </div>

            {/* Expanded details */}
            <div className={`overflow-hidden transition-all duration-300 ${expanded ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0"}`}>
                <div className="border-t border-white/5 px-5 py-4 space-y-4">
                    {/* Summary */}
                    <div>
                        <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">AI Summary</h4>
                        <p className="text-sm text-zinc-400 leading-relaxed rounded-lg bg-white/[0.02] border border-white/5 p-3">
                            {candidate.summary}
                        </p>
                    </div>

                    {/* Missing skills */}
                    {candidate.missing_skills.length > 0 && (
                        <div>
                            <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Missing Skills</h4>
                            <div className="flex flex-wrap gap-1.5">
                                {candidate.missing_skills.map((skill) => (
                                    <span key={skill} className="rounded-lg border border-red-500/20 bg-red-500/10 px-2.5 py-1 text-xs text-red-400">
                                        {skill}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Fairness */}
                    <div className="flex items-center gap-3">
                        <span className="text-xs text-zinc-500">Fairness:</span>
                        <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                            <div
                                className={`h-full rounded-full transition-all duration-700 ${candidate.fairness_score >= 80 ? "bg-green-500" : "bg-yellow-500"}`}
                                style={{ width: `${candidate.fairness_score}%` }}
                            />
                        </div>
                        <span className={`text-xs font-medium ${candidate.fairness_score >= 80 ? "text-green-400" : "text-yellow-400"}`}>
                            {candidate.fairness_score}%
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function RankPage() {
    const [files, setFiles] = useState<File[]>([]);
    const [jobDesc, setJobDesc] = useState("");
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [result, setResult] = useState<BatchRankingResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [progress, setProgress] = useState(0);

    const handleRank = async () => {
        if (files.length === 0 || !jobDesc.trim()) return;

        setIsAnalyzing(true);
        setError(null);
        setResult(null);
        setProgress(0);

        // Simulate progress while waiting for API
        const interval = setInterval(() => {
            setProgress(prev => {
                if (prev >= 90) { clearInterval(interval); return 90; }
                return prev + Math.random() * 8;
            });
        }, 500);

        try {
            const data = await rankResumes(files, jobDesc);
            clearInterval(interval);
            setProgress(100);
            setTimeout(() => setResult(data), 300);
        } catch (err) {
            clearInterval(interval);
            setProgress(0);
            setError(err instanceof Error ? err.message : "Ranking failed");
        } finally {
            setIsAnalyzing(false);
        }
    };

    const bestScore = result ? Math.round(Math.max(...result.candidates.map(c => c.similarity_score)) * 100) : 0;
    const avgScore = result ? Math.round(result.candidates.reduce((a, c) => a + c.similarity_score, 0) / result.candidates.length * 100) : 0;

    return (
        <main className="relative min-h-screen overflow-hidden p-6 pb-20">
            <div className="gradient-bg" />
            <div className="grid-pattern" />
            <div className="orb orb-1" />
            <div className="orb orb-2" />

            <div className="relative z-10 mx-auto max-w-6xl">
                {/* Header */}
                <header className="mb-10 text-center animate-fadeIn">
                    <div className="mb-6 inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-5 py-2.5 backdrop-blur-sm">
                        <span className="relative flex h-2.5 w-2.5">
                            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-purple-400 opacity-75" />
                            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-purple-500" />
                        </span>
                        <span className="text-sm font-medium text-zinc-300">Batch Resume Ranking</span>
                    </div>

                    <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
                        <span className="gradient-text">Compare & Rank</span>
                        <br />
                        <span className="text-white">Multiple Candidates</span>
                    </h1>
                    <p className="mx-auto mt-4 max-w-xl text-zinc-400">
                        Upload up to 10 resumes, paste a job description, and get an
                        <span className="text-indigo-400"> AI-ranked leaderboard </span>
                        with fairness checks instantly.
                    </p>
                </header>

                <div className="grid gap-8 lg:grid-cols-5">
                    {/* Left Column: Inputs (2/5) */}
                    <div className="space-y-6 lg:col-span-2">
                        {/* Upload */}
                        <section className="glass-card animate-slideUp rounded-2xl" style={{ animationDelay: "0.1s" }}>
                            <div className="flex items-center gap-4 border-b border-white/5 p-5">
                                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 text-xl">📚</div>
                                <div>
                                    <h2 className="text-base font-semibold">Upload Resumes</h2>
                                    <p className="text-xs text-zinc-500">PDF files, up to 10</p>
                                </div>
                            </div>
                            <div className="p-5">
                                <MultiFileUpload onFilesSelect={setFiles} selectedFiles={files} />
                            </div>
                        </section>

                        {/* Job Description */}
                        <section className="glass-card animate-slideUp rounded-2xl" style={{ animationDelay: "0.2s" }}>
                            <div className="flex items-center gap-4 border-b border-white/5 p-5">
                                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 text-xl">💼</div>
                                <div>
                                    <h2 className="text-base font-semibold">Job Description</h2>
                                    <p className="text-xs text-zinc-500">Paste the role requirements</p>
                                </div>
                            </div>
                            <div className="p-5">
                                <textarea
                                    value={jobDesc}
                                    onChange={(e) => setJobDesc(e.target.value)}
                                    placeholder={`We're looking for a Senior Engineer with:\n\n• 5+ years experience in Python\n• Cloud platforms (AWS/GCP)\n• System design expertise`}
                                    className="h-40 w-full resize-none rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-white placeholder-zinc-600 outline-none transition-all focus:border-indigo-500/50 focus:bg-white/[0.07] focus:ring-2 focus:ring-indigo-500/20"
                                />
                                <div className="mt-2 flex items-center justify-between text-xs text-zinc-500">
                                    <span>{jobDesc.length} chars</span>
                                    <span className={jobDesc.length > 10 ? "text-green-400" : ""}>
                                        {jobDesc.length > 10 ? "✓ Ready" : "Min 10 characters"}
                                    </span>
                                </div>
                            </div>
                        </section>

                        {/* Action Button */}
                        <button
                            onClick={handleRank}
                            disabled={isAnalyzing || files.length === 0 || jobDesc.trim().length < 10}
                            className={`glow-button animate-slideUp group relative flex w-full items-center justify-center gap-3 rounded-xl px-8 py-4 text-base font-semibold text-white shadow-lg transition-all duration-300
                                ${isAnalyzing || files.length === 0 || jobDesc.trim().length < 10
                                    ? "cursor-not-allowed bg-zinc-800 text-zinc-500 opacity-60"
                                    : "bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-600 bg-[length:200%_100%] hover:bg-[position:100%_0] hover:scale-[1.02] hover:shadow-indigo-500/25"
                                }`}
                            style={{ animationDelay: "0.3s" }}
                        >
                            {isAnalyzing ? (
                                <>
                                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                                    <span>Ranking {files.length} Candidates...</span>
                                </>
                            ) : (
                                <>
                                    <span>Rank {files.length > 0 ? `${files.length} ` : ""}Candidates</span>
                                    <svg className="h-5 w-5 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                    </svg>
                                </>
                            )}
                        </button>

                        {/* Progress bar */}
                        {isAnalyzing && (
                            <div className="animate-fadeIn space-y-2">
                                <div className="h-1.5 w-full rounded-full bg-white/5 overflow-hidden">
                                    <div
                                        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500 ease-out"
                                        style={{ width: `${progress}%` }}
                                    />
                                </div>
                                <p className="text-center text-xs text-zinc-500">
                                    Processing resumes with AI... {Math.round(progress)}%
                                </p>
                            </div>
                        )}

                        {/* Error */}
                        {error && (
                            <div className="animate-scaleIn glass-card flex items-center gap-3 rounded-xl border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
                                <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span>{error}</span>
                            </div>
                        )}
                    </div>

                    {/* Right Column: Results (3/5) */}
                    <div className="lg:col-span-3 space-y-6">
                        {result ? (
                            <div className="space-y-6 animate-fadeIn">
                                {/* Stats Row */}
                                <div className="grid grid-cols-4 gap-3">
                                    {[
                                        { icon: "👥", value: result.total_processed, label: "Ranked" },
                                        { icon: "🏆", value: bestScore, label: "Best Match", suffix: "%" },
                                        { icon: "📊", value: avgScore, label: "Avg Score", suffix: "%" },
                                        { icon: "⚡", value: (result.processing_time_ms / 1000).toFixed(1), label: "Seconds" },
                                    ].map((s, i) => (
                                        <div key={i} className="glass-card rounded-xl p-4 text-center animate-slideUp" style={{ animationDelay: `${i * 80}ms` }}>
                                            <div className="text-xl mb-1">{s.icon}</div>
                                            <div className="text-lg font-bold text-white">
                                                {typeof s.value === "number" ? <AnimatedNumber value={s.value} suffix={s.suffix} /> : s.value}
                                            </div>
                                            <div className="text-[10px] text-zinc-500 uppercase tracking-wider">{s.label}</div>
                                        </div>
                                    ))}
                                </div>

                                {/* JD Fairness */}
                                <div className="glass-card rounded-2xl p-5 animate-slideUp" style={{ animationDelay: "0.1s" }}>
                                    <div className="flex items-center justify-between mb-3">
                                        <h3 className="text-sm font-semibold flex items-center gap-2">
                                            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-blue-500/10 text-xs">⚖️</span>
                                            JD Fairness Check
                                        </h3>
                                        <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${result.job_description_fairness.is_fair ? "bg-green-500/10 text-green-400" : "bg-yellow-500/10 text-yellow-400"}`}>
                                            {result.job_description_fairness.is_fair ? "PASS" : "ISSUES"}
                                        </span>
                                    </div>
                                    {result.job_description_fairness.issues.length > 0 ? (
                                        <ul className="space-y-1.5">
                                            {result.job_description_fairness.issues.map((issue, i) => (
                                                <li key={i} className="flex items-start gap-2 text-xs text-yellow-400/80">
                                                    <span>⚠️</span>{issue}
                                                </li>
                                            ))}
                                        </ul>
                                    ) : (
                                        <p className="text-xs text-green-400/80">✅ Job description appears free of common bias triggers.</p>
                                    )}
                                </div>

                                {/* Leaderboard */}
                                <div>
                                    <h2 className="mb-4 text-lg font-bold flex items-center gap-2 animate-slideUp">
                                        🏆 Candidate Leaderboard
                                        <span className="text-sm font-normal text-zinc-500">
                                            ({result.candidates.length} ranked • click to expand)
                                        </span>
                                    </h2>
                                    <div className="space-y-3">
                                        {result.candidates.map((candidate, i) => (
                                            <CandidateCard key={candidate.filename} candidate={candidate} index={i} />
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            /* Placeholder */
                            <div className="glass-card flex h-full min-h-[500px] flex-col items-center justify-center rounded-2xl p-8 text-center animate-slideUp">
                                <div className="relative mb-6">
                                    <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-indigo-500 to-purple-500 blur-xl opacity-20" />
                                    <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-zinc-800 to-zinc-900 text-4xl">
                                        🏆
                                    </div>
                                </div>
                                <h3 className="text-xl font-semibold text-white">Ready to Rank</h3>
                                <p className="mt-2 max-w-sm text-sm text-zinc-500">
                                    Upload multiple resumes and enter a job description to see the AI-powered candidate leaderboard here.
                                </p>
                                <div className="mt-8 grid grid-cols-3 gap-6 text-center">
                                    {[
                                        { icon: "📚", label: "Upload PDFs" },
                                        { icon: "💼", label: "Add JD" },
                                        { icon: "🚀", label: "Get Rankings" },
                                    ].map((step, i) => (
                                        <div key={i} className="flex flex-col items-center gap-2">
                                            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 text-xl">{step.icon}</div>
                                            <span className="text-xs text-zinc-500">{step.label}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}
