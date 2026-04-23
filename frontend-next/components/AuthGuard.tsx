'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { isAuthenticated, getCurrentUser, logout, type UserResponse } from '@/lib/auth';

interface AuthGuardProps {
    children: React.ReactNode;
}

// Pages that don't require authentication
const PUBLIC_PATHS = ['/login', '/register'];

export function AuthGuard({ children }: AuthGuardProps) {
    const router = useRouter();
    const pathname = usePathname();
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const checkAuth = async () => {
            // Skip auth check for public pages
            if (PUBLIC_PATHS.includes(pathname)) {
                setIsLoading(false);
                return;
            }

            // Check if user is authenticated
            if (!isAuthenticated()) {
                router.push('/login');
                setIsLoading(false);
                return;
            }

            // Verify token is still valid
            const currentUser = await getCurrentUser();
            if (!currentUser) {
                logout();
                router.push('/login');
                setIsLoading(false);
                return;
            }

            setIsLoading(false);
        };

        checkAuth();
    }, [pathname, router]);

    // Show loading for protected routes
    if (isLoading && !PUBLIC_PATHS.includes(pathname)) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
                    <p className="text-slate-400">Loading...</p>
                </div>
            </div>
        );
    }

    return <>{children}</>;
}

// Hook to get current user in components
export function useAuth() {
    const [user, setUser] = useState<UserResponse | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getCurrentUser().then(u => {
            setUser(u);
            setLoading(false);
        });
    }, []);

    return { user, loading, logout };
}
