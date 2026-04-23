'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/components/AuthGuard';

const PUBLIC_PATHS = ['/login', '/register'];

export function Navigation() {
    const pathname = usePathname();
    const { user, logout } = useAuth();

    // Don't show nav on login/register pages
    if (PUBLIC_PATHS.includes(pathname)) {
        return null;
    }

    const handleLogout = () => {
        logout();
        window.location.href = '/login';
    };

    return (
        <nav className="border-b border-white/5 bg-white/[0.02] backdrop-blur-xl">
            <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
                <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 font-bold text-white shadow-lg">
                        AI
                    </div>
                    <span className="text-lg font-bold">Resume Screener</span>
                </div>

                <div className="flex items-center gap-6">
                    <Link
                        href="/"
                        className={`text-sm font-medium transition-colors hover:text-white ${pathname === '/' ? 'text-white underline decoration-indigo-500 underline-offset-4' : 'text-zinc-400'
                            }`}
                    >
                        Single Screen
                    </Link>
                    <Link
                        href="/rank"
                        className={`text-sm font-medium transition-colors hover:text-white ${pathname === '/rank' ? 'text-white underline decoration-indigo-500 underline-offset-4' : 'text-zinc-400'
                            }`}
                    >
                        Batch Ranking
                        <span className="ml-1 rounded bg-indigo-500/10 px-1.5 py-0.5 text-[10px] text-indigo-400">NEW</span>
                    </Link>

                    {/* Desktop only features */}
                    <div className="hidden md:flex items-center gap-6 border-l border-white/10 pl-6">
                        <a
                            href="http://127.0.0.1:8000/docs"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="group flex items-center gap-2 text-sm text-zinc-400 transition-colors hover:text-white"
                        >
                            <span>API Docs</span>
                            <svg className="h-4 w-4 transition-transform group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                        </a>
                        <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs">
                            <span className="h-2 w-2 animate-pulse rounded-full bg-green-400" />
                            <span className="text-zinc-400">Online</span>
                        </div>
                    </div>

                    {/* User menu */}
                    <div className="flex items-center gap-3 pl-4 border-l border-white/10">
                        <span className="text-xs text-zinc-500 hidden sm:inline-block">
                            {user?.email || 'Loading...'}
                        </span>
                        <button
                            onClick={handleLogout}
                            className="text-sm font-medium text-zinc-400 hover:text-red-400 transition-colors"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
}
