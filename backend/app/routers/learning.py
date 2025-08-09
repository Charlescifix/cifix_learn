"""
Learning router for CIFIX LEARN
Handle learning paths, modules, and progress tracking
"""
from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.database import get_db
from app.models.user import User, Student, LearningPath, LearningModule, StudentModuleProgress
from app.routers.auth import get_current_user
from app.middleware import rate_limit_normal, rate_limit_relaxed
from app.services.learning_service import LearningService
from app.services.analytics_service import AnalyticsService

# Router setup
router = APIRouter()
learning_service = LearningService()
analytics = AnalyticsService()

# Pydantic models
class LearningPathDetail(BaseModel):
    """Detailed learning path information"""
    id: str
    name: str
    slug: str
    description: str
    icon: Optional[str]
    difficulty_level: str
    estimated_hours: int
    sort_order: int
    total_modules: int
    is_active: bool

class ModuleDetail(BaseModel):
    """Detailed module information"""
    id: str
    title: str
    description: str
    content: Optional[str]
    icon: Optional[str]
    difficulty_level: str
    estimated_hours: int
    sort_order: int
    learning_objectives: List[str]
    topics: List[str]
    is_locked: bool
    is_active: bool

class StudentProgress(BaseModel):
    """Student progress on a module"""
    id: str
    module_id: str
    status: str
    progress_percentage: int
    time_spent_minutes: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    last_accessed: datetime
    notes: Optional[str]

class PathWithModules(BaseModel):
    """Learning path with all modules"""
    path: LearningPathDetail
    modules: List[ModuleDetail]
    student_progress: List[StudentProgress]

class ProgressUpdate(BaseModel):
    """Progress update request"""
    progress_percentage: float
    time_spent_minutes: int
    notes: Optional[str] = None
    difficulty_rating: Optional[int] = None
    feedback: Optional[str] = None

class ModuleComplete(BaseModel):
    """Module completion request"""
    final_time_spent: int
    difficulty_rating: Optional[int] = None
    feedback: Optional[str] = None
    project_submission: Optional[str] = None

@router.get("/paths", response_model=List[LearningPathDetail])
@rate_limit_relaxed(requests=50, window=60)
async def get_all_learning_paths(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all available learning paths"""
    
    stmt = select(LearningPath).where(LearningPath.is_active == True).order_by(LearningPath.sort_order)
    result = await db.execute(stmt)
    paths = result.scalars().all()
    
    # Get module counts for each path
    path_details = []
    for path in paths:
        modules_stmt = select(LearningModule).where(
            and_(
                LearningModule.path_id == path.id,
                LearningModule.is_active == True
            )
        )
        modules_result = await db.execute(modules_stmt)
        module_count = len(modules_result.scalars().all())
        
        path_details.append(LearningPathDetail(
            id=str(path.id),
            name=path.name,
            slug=path.slug,
            description=path.description,
            icon=path.icon,
            difficulty_level=path.difficulty_level,
            estimated_hours=path.estimated_hours,
            sort_order=path.sort_order,
            total_modules=module_count,
            is_active=path.is_active
        ))
    
    return path_details

@router.get("/paths/{path_id}", response_model=PathWithModules)
@rate_limit_normal(requests=30, window=60)
async def get_learning_path_detail(
    request: Request,
    path_id: str,
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed learning path with modules and student progress"""
    
    # Verify student belongs to current user
    student_stmt = select(Student).where(
        Student.id == uuid.UUID(student_id),
        Student.user_id == current_user.id,
        Student.is_active == True
    )
    student_result = await db.execute(student_stmt)
    student = student_result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get learning path
    path_stmt = select(LearningPath).where(
        LearningPath.id == uuid.UUID(path_id),
        LearningPath.is_active == True
    )
    path_result = await db.execute(path_stmt)
    path = path_result.scalar_one_or_none()
    
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning path not found"
        )
    
    # Get modules for this path
    modules_stmt = select(LearningModule).where(
        and_(
            LearningModule.path_id == path.id,
            LearningModule.is_active == True
        )
    ).order_by(LearningModule.sort_order)
    
    modules_result = await db.execute(modules_stmt)
    modules = modules_result.scalars().all()
    
    # Get student progress for each module
    progress_stmt = select(StudentModuleProgress).where(
        StudentModuleProgress.student_id == student.id
    )
    progress_result = await db.execute(progress_stmt)
    progress_records = {str(p.module_id): p for p in progress_result.scalars().all()}
    
    # Build module details with progress
    module_details = []
    student_progress = []
    
    for i, module in enumerate(modules):
        # Determine if module is locked
        progress = progress_records.get(str(module.id))
        is_locked = module.is_locked
        
        if progress:
            is_locked = False  # If there's progress, it's unlocked
        elif i == 0:
            is_locked = False  # First module is always unlocked
        else:
            # Check if previous module is completed
            prev_module = modules[i-1]
            prev_progress = progress_records.get(str(prev_module.id))
            is_locked = not (prev_progress and prev_progress.status == "completed")
        
        module_details.append(ModuleDetail(
            id=str(module.id),
            title=module.title,
            description=module.description,
            content=module.content,
            icon=module.icon,
            difficulty_level=module.difficulty_level,
            estimated_hours=module.estimated_hours,
            sort_order=module.sort_order,
            learning_objectives=module.learning_objectives or [],
            topics=module.topics or [],
            is_locked=is_locked,
            is_active=module.is_active
        ))
        
        if progress:
            student_progress.append(StudentProgress(
                id=str(progress.id),
                module_id=str(module.id),
                status=progress.status,
                progress_percentage=progress.progress_percentage,
                time_spent_minutes=progress.time_spent_minutes,
                started_at=progress.started_at,
                completed_at=progress.completed_at,
                last_accessed=progress.last_accessed,
                notes=progress.notes
            ))
    
    # Track path viewing
    await analytics.track_user_action(
        user_id=current_user.id,
        action_type="learning_path_view",
        action_name="Learning Path Viewed",
        metadata={
            "path_id": path_id,
            "path_name": path.name,
            "student_id": student_id
        }
    )
    
    return PathWithModules(
        path=LearningPathDetail(
            id=str(path.id),
            name=path.name,
            slug=path.slug,
            description=path.description,
            icon=path.icon,
            difficulty_level=path.difficulty_level,
            estimated_hours=path.estimated_hours,
            sort_order=path.sort_order,
            total_modules=len(modules),
            is_active=path.is_active
        ),
        modules=module_details,
        student_progress=student_progress
    )

