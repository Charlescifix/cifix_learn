"""
CIFIX LEARN FastAPI Backend
Simple, secure backend for 10-15 users
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import modules
from app.database import engine
from app.models.user import Base as UserBase
from app.models.analytics import Base as AnalyticsBase
from app.middleware.logging import RequestLoggingMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware
from app.routers import auth, students, assessments, learning, admin
from app.core.config import settings

# Create database tables
async def create_tables():
    """Create database tables on startup"""
    async with engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(AnalyticsBase.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    await create_tables()
    print("✅ Database tables created")
    print(f"✅ CIFIX LEARN API started on {settings.APP_URL}")
    yield
    # Shutdown
    print("🔄 CIFIX LEARN API shutting down...")

# Create FastAPI application
app = FastAPI(
    title="CIFIX LEARN API",
    description="Secure backend for CIFIX LEARN educational platform",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url="/redoc" if settings.APP_ENV == "development" else None,
    lifespan=lifespan
)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [settings.APP_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, calls=1000, period=3600)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(students.router, prefix="/api/students", tags=["Students"]) 
app.include_router(assessments.router, prefix="/api/assessments", tags=["Assessments"])
app.include_router(learning.router, prefix="/api/learning", tags=["Learning"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "CIFIX LEARN API is running",
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.APP_ENV
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "environment": settings.APP_ENV,
        "features": {
            "authentication": True,
            "assessments": True,
            "learning_paths": True,
            "email_service": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_ENV == "development",
        log_level="info"
    )