/**
 * TaskFlow — Centralized Authentication & Session Management
 * 
 * Secure Frontend Practices:
 * - The JWT secret is NEVER exposed to client-side code; it stays on the backend.
 * - The browser only receives the signed token and stores it in localStorage.
 * - All authenticated requests attach the token via the HTTP "Authorization: Bearer <token>" header.
 */

const TOKEN_STORAGE_KEY = "taskflow_access_token";
const USER_STORAGE_KEY = "taskflow_user_profile";

// Determine API Base URL
const API_BASE = window.location.origin.startsWith("http")
    ? window.location.origin
    : "http://127.0.0.1:8000";

const Auth = {
    /**
     * Retrieves the stored JWT access token.
     */
    getToken() {
        return localStorage.getItem(TOKEN_STORAGE_KEY);
    },

    /**
     * Retrieves the stored user profile data.
     */
    getUser() {
        const raw = localStorage.getItem(USER_STORAGE_KEY);
        try {
            return raw ? JSON.parse(raw) : null;
        } catch {
            return null;
        }
    },

    /**
     * Saves session upon successful login.
     */
    saveSession(token, user) {
        localStorage.setItem(TOKEN_STORAGE_KEY, token);
        if (user) {
            localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
        }
    },

    /**
     * Clears all session credentials (used during sign out or token expiration).
     */
    clearSession() {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(USER_STORAGE_KEY);
    },

    /**
     * Checks if a token exists in local storage.
     */
    isAuthenticated() {
        return Boolean(this.getToken());
    },

    /**
     * Authenticated fetch wrapper.
     * Automatically attaches the "Authorization: Bearer <token>" header.
     * If the backend returns 401 Unauthorized (e.g. token expired),
     * it automatically clears the session and redirects to login.
     */
    async authFetch(endpoint, options = {}) {
        const token = this.getToken();
        const headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            ...(options.headers || {})
        };

        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;
        const response = await fetch(url, { ...options, headers });

        if (response.status === 401) {
            console.warn("Session expired or unauthorized. Redirecting to login...");
            this.clearSession();
            // Redirect to login page if not already there
            if (!window.location.pathname.endsWith("login.html")) {
                window.location.href = "login.html?expired=true";
            }
        }

        return response;
    },

    /**
     * Signs out the user and redirects to login.
     */
    logout() {
        this.clearSession();
        window.location.href = "login.html";
    }
};

window.Auth = Auth;
