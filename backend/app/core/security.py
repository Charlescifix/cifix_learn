"""
Security utilities for CIFIX LEARN
JWT authentication, password hashing, and validation
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings
import secrets
import re

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"

class SecurityService:
    """Security service for authentication and validation"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(seconds=settings.SESSION_TIMEOUT)
            
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET, 
            algorithm=ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET, 
                algorithms=[ALGORITHM]
            )
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength and return feedback"""
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= settings.PASSWORD_MIN_LENGTH:
            score += 2
        else:
            feedback.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        # Uppercase check
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("Password must contain at least one uppercase letter")
        
        # Lowercase check
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("Password must contain at least one lowercase letter")
        
        # Number check
        if re.search(r'[0-9]', password):
            score += 1
        else:
            feedback.append("Password must contain at least one number")
        
        # Special character check
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\?]', password):
            score += 2
        else:
            feedback.append("Password must contain at least one special character")
        
        # Common password check
        common_passwords = ['password', '123456', 'password123', 'admin', 'letmein']
        if password.lower() in common_passwords:
            score = 0
            feedback.append("Password is too common and easily guessed")
        
        is_valid = score >= 5 if settings.REQUIRE_STRONG_PASSWORDS else score >= 2
        
        return {
            "is_valid": is_valid,
            "strength_score": score,
            "feedback": feedback
        }
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate secure verification token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Basic input sanitization"""
        if not input_str:
            return ""
        
        # Remove null bytes and normalize whitespace
        sanitized = input_str.replace('\x00', '').strip()
        
        # Limit length to prevent DoS
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000]
        
        return sanitized
    
    @staticmethod
    def validate_student_age(age: int) -> bool:
        """Validate student age is within acceptable range"""
        return 5 <= age <= 18

# Create security service instance
security = SecurityService()

# Helper functions for dependency injection
def create_access_token_for_user(user_id: str, email: str) -> str:
    """Create access token for specific user"""
    token_data = {
        "sub": str(user_id),
        "email": email,
        "type": "access"
    }
    return security.create_access_token(token_data)

def get_password_hash(password: str) -> str:
    """Get password hash"""
    return security.hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return security.verify_password(plain_password, hashed_password)

def validate_password(password: str) -> None:
    """Validate password and raise exception if invalid"""
    validation = security.validate_password_strength(password)
    
    if not validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Password does not meet requirements",
                "feedback": validation["feedback"]
            }
        )

def validate_email_format(email: str) -> None:
    """Validate email format and raise exception if invalid"""
    if not security.validate_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )