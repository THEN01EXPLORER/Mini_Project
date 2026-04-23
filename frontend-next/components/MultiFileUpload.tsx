"use client";

import { useCallback, useState } from "react";

interface MultiFileUploadProps {
    onFilesSelect: (files: File[]) => void;
    selectedFiles: File[];
    maxFiles?: number;
}

export function MultiFileUpload({ onFilesSelect, selectedFiles, maxFiles = 10 }: MultiFileUploadProps) {
    const [isDragOver, setIsDragOver] = useState(false);

    const addFiles = useCallback(
        (newFiles: File[]) => {
            const pdfFiles = newFiles.filter(f => f.type === "application/pdf" || f.name.toLowerCase().endsWith('.pdf'));
            const combined = [...selectedFiles, ...pdfFiles].slice(0, maxFiles);
            onFilesSelect(combined);
        },
        [onFilesSelect, selectedFiles, maxFiles]
    );

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
            addFiles(Array.from(e.dataTransfer.files));
        },
        [addFiles]
    );

    const handleFileChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            if (e.target.files && e.target.files.length > 0) {
                addFiles(Array.from(e.target.files));
                e.target.value = "";
            }
        },
        [addFiles]
    );

    const removeFile = (index: number) => {
        onFilesSelect(selectedFiles.filter((_, i) => i !== index));
    };

    const clearAll = () => onFilesSelect([]);

    const totalSize = selectedFiles.reduce((acc, f) => acc + f.size, 0);

    return (
        <div className="space-y-4">
            {/* Drop Zone */}
            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => document.getElementById("multi-file-input")?.click()}
                className={`
                    group relative cursor-pointer overflow-hidden rounded-xl border-2 border-dashed p-8 text-center
                    transition-all duration-300
                    ${isDragOver
                        ? "scale-[1.02] border-indigo-500 bg-indigo-500/10"
                        : selectedFiles.length > 0
                            ? "border-green-500/30 bg-green-500/5 hover:border-green-500/50"
                            : "border-white/10 hover:border-white/20 hover:bg-white/5"
                    }
                `}
            >
                {/* Shimmer */}
                <div className="pointer-events-none absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 transition-all duration-700 group-hover:translate-x-full group-hover:opacity-100" />

                <input
                    id="multi-file-input"
                    type="file"
                    accept=".pdf"
                    multiple
                    onChange={handleFileChange}
                    className="hidden"
                />

                <div className="relative mx-auto mb-4 flex h-16 w-16 items-center justify-center">
                    <div className={`absolute inset-0 rounded-2xl blur-xl transition-opacity duration-300 ${isDragOver ? "bg-indigo-500 opacity-40" : selectedFiles.length > 0 ? "bg-green-500 opacity-30" : "bg-indigo-500 opacity-0 group-hover:opacity-20"}`} />
                    <div className={`relative flex h-full w-full items-center justify-center rounded-2xl border transition-all duration-300 text-3xl ${isDragOver ? "border-indigo-500/50 bg-indigo-500/20 scale-110" : selectedFiles.length > 0 ? "border-green-500/30 bg-green-500/10" : "border-white/10 bg-white/5"}`}>
                        {isDragOver ? "📥" : selectedFiles.length > 0 ? "✅" : "📚"}
                    </div>
                </div>

                <p className="text-lg font-semibold text-white">
                    {isDragOver ? "Drop files here" : selectedFiles.length > 0 ? `${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''} selected` : "Drag & drop multiple resumes"}
                </p>
                <p className="mt-1 text-sm text-zinc-500">
                    {selectedFiles.length > 0
                        ? "Click to add more files"
                        : `Up to ${maxFiles} PDF files • Click to browse`
                    }
                </p>

                {/* Capacity bar */}
                {selectedFiles.length > 0 && (
                    <div className="mt-4 mx-auto max-w-xs">
                        <div className="flex items-center justify-between text-[10px] text-zinc-500 mb-1">
                            <span>{selectedFiles.length}/{maxFiles} files</span>
                            <span>{(totalSize / 1024 / 1024).toFixed(1)} MB total</span>
                        </div>
                        <div className="h-1 w-full rounded-full bg-white/5 overflow-hidden">
                            <div
                                className={`h-full rounded-full transition-all duration-500 ${selectedFiles.length >= maxFiles ? 'bg-yellow-500' : 'bg-indigo-500'}`}
                                style={{ width: `${(selectedFiles.length / maxFiles) * 100}%` }}
                            />
                        </div>
                    </div>
                )}
            </div>

            {/* File List */}
            {selectedFiles.length > 0 && (
                <div className="space-y-2">
                    <div className="flex items-center justify-between px-1">
                        <span className="text-xs font-medium text-zinc-500">
                            {selectedFiles.length} resume{selectedFiles.length > 1 ? 's' : ''} queued
                        </span>
                        <button
                            onClick={(e) => { e.stopPropagation(); clearAll(); }}
                            className="text-xs text-zinc-500 hover:text-red-400 transition-colors"
                        >
                            Clear all
                        </button>
                    </div>
                    <div className="grid gap-2 max-h-60 overflow-y-auto pr-1">
                        {selectedFiles.map((file, i) => (
                            <div
                                key={`${file.name}-${i}`}
                                className="animate-slideUp flex items-center gap-3 rounded-lg border border-white/5 bg-white/[0.02] p-3 transition-all hover:bg-white/[0.05] group/item"
                                style={{ animationDelay: `${i * 50}ms` }}
                            >
                                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20 text-xs font-bold text-indigo-400">
                                    {i + 1}
                                </div>
                                <div className="flex-1 overflow-hidden">
                                    <p className="truncate text-sm font-medium text-white">{file.name}</p>
                                    <p className="text-xs text-zinc-500">{(file.size / 1024).toFixed(1)} KB</p>
                                </div>
                                <button
                                    onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                                    className="shrink-0 rounded-lg p-1.5 text-zinc-600 opacity-0 group-hover/item:opacity-100 hover:bg-red-500/20 hover:text-red-400 transition-all"
                                >
                                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
