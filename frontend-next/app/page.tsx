"use client";

import { useState } from "react";
import { FileUpload } from "@/components/FileUpload";
import { ResultsCard } from "@/components/ResultsCard";
import { useScreenResume } from "@/hooks/useScreenResume";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");

  const { mutate, data, isPending, error } = useScreenResume();

  const handleAnalyze = () => {
    if (!file || !jobDescription.trim()) return;
    mutate({ file, jobDescription: jobDescription.trim() });
  };

  const isButtonDisabled = !file || jobDescription.trim().length < 10 || isPending;

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Animated Background */}
      <div className="gradient-bg" />
      <div className="grid-pattern" />
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />



      {/* Hero */}
      <header className="relative z-10 mx-auto max-w-3xl px-6 pt-20 pb-16 text-center">
        <div className="animate-fadeIn mb-8 inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-5 py-2.5 backdrop-blur-sm">
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-green-500" />
          </span>
          <span className="text-sm font-medium text-zinc-300">AI-Powered Resume Analysis</span>
          <span className="rounded-full bg-indigo-500/20 px-2 py-0.5 text-[10px] font-bold uppercase text-indigo-300">New</span>
        </div>

        <h1 className="animate-slideUp text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
          <span className="gradient-text">Intelligent Resume</span>
          <br />
          <span className="text-white">Screening</span>
        </h1>

        <p className="animate-slideUp mx-auto mt-6 max-w-xl text-lg text-zinc-400" style={{ animationDelay: "0.1s" }}>
          Upload a resume and job description to instantly analyze candidate fit with{" "}
          <span className="text-indigo-400">AI-powered</span> skill matching and gap analysis.
        </p>

        {/* Stats */}
        <div className="animate-slideUp mt-10 flex items-center justify-center gap-8" style={{ animationDelay: "0.2s" }}>
          {[
            { value: "99%", label: "Accuracy" },
            { value: "<3s", label: "Analysis" },
            { value: "50+", label: "Skills Detected" },
          ].map((stat, i) => (
            <div key={i} className="text-center">
              <div className="text-2xl font-bold text-white">{stat.value}</div>
              <div className="text-xs text-zinc-500">{stat.label}</div>
            </div>
          ))}
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 mx-auto max-w-7xl px-6 pb-20">
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Left Column - Inputs */}
          <div className="space-y-6">
            {/* Upload Card */}
            <div className="glass-card animate-slideUp rounded-2xl transition-all duration-300" style={{ animationDelay: "0.1s" }}>
              <div className="flex items-center gap-4 border-b border-white/5 p-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 text-2xl">
                  📄
                </div>
                <div>
                  <h2 className="text-lg font-semibold">Resume Upload</h2>
                  <p className="text-sm text-zinc-500">Drag & drop or click to browse</p>
                </div>
              </div>
              <div className="p-6">
                <FileUpload onFileSelect={setFile} selectedFile={file} />
              </div>
            </div>

            {/* Job Description Card */}
            <div className="glass-card animate-slideUp rounded-2xl transition-all duration-300" style={{ animationDelay: "0.2s" }}>
              <div className="flex items-center gap-4 border-b border-white/5 p-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 text-2xl">
                  💼
                </div>
                <div>
                  <h2 className="text-lg font-semibold">Job Description</h2>
                  <p className="text-sm text-zinc-500">Paste the role requirements</p>
                </div>
              </div>
              <div className="p-6">
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder={`We're looking for a Senior Software Engineer with:

• 5+ years of experience in Python or Node.js
• Experience with cloud platforms (AWS, GCP, or Azure)
• Strong understanding of system design
• Excellent communication skills`}
                  className="h-52 w-full resize-none rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-white placeholder-zinc-600 outline-none transition-all focus:border-indigo-500/50 focus:bg-white/[0.07] focus:ring-2 focus:ring-indigo-500/20"
                />
                <div className="mt-3 flex items-center justify-between text-xs text-zinc-500">
                  <span>{jobDescription.length} characters</span>
                  <span className={jobDescription.length > 10 ? "text-green-400" : ""}>
                    {jobDescription.length > 10 ? "✓ Ready" : "Minimum 10 characters"}
                  </span>
                </div>
              </div>
            </div>

            {/* Analyze Button */}
            <button
              onClick={handleAnalyze}
              disabled={isButtonDisabled}
              className={`
                glow-button animate-slideUp group relative flex w-full items-center justify-center gap-3 rounded-xl
                bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-600 bg-[length:200%_100%]
                px-8 py-5 text-lg font-semibold text-white shadow-lg
                transition-all duration-300 hover:bg-[position:100%_0]
                disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-[position:0_0]
              `}
              style={{ animationDelay: "0.3s" }}
            >
              {isPending ? (
                <>
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  <span>Analyzing Resume...</span>
                </>
              ) : (
                <>
                  <span>Analyze Resume</span>
                  <svg className="h-5 w-5 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </>
              )}
            </button>

            {/* Error Message */}
            {error && (
              <div className="animate-scaleIn glass-card flex items-center gap-3 rounded-xl border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
                <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{error.message}</span>
              </div>
            )}
          </div>

          {/* Right Column - Results */}
          <div className="animate-slideUp" style={{ animationDelay: "0.2s" }}>
            {data ? (
              <ResultsCard result={data} />
            ) : (
              <div className="glass-card flex h-full min-h-[500px] flex-col items-center justify-center rounded-2xl p-8 text-center">
                <div className="relative mb-6">
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-indigo-500 to-purple-500 blur-xl opacity-30" />
                  <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-zinc-800 to-zinc-900 text-4xl">
                    📊
                  </div>
                </div>
                <h3 className="text-xl font-semibold text-white">Ready to Analyze</h3>
                <p className="mt-2 max-w-sm text-sm text-zinc-500">
                  Upload a resume and enter a job description to see AI-powered analysis results here.
                </p>
                <div className="mt-8 flex items-center gap-2 text-xs text-zinc-600">
                  <div className="h-1 w-1 rounded-full bg-zinc-600" />
                  <span>Powered by Gemini AI</span>
                  <div className="h-1 w-1 rounded-full bg-zinc-600" />
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 py-8">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 sm:flex-row">
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <span>Built with</span>
            <span className="font-semibold text-zinc-400">FastAPI</span>
            <span>•</span>
            <span className="font-semibold text-zinc-400">Gemini AI</span>
            <span>•</span>
            <span className="font-semibold text-zinc-400">Next.js</span>
          </div>
          <div className="flex items-center gap-4">
            <a href="http://localhost:8001/docs" className="text-sm text-zinc-500 hover:text-white transition-colors">
              API Docs
            </a>
            <a href="https://github.com" className="text-sm text-zinc-500 hover:text-white transition-colors">
              GitHub
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
