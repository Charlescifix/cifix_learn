"""
Authentication router for CIFIX LEARN
Simple JWT-based authentication for 10-15 users
"""
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import uuid

from app.database import get_db
from app.models.user import User, Student
from app.core.security import (
    security, 
    create_access_token_for_user, 
    get_password_hash, 
    verify_password,
    validate_password,
    validate_email_format
)
from app.middleware import rate_limit_strict, rate_limit_normal
from app.services.email_service import EmailService

# Router setup
router = APIRouter()
bearer_scheme = HTTPBearer()
email_service = EmailService()

# Pydantic models
class UserRegistration(BaseModel):
    """User registration data"""
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None

class StudentRegistration(BaseModel):
    """Student registration data"""
    student_name: str
    age: int
    grade_level: Optional[str] = None
    school_name: Optional[str] = None
    parent_name: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_conditions: Optional[str] = None
    dietary_restrictions: Optional[str] = None

class CompleteRegistration(BaseModel):
    """Complete registration with user and student data"""
    user: UserRegistration
    student: StudentRegistration

class LoginRequest(BaseModel):
    """Login request data"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    expires_in: int

class UserResponse(BaseModel):
    """User response data"""
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    email_verified: bool
    created_at: datetime

class StudentResponse(BaseModel):
    """Student response data"""
    id: str
    student_name: str
    age: int
    grade_level: Optional[str]
    school_name: Optional[str]

# Dependency: Get current user from token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    payload = security.verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    # Get user ID from payload
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    stmt = select(User).where(User.id == uuid.UUID(user_id), User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@rate_limit_strict(requests=3, window=300)  # 3 registrations per 5 minutes
async def register(
    request: Request,
    registration_data: CompleteRegistration,
    db: AsyncSession = Depends(get_db)
):
    """Register new user with student"""
    
    # Validate email format
    validate_email_format(registration_data.user.email)
    
    # Validate password strength
    validate_password(registration_data.user.password)
    
    # Validate student age
    if not security.validate_student_age(registration_data.student.age):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student age must be between 5 and 18 years"
        )
    
    # Check if user already exists
    stmt = select(User).where(User.email == registration_data.user.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered"
        )
    
    try:
        # Create user
        password_hash = get_password_hash(registration_data.user.password)
        verification_token = security.generate_verification_token()
        
        new_user = User(
            email=registration_data.user.email.lower(),
            password_hash=password_hash,
            first_name=security.sanitize_input(registration_data.user.first_name),
            last_name=security.sanitize_input(registration_data.user.last_name),
            phone=security.sanitize_input(registration_data.user.phone) if registration_data.user.phone else None,
            email_verification_token=verification_token,
            email_verification_expires=datetime.utcnow() + timedelta(hours=24)
        )
        
        db.add(new_user)
        await db.flush()  # Get the user ID
        
        # Create student
        new_student = Student(
            user_id=new_user.id,
            student_name=security.sanitize_input(registration_data.student.student_name),
            age=registration_data.student.age,
            grade_level=security.sanitize_input(registration_data.student.grade_level),
            school_name=security.sanitize_input(registration_data.student.school_name),
            parent_name=security.sanitize_input(registration_data.student.parent_name),
            emergency_contact=security.sanitize_input(registration_data.student.emergency_contact),
            medical_conditions=security.sanitize_input(registration_data.student.medical_conditions),
            dietary_restrictions=security.sanitize_input(registration_data.student.dietary_restrictions)
        )
        
        db.add(new_student)
        await db.commit()
        
        # Send verification email (non-blocking for better UX)
        try:
            await email_service.send_verification_email(
                new_user.email,
                verification_token,
                f"{new_user.first_name} {new_user.last_name}"
            )
        except Exception as e:
            # Log error but don't fail registration
            print(f"Failed to send verification email: {e}")
        
        # Create access token
        access_token = create_access_token_for_user(
            str(new_user.id),
            new_user.email
        )
        
        return TokenResponse(
            access_token=access_token,
            user_id=str(new_user.id),
            email=new_user.email,
            expires_in=3600  # 1 hour
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@router.post("/login", response_model=TokenResponse)
@rate_limit_strict(requests=5, window=300)  # 5 login attempts per 5 minutes
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token"""
    
    # Get user from database
    stmt = select(User).where(User.email == login_data.email.lower(), User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # Check if user exists and password is correct
    if not user or not verify_password(login_data.password, user.password_hash):
        # Increment failed login attempts
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to too many failed login attempts"
        )
    
    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create access token
    access_token = create_access_token_for_user(
        str(user.id),
        user.email
    )
    
    return TokenResponse(
        access_token=access_token,
        user_id=str(user.id),
        email=user.email,
        expires_in=3600
    )

@router.get("/me", response_model=UserResponse)
@rate_limit_normal(requests=20, window=60)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone=current_user.phone,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at
    )

@router.get("/students", response_model=list[StudentResponse])
@rate_limit_normal(requests=20, window=60)
async def get_user_students(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get students for current user"""
    
    stmt = select(Student).where(Student.user_id == current_user.id, Student.is_active == True)
    result = await db.execute(stmt)
    students = result.scalars().all()
    
    return [
        StudentResponse(
            id=str(student.id),
            student_name=student.student_name,
            age=student.age,
            grade_level=student.grade_level,
            school_name=student.school_name
        )
        for student in students
    ]

@router.post("/verify-email/{token}")
@rate_limit_normal(requests=10, window=60)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify user email with token"""
    
    stmt = select(User).where(
        User.email_verification_token == token,
        User.email_verification_expires > datetime.utcnow(),
        User.is_active == True
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Mark email as verified
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    
    await db.commit()
    
    return {"message": "Email verified successfully"}

@router.post("/logout")
@rate_limit_normal(requests=20, window=60)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """Logout user (client should remove token)"""
    
    # In a simple setup, logout is handled client-side
    # In production, you might want to blacklist tokens
    
    return {"message": "Logged out successfully"}