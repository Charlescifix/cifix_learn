"""
Admin router for CIFIX LEARN
Admin-only endpoints for monitoring and management
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, update, text
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.database import get_db
from app.models.user import User, Student, StudentModuleProgress, StudentLearningPath
from app.models.analytics import UserSession, PageView, UserAction, ErrorLog, SystemMetrics
from app.routers.auth import get_current_user
from app.services.analytics_service import AnalyticsService
from app.core.config import settings

# Router setup
router = APIRouter()
analytics = AnalyticsService()

# Admin verification dependency
async def verify_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verify current user has admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

# Pydantic models
class UserSummary(BaseModel):
    """User summary for admin dashboard"""
    id: str
    email: str
    full_name: str
    is_verified: bool
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    total_students: int
    total_actions: int

class StudentSummary(BaseModel):
    """Student summary for admin dashboard"""
    id: str
    student_name: str
    age: int
    user_email: str
    created_at: datetime
    assessment_completed: bool
    current_learning_path: Optional[str]
    modules_completed: int
    total_learning_time: int
    last_activity: Optional[datetime]

class SystemStats(BaseModel):
    """System statistics"""
    total_users: int
    active_users_24h: int
    total_students: int
    total_assessments: int
    completed_modules: int
    total_learning_hours: float
    system_health: str
    errors_24h: int
    critical_errors: int

class ErrorSummary(BaseModel):
    """Error log summary"""
    id: str
    error_type: str
    error_category: str
    severity: str
    error_message: str
    occurred_at: datetime
    user_id: Optional[str]
    endpoint: Optional[str]
    resolved: bool

@router.get("/dashboard", response_model=SystemStats)
async def get_admin_dashboard(
    admin_user: User = Depends(verify_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get admin dashboard overview"""
    
    # Get system statistics
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    
    # Total users
    users_stmt = select(func.count(User.id)).where(User.is_active == True)
    users_result = await db.execute(users_stmt)
    total_users = users_result.scalar() or 0
    
    # Active users in last 24h
    active_users_stmt = select(func.count(func.distinct(UserAction.user_id))).where(
        UserAction.performed_at >= yesterday
    )
    active_result = await db.execute(active_users_stmt)
    active_users = active_result.scalar() or 0
    
    # Total students
    students_stmt = select(func.count(Student.id)).where(Student.is_active == True)
    students_result = await db.execute(students_stmt)
    total_students = students_result.scalar() or 0
    
    # Completed modules
    completed_modules_stmt = select(func.count(StudentModuleProgress.id)).where(
        StudentModuleProgress.status == "completed"
    )
    completed_result = await db.execute(completed_modules_stmt)
    completed_modules = completed_result.scalar() or 0
    
    # Total learning time
    learning_time_stmt = select(func.coalesce(func.sum(StudentModuleProgress.time_spent_minutes), 0))
    time_result = await db.execute(learning_time_stmt)
    total_minutes = time_result.scalar() or 0
    total_hours = round(total_minutes / 60, 1)
    
    # System health metrics
    health_metrics = await analytics.get_system_health_metrics()
    
    return SystemStats(
        total_users=total_users,
        active_users_24h=active_users,
        total_students=total_students,
        total_assessments=total_students,  # Assuming one assessment per student
        completed_modules=completed_modules,
        total_learning_hours=total_hours,
        system_health=health_metrics.get("system_status", "unknown"),
        errors_24h=health_metrics.get("errors_last_24h", 0),
        critical_errors=health_metrics.get("critical_errors_unresolved", 0)
    )

