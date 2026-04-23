"use client";

import { useMutation } from "@tanstack/react-query";
import { screenResume, ScreeningResult } from "@/lib/api";

interface UseScreenResumeOptions {
    onSuccess?: (data: ScreeningResult) => void;
    onError?: (error: Error) => void;
}

export function useScreenResume(options?: UseScreenResumeOptions) {
    return useMutation({
        mutationFn: ({ file, jobDescription }: { file: File; jobDescription: string }) =>
            screenResume(file, jobDescription),
        onSuccess: options?.onSuccess,
        onError: options?.onError,
    });
}
