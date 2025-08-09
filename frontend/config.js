/**
 * Frontend Configuration for CIFIX LEARN
 * Production-ready settings with security and performance optimizations
 */

// Environment detection
const isDevelopment = window.location.hostname === 'localhost' || 
                     window.location.hostname === '127.0.0.1' ||
                     window.location.hostname.includes('railway.app');
const isProduction = !isDevelopment;

// API Configuration
const CONFIG = {
    // API Endpoints
    API: {
        BASE_URL: isDevelopment 
            ? 'http://localhost:8000/api' 
            : 'https://your-railway-domain.railway.app/api',
        TIMEOUT: 10000, // 10 seconds
        RETRY_ATTEMPTS: 3,
        RETRY_DELAY: 1000 // 1 second
    },
    
    // Authentication
    AUTH: {
        TOKEN_KEY: 'cifix_access_token',
        REFRESH_KEY: 'cifix_refresh_token',
        USER_KEY: 'cifix_current_user',
        TOKEN_EXPIRY_BUFFER: 300, // 5 minutes before expiry
        REMEMBER_ME_DAYS: 7,
        AUTO_LOGOUT_MINUTES: 60 // Auto logout after inactivity
    },
    
    // Security Settings
    SECURITY: {
        ENABLE_XSS_PROTECTION: true,
        SANITIZE_INPUT: true,
        VALIDATE_RESPONSES: true,
        SECURE_COOKIES: isProduction,
        HTTPS_ONLY: isProduction,
        CSRF_PROTECTION: false, // JWT-based API
        CSP_ENABLED: true
    },
    
    // Rate Limiting (Client-side protection)
    RATE_LIMITING: {
        LOGIN_ATTEMPTS: 5,
        LOGIN_WINDOW_MINUTES: 5,
        FORM_SUBMISSIONS: 3,
        FORM_WINDOW_MINUTES: 1,
        API_CALLS_PER_MINUTE: 60
    },
    
    // UI Configuration
    UI: {
        ANIMATION_DURATION: 300,
        TOAST_DURATION: 5000,
        LOADING_TIMEOUT: 30000,
        DEBOUNCE_DELAY: 300,
        PAGINATION_SIZE: 20,
        MAX_FILE_SIZE_MB: 5,
        ALLOWED_FILE_TYPES: ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.png']
    },
    
    // Form Validation
    VALIDATION: {
        PASSWORD_MIN_LENGTH: 8,
        EMAIL_MAX_LENGTH: 254,
        NAME_MAX_LENGTH: 100,
        PHONE_MAX_LENGTH: 20,
        TEXT_MAX_LENGTH: 1000,
        REQUIRE_STRONG_PASSWORDS: true,
        VALIDATE_ON_BLUR: true,
        SHOW_STRENGTH_METER: true
    },
    
    // Local Storage Keys
    STORAGE_KEYS: {
        THEME: 'cifix_theme',
        LANGUAGE: 'cifix_language',
        PREFERENCES: 'cifix_user_preferences',
        REGISTRATION_DATA: 'completeRegistration',
        ASSESSMENT_RESULTS: 'assessmentResults',
        LEARNING_PROGRESS: 'learningProgress'
    },
    
    // External Services
    EXTERNAL: {
        ASSESSMENT_TOOL_URL: 'https://kid-assessment.streamlit.app',
        SUPPORT_EMAIL: 'support@cifixlearn.com',
        CONTACT_PHONE: '+1-555-123-4567'
    },
    
    // Performance Settings
    PERFORMANCE: {
        ENABLE_CACHING: true,
        CACHE_DURATION_HOURS: 24,
        LAZY_LOAD_IMAGES: true,
        COMPRESS_REQUESTS: true,
        ENABLE_SERVICE_WORKER: isProduction,
        PREFETCH_RESOURCES: true
    },
    
    // Error Handling
    ERROR_HANDLING: {
        SHOW_DETAILED_ERRORS: isDevelopment,
        LOG_ERRORS_TO_CONSOLE: isDevelopment,
        SEND_ERROR_REPORTS: isProduction,
        RETRY_ON_NETWORK_ERROR: true,
        FALLBACK_MESSAGES: {
            NETWORK_ERROR: 'Network connection issue. Please check your internet connection.',
            SERVER_ERROR: 'Server temporarily unavailable. Please try again later.',
            VALIDATION_ERROR: 'Please check your input and try again.',
            AUTH_ERROR: 'Session expired. Please log in again.',
            PERMISSION_ERROR: 'You do not have permission to perform this action.',
            RATE_LIMIT_ERROR: 'Too many requests. Please wait a moment and try again.'
        }
    },
    
    // Feature Flags
    FEATURES: {
        ENABLE_DARK_MODE: true,
        ENABLE_NOTIFICATIONS: true,
        ENABLE_ANALYTICS: isProduction,
        ENABLE_BETA_FEATURES: isDevelopment,
        ENABLE_ACCESSIBILITY: true,
        ENABLE_PWA: isProduction,
        ENABLE_OFFLINE_MODE: false
    },
    
    // Development Settings
    DEBUG: {
        ENABLED: isDevelopment,
        LOG_LEVEL: isDevelopment ? 'debug' : 'error',
        SHOW_PERFORMANCE_METRICS: isDevelopment,
        ENABLE_REDUX_DEVTOOLS: isDevelopment,
        MOCK_API_DELAY: 0 // ms delay for development
    }
};

