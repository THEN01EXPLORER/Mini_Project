"use client";

import { ScreeningResult } from "@/lib/api";
import { useEffect, useState } from "react";

interface ResultsCardProps {
    result: ScreeningResult;
}

function ScoreRing({ score }: { score: number }) {
    const [offset, setOffset] = useState(452);
    const circumference = 452;

    useEffect(() => {
        const timer = setTimeout(() => {
            setOffset(circumference - (score / 100) * circumference);
        }, 300);
        return () => clearTimeout(timer);
    }, [score]);

    const getColor = () => {
        if (score >= 85) return { stroke: "#22c55e", glow: "rgba(34, 197, 94, 0.5)" };
        if (score >= 70) return { stroke: "#3b82f6", glow: "rgba(59, 130, 246, 0.5)" };
        if (score >= 50) return { stroke: "#eab308", glow: "rgba(234, 179, 8, 0.5)" };
        return { stroke: "#ef4444", glow: "rgba(239, 68, 68, 0.5)" };
    };

    const colors = getColor();

    return (
        <div className="relative mx-auto h-44 w-44">
            {/* Glow effect */}
            <div
                className="absolute inset-0 rounded-full blur-2xl opacity-30 transition-opacity duration-1000"
                style={{ backgroundColor: colors.glow }}
            />

            <svg className="h-44 w-44 -rotate-90 score-ring-animated" style={{ color: colors.stroke }}>
                {/* Background track */}
                <circle
                    cx="88"
                    cy="88"
                    r="72"
                    fill="none"
                    stroke="rgba(255,255,255,0.05)"
                    strokeWidth="10"
                />
                {/* Animated progress */}
                <circle
                    cx="88"
                    cy="88"
                    r="72"
                    fill="none"
                    stroke={colors.stroke}
                    strokeWidth="10"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    className="transition-all duration-[1500ms] ease-out"
                    style={{ filter: `drop-shadow(0 0 10px ${colors.glow})` }}
                />
            </svg>

            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <AnimatedNumber value={score} />
                <span className="mt-1 text-xs font-medium uppercase tracking-widest text-zinc-500">Match Score</span>
            </div>
        </div>
    );
}

function AnimatedNumber({ value }: { value: number }) {
    const [display, setDisplay] = useState(0);

    useEffect(() => {
        const duration = 1500;
        const startTime = performance.now();

        const animate = (currentTime: number) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 4);
            setDisplay(Math.round(value * eased));

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }, [value]);

    return <span className="text-5xl font-bold tracking-tight">{display}%</span>;
}

function SkillChip({
    skill,
    variant,
    delay,
}: {
    skill: string;
    variant: "found" | "missing";
    delay: number;
}) {
    return (
        <span
            className={`
        chip-animate cursor-default rounded-lg px-3 py-1.5 text-sm font-medium
        transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg
        ${variant === "found"
                    ? "bg-gradient-to-r from-green-500/10 to-emerald-500/10 text-green-400 border border-green-500/20 hover:border-green-500/40 hover:shadow-green-500/10"
                    : "bg-gradient-to-r from-red-500/10 to-rose-500/10 text-red-400 border border-red-500/20 hover:border-red-500/40 hover:shadow-red-500/10"
                }
      `}
            style={{ animationDelay: `${delay}ms` }}
        >
            {skill}
        </span>
    );
}

function StatCard({ value, label, icon, color }: { value: string | number; label: string; icon: string; color: string }) {
    return (
        <div className="group relative overflow-hidden rounded-xl border border-white/5 bg-white/[0.02] p-5 text-center transition-all hover:border-white/10 hover:bg-white/[0.04]">
            <div className={`absolute inset-0 bg-gradient-to-br ${color} opacity-0 transition-opacity group-hover:opacity-100`} />
            <div className="relative">
                <div className="mb-2 text-2xl">{icon}</div>
                <div className="text-2xl font-bold">{value}</div>
                <div className="mt-1 text-xs text-zinc-500">{label}</div>
            </div>
        </div>
    );
}

