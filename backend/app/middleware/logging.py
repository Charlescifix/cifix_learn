"""
Logging middleware for CIFIX LEARN
Track requests, responses, and system metrics
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
import logging
from typing import Callable

from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests and track system metrics"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.analytics = AnalyticsService()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate session ID if not present
        session_id = request.headers.get("x-session-id", str(uuid.uuid4()))
        
        # Record request start time
        start_time = time.time()
        
        # Add session ID to request state for other middlewares/routes
        request.state.session_id = session_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            process_time = time.time() - start_time
            response_time_ms = round(process_time * 1000, 2)
            
            # Add response headers
            response.headers["x-process-time"] = str(response_time_ms)
            response.headers["x-session-id"] = session_id
            
            # Log request details
            await self._log_request(
                request=request,
                response=response,
                process_time_ms=response_time_ms,
                session_id=session_id
            )
            
            # Record system metrics (async, don't wait)
            try:
                await self.analytics.record_system_metric(
                    metric_name="response_time",
                    metric_category="performance",
                    metric_value=response_time_ms,
                    metric_unit="ms",
                    endpoint=str(request.url.path),
                    method=request.method,
                    status_code=response.status_code
                )
            except Exception as e:
                logger.error(f"Failed to record system metric: {e}")
            
            return response
            
        except Exception as e:
            # Calculate error response time
            error_time = time.time() - start_time
            error_time_ms = round(error_time * 1000, 2)
            
            # Log error
            await self._log_error(
                request=request,
                error=e,
                process_time_ms=error_time_ms,
                session_id=session_id
            )
            
            # Re-raise the error
            raise e
    
    async def _log_request(
        self,
        request: Request,
        response: Response,
        process_time_ms: float,
        session_id: str
    ):
        """Log successful request"""
        try:
            # Get user ID from request if available (set by auth middleware)
            user_id = getattr(request.state, "user_id", None)
            
            # Extract client info
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            
            # Log basic request info
            logger.info(
                f"{request.method} {request.url.path} - "
                f"{response.status_code} - {process_time_ms}ms - "
                f"IP: {client_ip} - Session: {session_id[:8]}"
            )
            
            # Track page view for frontend routes
            if (request.method == "GET" and 
                not request.url.path.startswith("/api/") and
                response.status_code == 200):
                
                await self.analytics.track_page_view(
                    session_id=session_id,
                    page_path=str(request.url.path),
                    page_title=None,  # Would need to extract from HTML
                    referrer=request.headers.get("referer"),
                    user_id=user_id
                )
            
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
    
    async def _log_error(
        self,
        request: Request,
        error: Exception,
        process_time_ms: float,
        session_id: str
    ):
        """Log error request"""
        try:
            # Get user ID from request if available
            user_id = getattr(request.state, "user_id", None)
            
            # Extract client info
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            
            # Log error
            logger.error(
                f"ERROR - {request.method} {request.url.path} - "
                f"{type(error).__name__}: {str(error)} - "
                f"{process_time_ms}ms - IP: {client_ip} - Session: {session_id[:8]}"
            )
            
            # Track error in analytics
            await self.analytics.log_error(
                error_type=type(error).__name__,
                error_message=str(error),
                error_category="request_processing",
                severity="high" if "Internal Server Error" in str(error) else "medium",
                user_id=user_id,
                session_id=session_id,
                endpoint=str(request.url.path),
                request_method=request.method,
                user_agent=user_agent,
                ip_address=client_ip
            )
            
        except Exception as log_error:
            logger.error(f"Failed to log error: {log_error}")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://streamlit.io; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:; "
                "frame-src https://kid-assessment.streamlit.app; "
                "object-src 'none'; "
                "base-uri 'self';"
            )
        })
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware (basic implementation)"""
    
    def __init__(self, app: ASGIApp, calls: int = 1000, period: int = 3600):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.requests = {}  # In production, use Redis or similar
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for localhost in development
        if client_ip in ["127.0.0.1", "localhost", "::1"]:
            return await call_next(request)
        
        current_time = time.time()
        
        # Clean old requests
        self.requests = {
            ip: times for ip, times in self.requests.items()
            if any(t > current_time - self.period for t in times)
        }
        
        # Check rate limit
        if client_ip in self.requests:
            recent_requests = [
                t for t in self.requests[client_ip]
                if t > current_time - self.period
            ]
            if len(recent_requests) >= self.calls:
                return Response(
                    content="Rate limit exceeded",
                    status_code=429,
                    headers={
                        "Retry-After": str(self.period),
                        "X-RateLimit-Limit": str(self.calls),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(current_time + self.period))
                    }
                )
            
            self.requests[client_ip] = recent_requests + [current_time]
        else:
            self.requests[client_ip] = [current_time]
        
        # Add rate limit headers to response
        response = await call_next(request)
        remaining = max(0, self.calls - len(self.requests[client_ip]))
        
        response.headers.update({
            "X-RateLimit-Limit": str(self.calls),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(current_time + self.period))
        })
        
        return response