// Security helper functions
const SecurityHelpers = {
    /**
     * Sanitize user input to prevent XSS
     */
    sanitizeInput(input) {
        if (typeof input !== 'string') return input;
        
        return input
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#x27;')
            .replace(/\//g, '&#x2F;');
    },
    
    /**
     * Validate email format
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    /**
     * Check password strength
     */
    checkPasswordStrength(password) {
        const checks = {
            length: password.length >= CONFIG.VALIDATION.PASSWORD_MIN_LENGTH,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /\d/.test(password),
            special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\?]/.test(password)
        };
        
        const score = Object.values(checks).filter(Boolean).length;
        
        return {
            score,
            checks,
            strength: score < 3 ? 'weak' : score < 5 ? 'medium' : 'strong',
            isValid: CONFIG.VALIDATION.REQUIRE_STRONG_PASSWORDS ? score >= 4 : score >= 2
        };
    },
    
    /**
     * Generate secure random string
     */
    generateSecureId() {
        return crypto.getRandomValues(new Uint32Array(2)).join('');
    }
};

// API helper functions
const APIHelpers = {
    /**
     * Get authentication headers
     */
    getAuthHeaders() {
        const token = localStorage.getItem(CONFIG.AUTH.TOKEN_KEY);
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    },
    
    /**
     * Handle API errors consistently
     */
    handleError(error) {
        if (error.response) {
            // Server responded with error status
            const status = error.response.status;
            const message = error.response.data?.detail || error.response.data?.message || 'Server error';
            
            switch (status) {
                case 401:
                    this.handleAuthError();
                    return CONFIG.ERROR_HANDLING.FALLBACK_MESSAGES.AUTH_ERROR;
                case 403:
                    return CONFIG.ERROR_HANDLING.FALLBACK_MESSAGES.PERMISSION_ERROR;
                case 429:
                    return CONFIG.ERROR_HANDLING.FALLBACK_MESSAGES.RATE_LIMIT_ERROR;
                case 422:
                    return message; // Validation error
                default:
                    return CONFIG.ERROR_HANDLING.FALLBACK_MESSAGES.SERVER_ERROR;
            }
        } else if (error.request) {
            // Network error
            return CONFIG.ERROR_HANDLING.FALLBACK_MESSAGES.NETWORK_ERROR;
        } else {
            // Other error
            return CONFIG.ERROR_HANDLING.FALLBACK_MESSAGES.VALIDATION_ERROR;
        }
    },
    
    /**
     * Handle authentication errors
     */
    handleAuthError() {
        // Clear authentication data
        localStorage.removeItem(CONFIG.AUTH.TOKEN_KEY);
        localStorage.removeItem(CONFIG.AUTH.REFRESH_KEY);
        localStorage.removeItem(CONFIG.AUTH.USER_KEY);
        
        // Redirect to login if not already there
        if (window.location.pathname !== '/login.html') {
            window.location.href = '/login.html';
        }
    },
    
    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        const token = localStorage.getItem(CONFIG.AUTH.TOKEN_KEY);
        if (!token) return false;
        
        try {
            // Check if token is expired (basic check)
            const payload = JSON.parse(atob(token.split('.')[1]));
            const currentTime = Date.now() / 1000;
            return payload.exp > currentTime + CONFIG.AUTH.TOKEN_EXPIRY_BUFFER;
        } catch (error) {
            return false;
        }
    }
};

// Initialize security features
if (CONFIG.SECURITY.CSP_ENABLED && isProduction) {
    // Add Content Security Policy via meta tag if not set by server
    if (!document.querySelector('meta[http-equiv="Content-Security-Policy"]')) {
        const cspMeta = document.createElement('meta');
        cspMeta.httpEquiv = 'Content-Security-Policy';
        cspMeta.content = "default-src 'self'; script-src 'self' 'unsafe-inline' https://kid-assessment.streamlit.app; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://kid-assessment.streamlit.app; frame-src https://kid-assessment.streamlit.app;";
        document.head.appendChild(cspMeta);
    }
}

// Export configuration
window.CIFIX_CONFIG = CONFIG;
window.CIFIX_SECURITY = SecurityHelpers;
window.CIFIX_API = APIHelpers;

// Log configuration status in development
if (isDevelopment) {
    console.log('🚀 CIFIX LEARN Frontend Configuration Loaded');
    console.log('Environment:', isDevelopment ? 'Development' : 'Production');
    console.log('API Base URL:', CONFIG.API.BASE_URL);
    console.log('Security Features:', Object.keys(CONFIG.SECURITY).filter(key => CONFIG.SECURITY[key]));
}

// Production-ready service worker registration
if (CONFIG.FEATURES.ENABLE_PWA && 'serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
            .then(registration => {
                if (CONFIG.DEBUG.ENABLED) {
                    console.log('SW registered: ', registration);
                }
            })
            .catch(registrationError => {
                if (CONFIG.DEBUG.ENABLED) {
                    console.log('SW registration failed: ', registrationError);
                }
            });
    });
}