function FairnessMeter({ score, issues }: { score: number; issues: string[] }) {
    const isHigh = score >= 85;
    const isMedium = score >= 70;

    return (
        <div className="border-b border-white/5 p-6">
            <h4 className="mb-4 flex items-center gap-2.5 text-sm font-semibold">
                <span className="flex h-6 w-6 items-center justify-center rounded-md bg-blue-500/10 text-xs">⚖️</span>
                <span className="text-zinc-400">Fairness Check</span>
                <span className={`ml-auto text-xs font-medium ${isHigh ? 'text-green-400' : isMedium ? 'text-yellow-400' : 'text-red-400'}`}>
                    {score}/100
                </span>
            </h4>

            {/* Progress Bar */}
            <div className="relative h-2 w-full overflow-hidden rounded-full bg-white/5">
                <div
                    className={`absolute inset-y-0 left-0 rounded-full transition-all duration-1000 ${isHigh ? 'bg-gradient-to-r from-green-500 to-emerald-500' :
                        isMedium ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
                            'bg-gradient-to-r from-red-500 to-rose-500'
                        }`}
                    style={{ width: `${score}%` }}
                />
            </div>

            {/* Issues or Success Message */}
            <div className="mt-4">
                {issues.length === 0 ? (
                    <div className="flex items-center gap-2 text-xs text-green-400/80">
                        <span>✅</span> No bias indicators detected
                    </div>
                ) : (
                    <div className="space-y-2">
                        {issues.map((issue, i) => (
                            <div key={i} className="flex items-start gap-2 text-xs text-yellow-400/80">
                                <span className="mt-0.5">⚠️</span>
                                <span>{issue}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export function ResultsCard({ result }: ResultsCardProps) {
    const score = Math.round(result.similarity_score * 100);
    const { extracted_data: ext, gap_analysis: gap } = result;
    const allSkills = [...(ext.technical_skills || []), ...(ext.soft_skills || [])];
    const missingSkills = gap.missing_skills || [];

    const getMatchLabel = () => {
        if (score >= 85) return { icon: "🌟", text: "Excellent Match", gradient: "from-green-500 to-emerald-500", bg: "bg-green-500/10", border: "border-green-500/30" };
        if (score >= 70) return { icon: "👍", text: "Good Match", gradient: "from-blue-500 to-cyan-500", bg: "bg-blue-500/10", border: "border-blue-500/30" };
        if (score >= 50) return { icon: "⚡", text: "Moderate Match", gradient: "from-yellow-500 to-orange-500", bg: "bg-yellow-500/10", border: "border-yellow-500/30" };
        return { icon: "📈", text: "Needs Improvement", gradient: "from-red-500 to-rose-500", bg: "bg-red-500/10", border: "border-red-500/30" };
    };

    const match = getMatchLabel();

    return (
        <div className="glass-card animate-slideUp overflow-hidden rounded-2xl">
            {/* Header with gradient */}
            <div className="relative overflow-hidden border-b border-white/5 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 p-6">
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImEiIHBhdHRlcm5Vbml0cz0idXNlclNwYWNlT25Vc2UiIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCI+PHBhdGggZD0iTTEwIDBWMjBNMCAxMEgyMCIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDMpIiBmaWxsPSJub25lIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCBmaWxsPSJ1cmwoI2EpIiB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIi8+PC9zdmc+')] opacity-50" />

                <div className="relative flex items-center gap-4">
                    <div className="relative">
                        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 blur-lg opacity-50" />
                        <div className="relative flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-2xl font-bold shadow-lg">
                            {(ext.candidate_name || "?")[0].toUpperCase()}
                        </div>
                    </div>
                    <div>
                        <h3 className="text-xl font-bold">{ext.candidate_name || "Candidate"}</h3>
                        <p className="text-sm text-zinc-400">
                            {ext.total_experience_years
                                ? `${ext.total_experience_years} years of experience`
                                : "Experience not specified"}
                        </p>
                    </div>
                </div>
            </div>

            {/* Score Section */}
            <div className="border-b border-white/5 p-8 text-center">
                <ScoreRing score={score} />

                <div className={`mt-6 inline-flex items-center gap-2.5 rounded-full ${match.bg} border ${match.border} px-5 py-2.5`}>
                    <span className="text-lg">{match.icon}</span>
                    <span className={`font-semibold bg-gradient-to-r ${match.gradient} bg-clip-text text-transparent`}>
                        {match.text}
                    </span>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-3 gap-px border-b border-white/5 bg-white/5">
                <StatCard value={allSkills.length} label="Skills Found" icon="✅" color="from-green-500/5 to-transparent" />
                <StatCard value={missingSkills.length} label="Gaps" icon="⚠️" color="from-yellow-500/5 to-transparent" />
                <StatCard value={`${(result.processing_time_ms / 1000).toFixed(1)}s`} label="Analysis" icon="⚡" color="from-blue-500/5 to-transparent" />
            </div>

            {/* Fairness Meter */}
            <FairnessMeter score={result.fairness_score || 100} issues={result.fairness_issues || []} />

            {/* Skills Found */}
            <div className="border-b border-white/5 p-6">
                <h4 className="mb-4 flex items-center gap-2.5 text-sm font-semibold">
                    <span className="flex h-6 w-6 items-center justify-center rounded-md bg-green-500/10 text-xs">✓</span>
                    <span className="text-zinc-400">Matched Skills</span>
                    <span className="ml-auto text-xs text-zinc-600">{allSkills.length} found</span>
                </h4>
                <div className="flex flex-wrap gap-2">
                    {allSkills.slice(0, 15).map((skill, i) => (
                        <SkillChip key={skill} skill={skill} variant="found" delay={500 + i * 40} />
                    ))}
                    {allSkills.length > 15 && (
                        <span className="rounded-lg bg-white/5 px-3 py-1.5 text-sm text-zinc-500">
                            +{allSkills.length - 15} more
                        </span>
                    )}
                </div>
            </div>

            {/* Missing Skills */}
            {missingSkills.length > 0 && (
                <div className="border-b border-white/5 p-6">
                    <h4 className="mb-4 flex items-center gap-2.5 text-sm font-semibold">
                        <span className="flex h-6 w-6 items-center justify-center rounded-md bg-red-500/10 text-xs">✗</span>
                        <span className="text-zinc-400">Missing Skills</span>
                        <span className="ml-auto text-xs text-zinc-600">{missingSkills.length} gaps</span>
                    </h4>
                    <div className="flex flex-wrap gap-2">
                        {missingSkills.map((skill, i) => (
                            <SkillChip key={skill} skill={skill} variant="missing" delay={600 + i * 40} />
                        ))}
                    </div>
                </div>
            )}

            {/* Summary */}
            <div className="p-6">
                <h4 className="mb-3 flex items-center gap-2.5 text-sm font-semibold">
                    <span className="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-500/10 text-xs">💡</span>
                    <span className="text-zinc-400">AI Analysis Summary</span>
                </h4>
                <p className="rounded-xl bg-gradient-to-r from-white/[0.02] to-transparent p-4 text-sm leading-relaxed text-zinc-400 border border-white/5">
                    {gap.summary || "No specific gaps identified. The candidate appears to be a strong match for the position."}
                </p>
            </div>
        </div>
    );
}
