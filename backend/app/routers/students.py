"""
Student management router for CIFIX LEARN
Handle student profiles, progress, and dashboard data
"""
from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.database import get_db
from app.models.user import User, Student, StudentLearningPath, StudentModuleProgress, LearningPath, LearningModule, StudentAchievement, AchievementType
from app.models.analytics import UserAction, LearningAnalytics
from app.routers.auth import get_current_user
from app.middleware import rate_limit_normal, rate_limit_relaxed
from app.services.analytics_service import AnalyticsService

# Router setup
router = APIRouter()
analytics = AnalyticsService()

# Pydantic models
class StudentProfile(BaseModel):
    """Student profile response"""
    id: str
    student_name: str
    age: int
    grade_level: Optional[str]
    school_name: Optional[str]
    parent_name: Optional[str]
    emergency_contact: Optional[str]
    medical_conditions: Optional[str]
    dietary_restrictions: Optional[str]
    created_at: datetime
    
class LearningPathSummary(BaseModel):
    """Learning path summary"""
    id: str
    name: str
    slug: str
    description: str
    icon: Optional[str]
    difficulty_level: str
    estimated_hours: int
    progress_percentage: int
    is_active: bool

class ModuleProgress(BaseModel):
    """Module progress details"""
    id: str
    module_id: str
    title: str
    description: str
    icon: Optional[str]
    difficulty_level: str
    estimated_hours: int
    sort_order: int
    status: str
    progress_percentage: int
    time_spent_minutes: int
    is_locked: bool
    learning_objectives: List[str]
    topics: List[str]

class Achievement(BaseModel):
    """Achievement details"""
    id: str
    name: str
    description: str
    icon: Optional[str]
    badge_color: Optional[str]
    points: int
    earned_at: datetime

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_courses: int
    completed_modules: int
    total_modules: int
    hours_spent: int
    achievements_count: int
    current_streak: int
    
class StudentDashboard(BaseModel):
    """Complete student dashboard data"""
    student: StudentProfile
    stats: DashboardStats
    current_path: Optional[LearningPathSummary]
    module_progress: List[ModuleProgress]
    recent_achievements: List[Achievement]
    available_paths: List[LearningPathSummary]

class UpdateStudentProfile(BaseModel):
    """Update student profile data"""
    student_name: Optional[str] = None
    age: Optional[int] = None
    grade_level: Optional[str] = None
    school_name: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_conditions: Optional[str] = None
    dietary_restrictions: Optional[str] = None

