"""
Middleware for CIFIX LEARN FastAPI application
CORS, security headers, rate limiting for small-scale deployment
"""
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import time
from typing import Dict
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Simple in-memory store for rate limiting (suitable for 10-15 users)
limiter = Limiter(key_func=get_remote_address)

# Request tracking for simple analytics
request_stats: Dict[str, int] = {}

def setup_middleware(app: FastAPI):
    """Set up all middleware for the FastAPI application"""
    
    # Add trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "cifixlearn.online", "*.cifixlearn.online"]
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Rate-Limit-Remaining"]
    )
    
    # Add rate limiting middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    # Add custom security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses"""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add HSTS in production
        if settings.APP_ENV == "production":
            response.headers["Strict-Transport-Security"] = f"max-age={settings.HSTS_MAX_AGE}; includeSubDomains"
        
        # Add CSP header
        response.headers["Content-Security-Policy"] = settings.CSP_POLICY
        
        # Add processing time header (helpful for monitoring)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log requests for monitoring (simple approach for small scale)"""
        
        # Track request stats (simple in-memory for 10-15 users)
        endpoint = f"{request.method} {request.url.path}"
        request_stats[endpoint] = request_stats.get(endpoint, 0) + 1
        
        # Log request (in production, use proper logging service)
        if settings.APP_ENV == "development":
            logger.info(f"Request: {request.method} {request.url.path} from {get_remote_address(request)}")
        
        # Process request
        response = await call_next(request)
        
        # Log response status
        if response.status_code >= 400:
            logger.warning(f"Error response: {response.status_code} for {request.method} {request.url.path}")
        
        return response
    
    # Add simple authentication middleware for protected routes
    @app.middleware("http")
    async def check_maintenance_mode(request: Request, call_next):
        """Check if application is in maintenance mode"""
        
        # Skip health check and docs
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # In a real application, this would check a database setting
        # For now, we'll use environment variable
        maintenance_mode = False  # Could be loaded from database or config
        
        if maintenance_mode and not request.url.path.startswith("/api/admin"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="CIFIX LEARN is temporarily under maintenance. Please try again later."
            )
        
        return await call_next(request)

# Rate limiting decorators for different endpoint types
def rate_limit_strict(requests: int = 5, window: int = 60):
    """Strict rate limiting for sensitive endpoints like login"""
    return limiter.limit(f"{requests}/{window}second")

def rate_limit_normal(requests: int = 30, window: int = 60):
    """Normal rate limiting for regular API endpoints"""
    return limiter.limit(f"{requests}/{window}second")

def rate_limit_relaxed(requests: int = 100, window: int = 60):
    """Relaxed rate limiting for read-only endpoints"""
    return limiter.limit(f"{requests}/{window}second")

# Simple request stats endpoint (for monitoring)
def get_request_stats() -> Dict[str, int]:
    """Get simple request statistics"""
    return request_stats.copy()

def reset_request_stats():
    """Reset request statistics"""
    global request_stats
    request_stats.clear()