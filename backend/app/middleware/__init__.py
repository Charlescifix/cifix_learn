"""
Middleware for CIFIX LEARN
Custom middleware for logging, security, and rate limiting
"""
from .logging import RequestLoggingMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware

# Rate limiting decorators for specific endpoints
from functools import wraps
import time
from typing import Dict, Callable
from fastapi import HTTPException, status, Request

# Simple in-memory rate limiter (use Redis in production)
_rate_limit_storage: Dict[str, Dict[str, float]] = {}

def rate_limit_normal(requests: int = 30, window: int = 60):
    """Rate limiter for normal endpoints"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get identifier (could be user ID, IP, etc.)
            client_ip = request.client.host if request.client else "unknown"
            user_id = getattr(request.state, "user_id", None)
            identifier = str(user_id) if user_id else client_ip
            
            # Skip rate limiting for localhost
            if client_ip in ["127.0.0.1", "localhost", "::1"]:
                return await func(request, *args, **kwargs)
            
            current_time = time.time()
            key = f"{func.__name__}:{identifier}"
            
            # Initialize or clean old requests
            if key not in _rate_limit_storage:
                _rate_limit_storage[key] = {}
            
            # Remove old entries
            _rate_limit_storage[key] = {
                timestamp: count for timestamp, count in _rate_limit_storage[key].items()
                if current_time - timestamp < window
            }
            
            # Count requests in current window
            total_requests = sum(_rate_limit_storage[key].values())
            
            if total_requests >= requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Too many requests."
                )
            
            # Record this request
            window_start = int(current_time // window) * window
            _rate_limit_storage[key][window_start] = _rate_limit_storage[key].get(window_start, 0) + 1
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def rate_limit_relaxed(requests: int = 100, window: int = 60):
    """Rate limiter for relaxed endpoints (more requests allowed)"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get identifier
            client_ip = request.client.host if request.client else "unknown"
            user_id = getattr(request.state, "user_id", None)
            identifier = str(user_id) if user_id else client_ip
            
            # Skip rate limiting for localhost
            if client_ip in ["127.0.0.1", "localhost", "::1"]:
                return await func(request, *args, **kwargs)
            
            current_time = time.time()
            key = f"{func.__name__}:{identifier}"
            
            # Initialize or clean old requests
            if key not in _rate_limit_storage:
                _rate_limit_storage[key] = {}
            
            # Remove old entries
            _rate_limit_storage[key] = {
                timestamp: count for timestamp, count in _rate_limit_storage[key].items()
                if current_time - timestamp < window
            }
            
            # Count requests in current window
            total_requests = sum(_rate_limit_storage[key].values())
            
            if total_requests >= requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Too many requests."
                )
            
            # Record this request
            window_start = int(current_time // window) * window
            _rate_limit_storage[key][window_start] = _rate_limit_storage[key].get(window_start, 0) + 1
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def rate_limit_strict(requests: int = 10, window: int = 60):
    """Rate limiter for strict endpoints (fewer requests allowed)"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get identifier
            client_ip = request.client.host if request.client else "unknown"
            user_id = getattr(request.state, "user_id", None)
            identifier = str(user_id) if user_id else client_ip
            
            # Skip rate limiting for localhost
            if client_ip in ["127.0.0.1", "localhost", "::1"]:
                return await func(request, *args, **kwargs)
            
            current_time = time.time()
            key = f"{func.__name__}:{identifier}"
            
            # Initialize or clean old requests
            if key not in _rate_limit_storage:
                _rate_limit_storage[key] = {}
            
            # Remove old entries
            _rate_limit_storage[key] = {
                timestamp: count for timestamp, count in _rate_limit_storage[key].items()
                if current_time - timestamp < window
            }
            
            # Count requests in current window
            total_requests = sum(_rate_limit_storage[key].values())
            
            if total_requests >= requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Too many requests."
                )
            
            # Record this request
            window_start = int(current_time // window) * window
            _rate_limit_storage[key][window_start] = _rate_limit_storage[key].get(window_start, 0) + 1
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

__all__ = [
    "RequestLoggingMiddleware",
    "SecurityHeadersMiddleware", 
    "RateLimitMiddleware",
    "rate_limit_normal",
    "rate_limit_relaxed",
    "rate_limit_strict"
]