@router.get("/dashboard/{student_id}", response_model=StudentDashboard)
@rate_limit_normal(requests=30, window=60)
async def get_student_dashboard(
    request: Request,
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get complete student dashboard data"""
    
    # Verify student belongs to current user
    stmt = select(Student).where(
        Student.id == uuid.UUID(student_id),
        Student.user_id == current_user.id,
        Student.is_active == True
    )
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Track dashboard view
    await analytics.track_user_action(
        user_id=current_user.id,
        action_type="dashboard_view",
        action_name="Student Dashboard Accessed",
        metadata={"student_id": student_id}
    )
    
    # Get student's current learning path
    current_path_stmt = select(StudentLearningPath).options(
        selectinload(StudentLearningPath.path)
    ).where(
        StudentLearningPath.student_id == student.id,
        StudentLearningPath.is_active == True
    ).order_by(StudentLearningPath.assigned_at.desc())
    
    current_path_result = await db.execute(current_path_stmt)
    student_path = current_path_result.scalar_one_or_none()
    
    # Get module progress for current path
    module_progress = []
    if student_path:
        modules_stmt = select(LearningModule).where(
            LearningModule.path_id == student_path.path_id,
            LearningModule.is_active == True
        ).order_by(LearningModule.sort_order)
        
        modules_result = await db.execute(modules_stmt)
        modules = modules_result.scalars().all()
        
        for module in modules:
            # Get progress for this module
            progress_stmt = select(StudentModuleProgress).where(
                StudentModuleProgress.student_id == student.id,
                StudentModuleProgress.module_id == module.id
            )
            progress_result = await db.execute(progress_stmt)
            progress = progress_result.scalar_one_or_none()
            
            # Determine if module is locked
            is_locked = module.is_locked
            if progress:
                is_locked = False  # If there's progress, it's unlocked
            elif module.sort_order == 1:
                is_locked = False  # First module is always unlocked
            else:
                # Check if previous module is completed
                prev_module_stmt = select(StudentModuleProgress).join(LearningModule).where(
                    StudentModuleProgress.student_id == student.id,
                    LearningModule.path_id == student_path.path_id,
                    LearningModule.sort_order == module.sort_order - 1,
                    StudentModuleProgress.status == "completed"
                )
                prev_result = await db.execute(prev_module_stmt)
                prev_progress = prev_result.scalar_one_or_none()
                is_locked = prev_progress is None
            
            module_progress.append(ModuleProgress(
                id=str(progress.id) if progress else str(uuid.uuid4()),
                module_id=str(module.id),
                title=module.title,
                description=module.description,
                icon=module.icon,
                difficulty_level=module.difficulty_level,
                estimated_hours=module.estimated_hours,
                sort_order=module.sort_order,
                status=progress.status if progress else "not_started",
                progress_percentage=progress.progress_percentage if progress else 0,
                time_spent_minutes=progress.time_spent_minutes if progress else 0,
                is_locked=is_locked,
                learning_objectives=module.learning_objectives or [],
                topics=module.topics or []
            ))
    
    # Get dashboard statistics
    total_modules_stmt = select(func.count(LearningModule.id)).join(StudentLearningPath).where(
        StudentLearningPath.student_id == student.id,
        StudentLearningPath.is_active == True,
        LearningModule.is_active == True
    )
    total_modules_result = await db.execute(total_modules_stmt)
    total_modules = total_modules_result.scalar() or 0
    
    completed_modules_stmt = select(func.count(StudentModuleProgress.id)).where(
        StudentModuleProgress.student_id == student.id,
        StudentModuleProgress.status == "completed"
    )
    completed_modules_result = await db.execute(completed_modules_stmt)
    completed_modules = completed_modules_result.scalar() or 0
    
    total_hours_stmt = select(func.coalesce(func.sum(StudentModuleProgress.time_spent_minutes), 0)).where(
        StudentModuleProgress.student_id == student.id
    )
    total_hours_result = await db.execute(total_hours_stmt)
    total_minutes = total_hours_result.scalar() or 0
    total_hours = total_minutes // 60
    
    # Get achievements count
    achievements_stmt = select(func.count(StudentAchievement.id)).where(
        StudentAchievement.student_id == student.id
    )
    achievements_result = await db.execute(achievements_stmt)
    achievements_count = achievements_result.scalar() or 0
    
    # Get recent achievements
    recent_achievements_stmt = select(StudentAchievement).options(
        selectinload(StudentAchievement.achievement_type)
    ).where(
        StudentAchievement.student_id == student.id
    ).order_by(StudentAchievement.earned_at.desc()).limit(5)
    
    recent_achievements_result = await db.execute(recent_achievements_stmt)
    recent_achievements_data = recent_achievements_result.scalars().all()
    
    recent_achievements = [
        Achievement(
            id=str(ach.id),
            name=ach.achievement_type.name,
            description=ach.achievement_type.description,
            icon=ach.achievement_type.icon,
            badge_color=ach.achievement_type.badge_color,
            points=ach.achievement_type.points,
            earned_at=ach.earned_at
        ) for ach in recent_achievements_data
    ]
    
    # Get available learning paths
    all_paths_stmt = select(LearningPath).where(LearningPath.is_active == True).order_by(LearningPath.sort_order)
    all_paths_result = await db.execute(all_paths_stmt)
    all_paths = all_paths_result.scalars().all()
    
    available_paths = [
        LearningPathSummary(
            id=str(path.id),
            name=path.name,
            slug=path.slug,
            description=path.description,
            icon=path.icon,
            difficulty_level=path.difficulty_level,
            estimated_hours=path.estimated_hours,
            progress_percentage=student_path.progress_percentage if (student_path and student_path.path_id == path.id) else 0,
            is_active=True
        ) for path in all_paths
    ]
    
    # Build dashboard response
    dashboard = StudentDashboard(
        student=StudentProfile(
            id=str(student.id),
            student_name=student.student_name,
            age=student.age,
            grade_level=student.grade_level,
            school_name=student.school_name,
            parent_name=student.parent_name,
            emergency_contact=student.emergency_contact,
            medical_conditions=student.medical_conditions,
            dietary_restrictions=student.dietary_restrictions,
            created_at=student.created_at
        ),
        stats=DashboardStats(
            total_courses=1 if student_path else 0,
            completed_modules=completed_modules,
            total_modules=total_modules,
            hours_spent=total_hours,
            achievements_count=achievements_count,
            current_streak=0  # TODO: Implement streak calculation
        ),
        current_path=LearningPathSummary(
            id=str(student_path.path.id),
            name=student_path.path.name,
            slug=student_path.path.slug,
            description=student_path.path.description,
            icon=student_path.path.icon,
            difficulty_level=student_path.path.difficulty_level,
            estimated_hours=student_path.path.estimated_hours,
            progress_percentage=student_path.progress_percentage,
            is_active=True
        ) if student_path else None,
        module_progress=module_progress,
        recent_achievements=recent_achievements,
        available_paths=available_paths
    )
    
    return dashboard

@router.put("/profile/{student_id}", response_model=StudentProfile)
@rate_limit_normal(requests=10, window=60)
async def update_student_profile(
    request: Request,
    student_id: str,
    profile_data: UpdateStudentProfile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update student profile"""
    
    # Verify student belongs to current user
    stmt = select(Student).where(
        Student.id == uuid.UUID(student_id),
        Student.user_id == current_user.id,
        Student.is_active == True
    )
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Update fields if provided
    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)
    
    student.updated_at = datetime.utcnow()
    
    try:
        await db.commit()
        
        # Track profile update
        await analytics.track_user_action(
            user_id=current_user.id,
            action_type="profile_update",
            action_name="Student Profile Updated",
            metadata={"student_id": student_id, "fields_updated": list(update_data.keys())}
        )
        
        return StudentProfile(
            id=str(student.id),
            student_name=student.student_name,
            age=student.age,
            grade_level=student.grade_level,
            school_name=student.school_name,
            parent_name=student.parent_name,
            emergency_contact=student.emergency_contact,
            medical_conditions=student.medical_conditions,
            dietary_restrictions=student.dietary_restrictions,
            created_at=student.created_at
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update student profile"
        )

