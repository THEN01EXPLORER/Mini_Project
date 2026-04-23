"use client";

import { useCallback, useState } from "react";

interface FileUploadProps {
    onFileSelect: (file: File) => void;
    selectedFile: File | null;
}

export function FileUpload({ onFileSelect, selectedFile }: FileUploadProps) {
    const [isDragOver, setIsDragOver] = useState(false);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(true);
    }, []);

    const handleDragLeave = useCallback(() => {
        setIsDragOver(false);
    }, []);

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            setIsDragOver(false);
            const file = e.dataTransfer.files[0];
            if (file?.type === "application/pdf") {
                onFileSelect(file);
            }
        },
        [onFileSelect]
    );

    const handleFileChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const file = e.target.files?.[0];
            if (file) {
                onFileSelect(file);
            }
        },
        [onFileSelect]
    );

    return (
        <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById("file-input")?.click()}
            className={`
        group relative cursor-pointer overflow-hidden rounded-xl border-2 border-dashed p-10 text-center
        transition-all duration-300
        ${isDragOver ? "scale-[1.02] border-indigo-500 bg-indigo-500/10" : "border-white/10 hover:border-white/20 hover:bg-white/5"}
        ${selectedFile ? "border-green-500/50 bg-green-500/5" : ""}
      `}
        >
            {/* Shimmer effect on hover */}
            <div className="pointer-events-none absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 transition-all duration-700 group-hover:translate-x-full group-hover:opacity-100" />

            <input
                id="file-input"
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
            />

            <div className="relative mx-auto mb-5 flex h-20 w-20 items-center justify-center">
                {/* Glow effect */}
                <div className={`absolute inset-0 rounded-2xl blur-xl transition-opacity duration-300 ${selectedFile ? "bg-green-500 opacity-30" : isDragOver ? "bg-indigo-500 opacity-40" : "bg-indigo-500 opacity-0 group-hover:opacity-20"}`} />

                {/* Icon container */}
                <div className={`
          relative flex h-full w-full items-center justify-center rounded-2xl border text-4xl
          transition-all duration-300
          ${selectedFile
                        ? "border-green-500/30 bg-green-500/10"
                        : isDragOver
                            ? "border-indigo-500/50 bg-indigo-500/20 scale-110"
                            : "border-white/10 bg-white/5 group-hover:border-white/20 group-hover:bg-white/10"
                    }
        `}>
                    {selectedFile ? "✅" : isDragOver ? "📥" : "📄"}
                </div>
            </div>

            <p className={`text-lg font-semibold transition-colors ${selectedFile ? "text-green-400" : "text-white"}`}>
                {selectedFile ? "File Selected!" : isDragOver ? "Drop your file here" : "Drag & drop your resume"}
            </p>

            <p className="mt-1.5 text-sm text-zinc-500">
                {selectedFile ? "Click to change file" : "or click to browse • PDF only"}
            </p>

            {selectedFile && (
                <div className="mt-5 inline-flex items-center gap-3 rounded-full bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20 px-5 py-2.5">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-500/20 text-sm">
                        📎
                    </div>
                    <div className="text-left">
                        <p className="text-sm font-medium text-green-400 truncate max-w-[200px]">
                            {selectedFile.name}
                        </p>
                        <p className="text-xs text-green-500/70">
                            {(selectedFile.size / 1024).toFixed(1)} KB
                        </p>
                    </div>
                    <svg className="h-5 w-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                </div>
            )}
        </div>
    );
}