@router.get("/users", response_model=List[UserSummary])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    admin_user: User = Depends(verify_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all users with admin details"""
    
    # Build base query
    query = select(User).where(User.is_active == True)
    
    # Add search filter
    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            User.email.ilike(search_term) | 
            User.full_name.ilike(search_term)
        )
    
    # Order and paginate
    query = query.order_by(desc(User.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Get additional stats for each user
    user_summaries = []
    for user in users:
        # Count students
        students_stmt = select(func.count(Student.id)).where(
            and_(Student.user_id == user.id, Student.is_active == True)
        )
        students_result = await db.execute(students_stmt)
        student_count = students_result.scalar() or 0
        
        # Count actions
        actions_stmt = select(func.count(UserAction.id)).where(
            UserAction.user_id == user.id
        )
        actions_result = await db.execute(actions_stmt)
        action_count = actions_result.scalar() or 0
        
        user_summaries.append(UserSummary(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_verified=user.is_verified,
            is_admin=user.is_admin,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
            total_students=student_count,
            total_actions=action_count
        ))
    
    return user_summaries

@router.get("/students", response_model=List[StudentSummary])
async def get_all_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    admin_user: User = Depends(verify_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all students with learning progress"""
    
    # Build base query with user join
    query = select(Student).options(
        selectinload(Student.user)
    ).where(Student.is_active == True)
    
    # Add search filter
    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(Student.student_name.ilike(search_term))
    
    # Order and paginate
    query = query.order_by(desc(Student.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    students = result.scalars().all()
    
    # Get additional data for each student
    student_summaries = []
    for student in students:
        # Check assessment completion
        assessment_completed = student.assessment_results is not None
        
        # Get current learning path
        current_path_stmt = select(StudentLearningPath).options(
            selectinload(StudentLearningPath.path)
        ).where(
            and_(
                StudentLearningPath.student_id == student.id,
                StudentLearningPath.is_active == True
            )
        ).order_by(desc(StudentLearningPath.assigned_at))
        
        path_result = await db.execute(current_path_stmt)
        current_path = path_result.first()
        current_path_name = current_path.path.name if current_path else None
        
        # Count completed modules
        completed_stmt = select(func.count(StudentModuleProgress.id)).where(
            and_(
                StudentModuleProgress.student_id == student.id,
                StudentModuleProgress.status == "completed"
            )
        )
        completed_result = await db.execute(completed_stmt)
        modules_completed = completed_result.scalar() or 0
        
        # Total learning time
        time_stmt = select(func.coalesce(func.sum(StudentModuleProgress.time_spent_minutes), 0)).where(
            StudentModuleProgress.student_id == student.id
        )
        time_result = await db.execute(time_stmt)
        total_time = time_result.scalar() or 0
        
        # Last activity
        last_activity_stmt = select(func.max(StudentModuleProgress.last_accessed)).where(
            StudentModuleProgress.student_id == student.id
        )
        activity_result = await db.execute(last_activity_stmt)
        last_activity = activity_result.scalar()
        
        student_summaries.append(StudentSummary(
            id=str(student.id),
            student_name=student.student_name,
            age=student.age,
            user_email=student.user.email,
            created_at=student.created_at,
            assessment_completed=assessment_completed,
            current_learning_path=current_path_name,
            modules_completed=modules_completed,
            total_learning_time=total_time,
            last_activity=last_activity
        ))
    
    return student_summaries

@router.get("/errors", response_model=List[ErrorSummary])
async def get_system_errors(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    severity: Optional[str] = Query(None),
    resolved: Optional[bool] = Query(None),
    hours: int = Query(24, ge=1, le=168),
    admin_user: User = Depends(verify_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system error logs"""
    
    # Build query
    since_time = datetime.utcnow() - timedelta(hours=hours)
    query = select(ErrorLog).where(ErrorLog.occurred_at >= since_time)
    
    # Add filters
    if severity:
        query = query.where(ErrorLog.severity == severity)
    if resolved is not None:
        query = query.where(ErrorLog.resolved == resolved)
    
    # Order and paginate
    query = query.order_by(desc(ErrorLog.occurred_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    errors = result.scalars().all()
    
    return [
        ErrorSummary(
            id=str(error.id),
            error_type=error.error_type,
            error_category=error.error_category,
            severity=error.severity,
            error_message=error.error_message,
            occurred_at=error.occurred_at,
            user_id=str(error.user_id) if error.user_id else None,
            endpoint=error.endpoint,
            resolved=error.resolved
        )
        for error in errors
    ]

@router.patch("/errors/{error_id}/resolve")
async def resolve_error(
    error_id: str,
    admin_user: User = Depends(verify_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark an error as resolved"""
    
    # Update error status
    stmt = update(ErrorLog).where(ErrorLog.id == uuid.UUID(error_id)).values(
        resolved=True,
        resolved_at=datetime.utcnow(),
        resolved_by=admin_user.id
    )
    
    result = await db.execute(stmt)
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error not found"
        )
    
    await db.commit()
    
    return {"message": "Error marked as resolved"}

@router.get("/analytics/summary")
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365),
    admin_user: User = Depends(verify_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive analytics summary"""
    
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # User activity trends
    user_activity_stmt = select(
        func.date(UserAction.performed_at).label('date'),
        func.count(UserAction.id).label('actions'),
        func.count(func.distinct(UserAction.user_id)).label('active_users')
    ).where(
        UserAction.performed_at >= since_date
    ).group_by(func.date(UserAction.performed_at)).order_by('date')
    
    activity_result = await db.execute(user_activity_stmt)
    activity_trends = [
        {
            "date": row.date.isoformat(),
            "actions": row.actions,
            "active_users": row.active_users
        }
        for row in activity_result
    ]
    
    # Most popular features
    features_stmt = select(
        UserAction.action_type,
        func.count(UserAction.id).label('usage_count')
    ).where(
        UserAction.performed_at >= since_date
    ).group_by(UserAction.action_type).order_by(desc('usage_count')).limit(10)
    
    features_result = await db.execute(features_stmt)
    popular_features = [
        {"feature": row.action_type, "usage_count": row.usage_count}
        for row in features_result
    ]
    
    # Learning progress overview
    progress_stmt = select(
        func.count(StudentModuleProgress.id).label('total_progress'),
        func.count(func.distinct(StudentModuleProgress.student_id)).label('active_students'),
        func.avg(StudentModuleProgress.progress_percentage).label('avg_progress'),
        func.sum(StudentModuleProgress.time_spent_minutes).label('total_time')
    ).where(
        StudentModuleProgress.last_accessed >= since_date
    )
    
    progress_result = await db.execute(progress_stmt)
    progress_data = progress_result.first()
    
    learning_overview = {
        "total_progress_records": progress_data.total_progress or 0,
        "active_students": progress_data.active_students or 0,
        "average_progress_percentage": round(progress_data.avg_progress or 0, 2),
        "total_learning_hours": round((progress_data.total_time or 0) / 60, 2)
    }
    
    return {
        "period_days": days,
        "activity_trends": activity_trends,
        "popular_features": popular_features,
        "learning_overview": learning_overview,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/system/health")
async def get_system_health(
    admin_user: User = Depends(verify_admin_user)
):
    """Get detailed system health metrics"""
    
    health_metrics = await analytics.get_system_health_metrics()
    
    # Add additional system information
    health_metrics.update({
        "server_version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database_url_host": settings.DATABASE_URL.split('@')[1].split('/')[0] if '@' in settings.DATABASE_URL else "unknown",
        "uptime_check": "healthy"  # Could add actual uptime tracking
    })
    
    return health_metrics

@router.post("/users/{user_id}/toggle-admin")
async def toggle_user_admin_status(
    user_id: str,
    admin_user: User = Depends(verify_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle admin status for a user"""
    
    # Get user
    user_stmt = select(User).where(User.id == uuid.UUID(user_id))
    user_result = await db.execute(user_stmt)
    target_user = user_result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow admin to remove their own admin status
    if target_user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own admin status"
        )
    
    # Toggle admin status
    target_user.is_admin = not target_user.is_admin
    await db.commit()
    
    # Track admin action
    await analytics.track_user_action(
        user_id=admin_user.id,
        action_type="admin_user_toggle",
        action_name="Admin Status Toggled",
        metadata={
            "target_user_id": str(target_user.id),
            "new_admin_status": target_user.is_admin
        }
    )
    
    return {
        "message": f"User admin status {'granted' if target_user.is_admin else 'revoked'}",
        "user_email": target_user.email,
        "is_admin": target_user.is_admin
    }

@router.delete("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin_user: User = Depends(verify_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a user account"""
    
    # Get user
    user_stmt = select(User).where(User.id == uuid.UUID(user_id))
    user_result = await db.execute(user_stmt)
    target_user = user_result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow admin to deactivate themselves
    if target_user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Deactivate user and all their students
    target_user.is_active = False
    
    students_stmt = update(Student).where(Student.user_id == target_user.id).values(is_active=False)
    await db.execute(students_stmt)
    
    await db.commit()
    
    # Track admin action
    await analytics.track_user_action(
        user_id=admin_user.id,
        action_type="admin_user_deactivate",
        action_name="User Account Deactivated",
        metadata={
            "target_user_id": str(target_user.id),
            "target_user_email": target_user.email
        }
    )
    
    return {
        "message": f"User account deactivated",
        "user_email": target_user.email
    }