@router.get("/learning-paths", response_model=List[LearningPathSummary])
@rate_limit_relaxed(requests=50, window=60)
async def get_available_learning_paths(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all available learning paths"""
    
    stmt = select(LearningPath).where(LearningPath.is_active == True).order_by(LearningPath.sort_order)
    result = await db.execute(stmt)
    paths = result.scalars().all()
    
    return [
        LearningPathSummary(
            id=str(path.id),
            name=path.name,
            slug=path.slug,
            description=path.description,
            icon=path.icon,
            difficulty_level=path.difficulty_level,
            estimated_hours=path.estimated_hours,
            progress_percentage=0,
            is_active=True
        ) for path in paths
    ]

@router.get("/achievements/{student_id}", response_model=List[Achievement])
@rate_limit_relaxed(requests=30, window=60)
async def get_student_achievements(
    request: Request,
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all achievements for a student"""
    
    # Verify student belongs to current user
    stmt = select(Student).where(
        Student.id == uuid.UUID(student_id),
        Student.user_id == current_user.id,
        Student.is_active == True
    )
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get achievements
    achievements_stmt = select(StudentAchievement).options(
        selectinload(StudentAchievement.achievement_type)
    ).where(
        StudentAchievement.student_id == student.id
    ).order_by(StudentAchievement.earned_at.desc())
    
    achievements_result = await db.execute(achievements_stmt)
    achievements_data = achievements_result.scalars().all()
    
    return [
        Achievement(
            id=str(ach.id),
            name=ach.achievement_type.name,
            description=ach.achievement_type.description,
            icon=ach.achievement_type.icon,
            badge_color=ach.achievement_type.badge_color,
            points=ach.achievement_type.points,
            earned_at=ach.earned_at
        ) for ach in achievements_data
    ]

@router.post("/activity/{student_id}")
@rate_limit_normal(requests=100, window=60)
async def track_student_activity(
    request: Request,
    student_id: str,
    activity_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Track student activity for analytics"""
    
    # Verify student belongs to current user
    stmt = select(Student).where(
        Student.id == uuid.UUID(student_id),
        Student.user_id == current_user.id,
        Student.is_active == True
    )
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Track activity
    await analytics.track_student_activity(
        student_id=uuid.UUID(student_id),
        activity_type=activity_data.get("type", "interaction"),
        activity_data=activity_data,
        user_id=current_user.id
    )
    
    return {"message": "Activity tracked successfully"}