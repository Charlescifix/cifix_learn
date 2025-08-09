"""
Configuration settings for CIFIX LEARN
Loads all settings from environment variables
"""
from pydantic_settings import BaseSettings
from pydantic import validator
from typing import List
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application Settings
    APP_NAME: str = "CIFIX LEARN"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_URL: str = "http://localhost:8000"
    
    # Database Settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "cifix_learn"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    DATABASE_URL: str = ""
    
    # Security Settings
    JWT_SECRET: str
    ENCRYPTION_KEY: str
    BCRYPT_ROUNDS: int = 12
    SESSION_TIMEOUT: int = 86400  # 24 hours
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION: int = 1800  # 30 minutes
    
    # Password Requirements
    PASSWORD_MIN_LENGTH: int = 8
    REQUIRE_STRONG_PASSWORDS: bool = True
    
    # Email Settings (AWS SES) - Optional for basic functionality
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    SES_SOURCE_EMAIL: str = "noreply@localhost"
    SES_REPLY_TO_EMAIL: str = ""
    SES_CONFIGURATION_SET: str = ""
    
    # API Keys (Optional for basic functionality)
    OPENAI_API_KEY: str = ""
    
    # CORS Settings
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,https://cifixlearn.online"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 900  # 15 minutes
    
    # Feature Flags
    ENABLE_EMAIL_VERIFICATION: bool = True
    ENABLE_ANALYTICS: bool = True
    
    # External Services
    ASSESSMENT_TOOL_URL: str = "https://kid-assessment.streamlit.app"
    
    @validator("DATABASE_URL", pre=True)
    def build_database_url(cls, v, values):
        """Build PostgreSQL database URL from components"""
        if v:
            return v
        
        return f"postgresql://{values['DB_USER']}:{values['DB_PASSWORD']}@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}"
    
    @validator("CORS_ALLOWED_ORIGINS", pre=False)
    def parse_cors_origins(cls, v):
        """Parse CORS origins into list"""
        if isinstance(v, str):
            return v  # Keep as string for FastAPI CORS middleware
        return v
    
    @validator("JWT_SECRET")
    def validate_jwt_secret(cls, v):
        """Ensure JWT secret is set and strong"""
        if not v:
            raise ValueError("JWT_SECRET must be set in environment variables")
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v
    
    @validator("ENCRYPTION_KEY")
    def validate_encryption_key(cls, v):
        """Ensure encryption key is set"""
        if not v:
            raise ValueError("ENCRYPTION_KEY must be set in environment variables")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validation on startup
def validate_settings():
    """Validate critical settings on startup"""
    required_fields = [
        "JWT_SECRET", 
        "ENCRYPTION_KEY"
    ]
    
    missing_fields = []
    for field in required_fields:
        if not getattr(settings, field, None):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")
    
    print("[OK] All required environment variables are set")
    return True

# Validate settings on import
try:
    validate_settings()
except ValueError as e:
    print(f"[ERROR] Configuration Error: {e}")
    print("Please check your .env file and ensure all required variables are set")
    exit(1)