/**
 * Authentication utilities for the frontend.
 * Handles login, register, token storage, and API auth.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
const USER_CACHE_TTL_MS = 30_000;

let cachedUser: UserResponse | null = null;
let cachedUserFetchedAt = 0;
let inFlightUserRequest: Promise<UserResponse | null> | null = null;

export interface AuthResponse {
    access_token: string;
    token_type: string;
}

export interface UserResponse {
    id: number;
    email: string;
    created_at: string;
}

/**
 * Login with email and password.
 * Stores token in localStorage on success.
 */
export async function login(email: string, password: string): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
    }

    const data: AuthResponse = await response.json();
    localStorage.setItem('token', data.access_token);
    cachedUser = null;
    cachedUserFetchedAt = 0;
    return data;
}

/**
 * Register a new user.
 */
export async function register(email: string, password: string): Promise<UserResponse> {
    const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
    }

    return response.json();
}

/**
 * Get current user info.
 */
export async function getCurrentUser(): Promise<UserResponse | null> {
    const token = getToken();
    if (!token) return null;

    const now = Date.now();
    if (cachedUser && now - cachedUserFetchedAt < USER_CACHE_TTL_MS) {
        return cachedUser;
    }
    if (inFlightUserRequest) {
        return inFlightUserRequest;
    }

    try {
        inFlightUserRequest = fetch(`${API_BASE}/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` },
        })
            .then(async (response) => {
                if (!response.ok) {
                    return null;
                }
                const user = (await response.json()) as UserResponse;
                cachedUser = user;
                cachedUserFetchedAt = Date.now();
                return user;
            })
            .finally(() => {
                inFlightUserRequest = null;
            });

        return await inFlightUserRequest;
    } catch {
        inFlightUserRequest = null;
        return null;
    }
}

/**
 * Get stored token.
 */
export function getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
}

/**
 * Check if user is authenticated.
 */
export function isAuthenticated(): boolean {
    return !!getToken();
}

/**
 * Logout - clear token.
 */
export function logout(): void {
    localStorage.removeItem('token');
    cachedUser = null;
    cachedUserFetchedAt = 0;
    inFlightUserRequest = null;
}

/**
 * Get auth headers for API requests.
 */
export function getAuthHeaders(): Record<string, string> {
    const token = getToken();
    if (!token) return {};
    return { 'Authorization': `Bearer ${token}` };
}
