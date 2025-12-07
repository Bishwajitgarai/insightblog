// Authentication helper for JWT token management

class AuthService {
    constructor() {
        this.TOKEN_KEY = 'jwt_token';
        this.REFRESH_TOKEN_KEY = 'refresh_token';
    }

    // Store tokens
    setTokens(accessToken, refreshToken) {
        localStorage.setItem(this.TOKEN_KEY, accessToken);
        if (refreshToken) {
            localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
        }
    }

    // Get access token
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    // Get refresh token
    getRefreshToken() {
        return localStorage.getItem(this.REFRESH_TOKEN_KEY);
    }

    // Remove tokens (logout)
    clearTokens() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    }

    // Check if user is authenticated
    isAuthenticated() {
        return !!this.getToken();
    }

    // Get auth headers for API calls
    getAuthHeaders() {
        const token = this.getToken();
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }

    // API call wrapper with automatic auth headers
    async apiCall(url, options = {}) {
        const headers = {
            ...this.getAuthHeaders(),
            ...options.headers
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        // Handle 401 - token expired
        if (response.status === 401) {
            // Try to refresh token
            const refreshed = await this.refreshAccessToken();
            if (refreshed) {
                // Retry the original request
                const retryHeaders = {
                    ...this.getAuthHeaders(),
                    ...options.headers
                };
                return fetch(url, {
                    ...options,
                    headers: retryHeaders
                });
            } else {
                // Refresh failed, redirect to login
                this.clearTokens();
                window.location.href = '/login';
                throw new Error('Session expired');
            }
        }

        return response;
    }

    // Refresh access token
    async refreshAccessToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) return false;

        try {
            const response = await fetch('/api/v1/users/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                this.setTokens(data.access_token, data.refresh_token);
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }
        return false;
    }

    // Login
    async login(email, password) {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch('/api/v1/users/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            this.setTokens(data.access_token, data.refresh_token);
            return { success: true, data };
        } else {
            const error = await response.json();
            return { success: false, error: error.detail || 'Login failed' };
        }
    }

    // Register
    async register(email, fullName, password) {
        const response = await fetch('/api/v1/users/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email,
                full_name: fullName,
                password
            })
        });

        if (response.ok) {
            const data = await response.json();
            // Auto-login after registration
            return await this.login(email, password);
        } else {
            const error = await response.json();
            return { success: false, error: error.detail || 'Registration failed' };
        }
    }

    // Logout
    logout() {
        this.clearTokens();
        window.location.href = '/login';
    }
}

// Create global auth service instance
const authService = new AuthService();

// Helper function for toast notifications
function showToast(message, type = 'info') {
    // Simple alert for now, can be replaced with a toast library
    if (type === 'error') {
        alert('Error: ' + message);
    } else {
        alert(message);
    }
}