@router.post("/modules/{module_id}/start/{student_id}", response_model=StudentProgress)
@rate_limit_normal(requests=20, window=60)
async def start_module(
    request: Request,
    module_id: str,
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a learning module for a student"""
    
    # Verify student belongs to current user
    student_stmt = select(Student).where(
        Student.id == uuid.UUID(student_id),
        Student.user_id == current_user.id,
        Student.is_active == True
    )
    student_result = await db.execute(student_stmt)
    student = student_result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    try:
        # Use learning service to start module
        progress = await learning_service.start_module(
            student_id=student.id,
            module_id=uuid.UUID(module_id),
            db=db,
            user_id=current_user.id,
            session_id=request.headers.get("x-session-id")
        )
        
        return StudentProgress(
            id=str(progress.id),
            module_id=str(progress.module_id),
            status=progress.status,
            progress_percentage=progress.progress_percentage,
            time_spent_minutes=progress.time_spent_minutes,
            started_at=progress.started_at,
            completed_at=progress.completed_at,
            last_accessed=progress.last_accessed,
            notes=progress.notes
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/modules/{module_id}/progress/{student_id}", response_model=StudentProgress)
@rate_limit_normal(requests=100, window=60)  # Allow frequent progress updates
async def update_module_progress(
    request: Request,
    module_id: str,
    student_id: str,
    progress_data: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update progress on a learning module"""
    
    # Verify student belongs to current user
    student_stmt = select(Student).where(
        Student.id == uuid.UUID(student_id),
        Student.user_id == current_user.id,
        Student.is_active == True
    )
    student_result = await db.execute(student_stmt)
    student = student_result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    try:
        # Use learning service to update progress
        progress = await learning_service.update_module_progress(
            student_id=student.id,
            module_id=uuid.UUID(module_id),
            progress_percentage=progress_data.progress_percentage,
            time_spent_minutes=progress_data.time_spent_minutes,
            notes=progress_data.notes,
            db=db,
            user_id=current_user.id,
            session_id=request.headers.get("x-session-id")
        )
        
        return StudentProgress(
            id=str(progress.id),
            module_id=str(progress.module_id),
            status=progress.status,
            progress_percentage=progress.progress_percentage,
            time_spent_minutes=progress.time_spent_minutes,
            started_at=progress.started_at,
            completed_at=progress.completed_at,
            last_accessed=progress.last_accessed,
            notes=progress.notes
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/modules/{module_id}/complete/{student_id}", response_model=StudentProgress)
@rate_limit_normal(requests=20, window=60)
async def complete_module(
    request: Request,
    module_id: str,
    student_id: str,
    completion_data: ModuleComplete,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a module as completed"""
    
    # Verify student belongs to current user
    student_stmt = select(Student).where(
        Student.id == uuid.UUID(student_id),
        Student.user_id == current_user.id,
        Student.is_active == True
    )
    student_result = await db.execute(student_stmt)
    student = student_result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    try:
        # Use learning service to complete module
        progress = await learning_service.complete_module(
            student_id=student.id,
            module_id=uuid.UUID(module_id),
            final_time_spent=completion_data.final_time_spent,
            difficulty_rating=completion_data.difficulty_rating,
            feedback=completion_data.feedback,
            db=db,
            user_id=current_user.id,
            session_id=request.headers.get("x-session-id")
        )
        
        # Send progress update email (if enabled)
        # This would be implemented with background tasks in production
        
        return StudentProgress(
            id=str(progress.id),
            module_id=str(progress.module_id),
            status=progress.status,
            progress_percentage=progress.progress_percentage,
            time_spent_minutes=progress.time_spent_minutes,
            started_at=progress.started_at,
            completed_at=progress.completed_at,
            last_accessed=progress.last_accessed,
            notes=progress.notes
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/progress/{student_id}", response_model=List[StudentProgress])
@rate_limit_normal(requests=30, window=60)
async def get_student_progress(
    request: Request,
    student_id: str,
    path_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all progress records for a student"""
    
    # Verify student belongs to current user
    student_stmt = select(Student).where(
        Student.id == uuid.UUID(student_id),
        Student.user_id == current_user.id,
        Student.is_active == True
    )
    student_result = await db.execute(student_stmt)
    student = student_result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Build query
    query = select(StudentModuleProgress).where(
        StudentModuleProgress.student_id == student.id
    )
    
    # Filter by path if specified
    if path_id:
        query = query.join(LearningModule).where(
            LearningModule.path_id == uuid.UUID(path_id)
        )
    
    query = query.order_by(StudentModuleProgress.last_accessed.desc())
    
    result = await db.execute(query)
    progress_records = result.scalars().all()
    
    return [
        StudentProgress(
            id=str(progress.id),
            module_id=str(progress.module_id),
            status=progress.status,
            progress_percentage=progress.progress_percentage,
            time_spent_minutes=progress.time_spent_minutes,
            started_at=progress.started_at,
            completed_at=progress.completed_at,
            last_accessed=progress.last_accessed,
            notes=progress.notes
        ) for progress in progress_records
    ]

@router.get("/modules/{module_id}", response_model=ModuleDetail)
@rate_limit_relaxed(requests=50, window=60)
async def get_module_detail(
    request: Request,
    module_id: str,
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed module information"""
    
    # Verify student belongs to current user
    student_stmt = select(Student).where(
        Student.id == uuid.UUID(student_id),
        Student.user_id == current_user.id,
        Student.is_active == True
    )
    student_result = await db.execute(student_stmt)
    student = student_result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get module
    module_stmt = select(LearningModule).where(
        LearningModule.id == uuid.UUID(module_id),
        LearningModule.is_active == True
    )
    module_result = await db.execute(module_stmt)
    module = module_result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    # Check if module is locked for this student
    is_locked = await learning_service._is_module_locked(student.id, module, db)
    
    # Track module viewing
    await analytics.track_content_engagement(
        content_type="module",
        content_id=module_id,
        content_title=module.title,
        student_id=student.id,
        session_id=request.headers.get("x-session-id")
    )
    
    return ModuleDetail(
        id=str(module.id),
        title=module.title,
        description=module.description,
        content=module.content,
        icon=module.icon,
        difficulty_level=module.difficulty_level,
        estimated_hours=module.estimated_hours,
        sort_order=module.sort_order,
        learning_objectives=module.learning_objectives or [],
        topics=module.topics or [],
        is_locked=is_locked,
        is_active=module.is_active
    )

@router.post("/assign-path/{student_id}/{path_id}")
@rate_limit_normal(requests=5, window=300)  # Limited path assignments
async def assign_learning_path(
    request: Request,
    student_id: str,
    path_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Assign a learning path to a student"""
    
    # Verify student belongs to current user
    student_stmt = select(Student).where(
        Student.id == uuid.UUID(student_id),
        Student.user_id == current_user.id,
        Student.is_active == True
    )
    student_result = await db.execute(student_stmt)
    student = student_result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Verify learning path exists
    path_stmt = select(LearningPath).where(
        LearningPath.id == uuid.UUID(path_id),
        LearningPath.is_active == True
    )
    path_result = await db.execute(path_stmt)
    path = path_result.scalar_one_or_none()
    
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning path not found"
        )
    
    try:
        # Use learning service to assign path
        student_path = await learning_service.assign_learning_path(
            student_id=student.id,
            path_id=path.id,
            db=db,
            user_id=current_user.id
        )
        
        return {
            "message": f"Learning path '{path.name}' assigned to {student.student_name}",
            "student_path_id": str(student_path.id),
            "path_name": path.name
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign learning path"
        )

@router.get("/analytics/{student_id}")
@rate_limit_normal(requests=10, window=60)
async def get_learning_analytics(
    request: Request,
    student_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get learning analytics for a student"""
    
    # Verify student belongs to current user
    student_stmt = select(Student).where(
        Student.id == uuid.UUID(student_id),
        Student.user_id == current_user.id,
        Student.is_active == True
    )
    student_result = await db.execute(student_stmt)
    student = student_result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get analytics from service
    analytics_data = await analytics.get_student_learning_analytics(
        student_id=student.id,
        days=days
    )
    
    return analytics_data