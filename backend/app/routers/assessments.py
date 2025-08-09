"""
Assessment router for CIFIX LEARN
Handle AI pathway finder assessment and results
"""
from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import httpx

from app.database import get_db
from app.models.user import User, Student, StudentAssessment, LearningPath, StudentLearningPath
from app.models.analytics import AssessmentAnalytics, UserAction
from app.routers.auth import get_current_user
from app.middleware import rate_limit_normal, rate_limit_strict
from app.services.analytics_service import AnalyticsService
from app.services.learning_service import LearningService

# Router setup
router = APIRouter()
analytics = AnalyticsService()
learning_service = LearningService()

# Pydantic models
class AssessmentStart(BaseModel):
    """Start assessment request"""
    student_id: str
    assessment_type: str = "pathway_finder"

class AssessmentResponse(BaseModel):
    """Individual assessment question response"""
    question_id: str
    selected_option: str
    response_value: int
    time_spent_seconds: int

class AssessmentComplete(BaseModel):
    """Complete assessment with all responses"""
    student_id: str
    assessment_id: str
    responses: List[AssessmentResponse]
    total_time_minutes: int
    strengths: List[str]
    interests: List[str]
    recommended_path: str
    assessment_score: int
    confidence_level: Optional[int] = None
    feedback: Optional[str] = None

class AssessmentResult(BaseModel):
    """Assessment result response"""
    id: str
    student_id: str
    assessment_type: str
    completed_at: datetime
    assessment_score: int
    recommended_path_id: str
    recommended_path_name: str
    strengths: List[str]
    interests: List[str]
    total_time_minutes: int

class AssessmentProgress(BaseModel):
    """Assessment progress tracking"""
    id: str
    student_id: str
    started_at: datetime
    questions_answered: int
    total_questions: int
    progress_percentage: int
    is_completed: bool

class PathRecommendation(BaseModel):
    """Learning path recommendation"""
    path_id: str
    path_name: str
    match_score: int
    reasons: List[str]
    description: str
    estimated_hours: int

@router.post("/start", response_model=AssessmentProgress)
@rate_limit_strict(requests=5, window=300)  # Max 5 assessments per 5 minutes
async def start_assessment(
    request: Request,
    assessment_data: AssessmentStart,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a new assessment for a student"""
    
    # Verify student belongs to current user
    stmt = select(Student).where(
        Student.id == uuid.UUID(assessment_data.student_id),
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
    
    # Check if student already has a completed assessment
    existing_stmt = select(StudentAssessment).where(
        StudentAssessment.student_id == student.id,
        StudentAssessment.assessment_type == assessment_data.assessment_type,
        StudentAssessment.is_completed == True
    )
    existing_result = await db.execute(existing_stmt)
    existing_assessment = existing_result.scalar_one_or_none()
    
    if existing_assessment:
        # Return existing completed assessment
        return AssessmentProgress(
            id=str(existing_assessment.id),
            student_id=str(student.id),
            started_at=existing_assessment.started_at,
            questions_answered=existing_assessment.questions_answered,
            total_questions=existing_assessment.total_questions or 10,
            progress_percentage=100,
            is_completed=True
        )
    
    # Check for incomplete assessment
    incomplete_stmt = select(StudentAssessment).where(
        StudentAssessment.student_id == student.id,
        StudentAssessment.assessment_type == assessment_data.assessment_type,
        StudentAssessment.is_completed == False
    )
    incomplete_result = await db.execute(incomplete_stmt)
    incomplete_assessment = incomplete_result.scalar_one_or_none()
    
    if incomplete_assessment:
        # Return existing incomplete assessment
        return AssessmentProgress(
            id=str(incomplete_assessment.id),
            student_id=str(student.id),
            started_at=incomplete_assessment.started_at,
            questions_answered=incomplete_assessment.questions_answered,
            total_questions=incomplete_assessment.total_questions or 10,
            progress_percentage=int((incomplete_assessment.questions_answered / 10) * 100),
            is_completed=False
        )
    
    try:
        # Create new assessment
        new_assessment = StudentAssessment(
            student_id=student.id,
            assessment_type=assessment_data.assessment_type,
            total_questions=10,  # Standard pathway finder has 10 questions
            questions_answered=0,
            is_completed=False
        )
        
        db.add(new_assessment)
        await db.flush()
        
        # Create assessment analytics record
        assessment_analytics = AssessmentAnalytics(
            assessment_id=new_assessment.id,
            student_id=student.id,
            started_at=datetime.utcnow(),
            questions_answered=0,
            questions_skipped=0,
            questions_changed=0
        )
        
        db.add(assessment_analytics)
        await db.commit()
        
        # Track assessment start
        await analytics.track_user_action(
            user_id=current_user.id,
            action_type="assessment_start",
            action_name="Assessment Started",
            metadata={
                "student_id": assessment_data.student_id,
                "assessment_type": assessment_data.assessment_type,
                "assessment_id": str(new_assessment.id)
            }
        )
        
        return AssessmentProgress(
            id=str(new_assessment.id),
            student_id=str(student.id),
            started_at=new_assessment.started_at,
            questions_answered=0,
            total_questions=10,
            progress_percentage=0,
            is_completed=False
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start assessment"
        )

@router.post("/complete", response_model=AssessmentResult)
@rate_limit_normal(requests=10, window=300)  # 10 completions per 5 minutes
async def complete_assessment(
    request: Request,
    completion_data: AssessmentComplete,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Complete assessment and generate learning path recommendation"""
    
    # Verify student belongs to current user
    stmt = select(Student).where(
        Student.id == uuid.UUID(completion_data.student_id),
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
    
    # Get the assessment
    assessment_stmt = select(StudentAssessment).where(
        StudentAssessment.id == uuid.UUID(completion_data.assessment_id),
        StudentAssessment.student_id == student.id
    )
    assessment_result = await db.execute(assessment_stmt)
    assessment = assessment_result.scalar_one_or_none()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    if assessment.is_completed:
        # Return existing result
        path_stmt = select(LearningPath).where(LearningPath.id == assessment.recommended_path_id)
        path_result = await db.execute(path_stmt)
        recommended_path = path_result.scalar_one_or_none()
        
        return AssessmentResult(
            id=str(assessment.id),
            student_id=str(student.id),
            assessment_type=assessment.assessment_type,
            completed_at=assessment.completed_at,
            assessment_score=assessment.assessment_score,
            recommended_path_id=str(assessment.recommended_path_id),
            recommended_path_name=recommended_path.name if recommended_path else "Unknown",
            strengths=assessment.strengths or [],
            interests=assessment.interests or [],
            total_time_minutes=completion_data.total_time_minutes
        )
    
    try:
        # Find recommended learning path
        recommended_path = await learning_service.find_learning_path_by_name(
            completion_data.recommended_path, 
            db
        )
        
        if not recommended_path:
            # Default to General Programming if path not found
            default_stmt = select(LearningPath).where(LearningPath.slug == "general-programming")
            default_result = await db.execute(default_stmt)
            recommended_path = default_result.scalar_one_or_none()
        
        # Update assessment with completion data
        assessment.completed_at = datetime.utcnow()
        assessment.questions_answered = len(completion_data.responses)
        assessment.time_spent_minutes = completion_data.total_time_minutes
        assessment.assessment_score = completion_data.assessment_score
        assessment.recommended_path_id = recommended_path.id if recommended_path else None
        assessment.strengths = completion_data.strengths
        assessment.interests = completion_data.interests
        assessment.is_completed = True
        
        # Update assessment analytics
        analytics_stmt = select(AssessmentAnalytics).where(
            AssessmentAnalytics.assessment_id == assessment.id
        )
        analytics_result = await db.execute(analytics_stmt)
        assessment_analytics = analytics_result.scalar_one_or_none()
        
        if assessment_analytics:
            assessment_analytics.completed_at = datetime.utcnow()
            assessment_analytics.total_time_seconds = completion_data.total_time_minutes * 60
            assessment_analytics.questions_answered = len(completion_data.responses)
            assessment_analytics.average_time_per_question = (completion_data.total_time_minutes * 60) / len(completion_data.responses) if completion_data.responses else 0
        
        # Create or update student learning path
        if recommended_path:
            # Check if student already has this path
            existing_path_stmt = select(StudentLearningPath).where(
                StudentLearningPath.student_id == student.id,
                StudentLearningPath.path_id == recommended_path.id
            )
            existing_path_result = await db.execute(existing_path_stmt)
            existing_path = existing_path_result.scalar_one_or_none()
            
            if not existing_path:
                # Create new learning path assignment
                student_path = StudentLearningPath(
                    student_id=student.id,
                    path_id=recommended_path.id,
                    assigned_at=datetime.utcnow(),
                    progress_percentage=0,
                    is_active=True
                )
                db.add(student_path)
            else:
                # Reactivate existing path
                existing_path.is_active = True
                existing_path.assigned_at = datetime.utcnow()
        
        await db.commit()
        
        # Track assessment completion
        await analytics.track_user_action(
            user_id=current_user.id,
            action_type="assessment_complete",
            action_name="Assessment Completed",
            metadata={
                "student_id": completion_data.student_id,
                "assessment_id": completion_data.assessment_id,
                "score": completion_data.assessment_score,
                "recommended_path": completion_data.recommended_path,
                "time_spent": completion_data.total_time_minutes
            }
        )
        
        return AssessmentResult(
            id=str(assessment.id),
            student_id=str(student.id),
            assessment_type=assessment.assessment_type,
            completed_at=assessment.completed_at,
            assessment_score=assessment.assessment_score,
            recommended_path_id=str(recommended_path.id) if recommended_path else "",
            recommended_path_name=recommended_path.name if recommended_path else "General Programming",
            strengths=completion_data.strengths,
            interests=completion_data.interests,
            total_time_minutes=completion_data.total_time_minutes
        )
        
    except Exception as e:
        await db.rollback()
        print(f"Assessment completion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete assessment"
        )

@router.get("/results/{student_id}", response_model=List[AssessmentResult])
@rate_limit_normal(requests=20, window=60)
async def get_assessment_results(
    request: Request,
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all assessment results for a student"""
    
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
    
    # Get completed assessments
    assessments_stmt = select(StudentAssessment).options(
        selectinload(StudentAssessment.recommended_path)
    ).where(
        StudentAssessment.student_id == student.id,
        StudentAssessment.is_completed == True
    ).order_by(StudentAssessment.completed_at.desc())
    
    assessments_result = await db.execute(assessments_stmt)
    assessments = assessments_result.scalars().all()
    
    return [
        AssessmentResult(
            id=str(assessment.id),
            student_id=str(student.id),
            assessment_type=assessment.assessment_type,
            completed_at=assessment.completed_at,
            assessment_score=assessment.assessment_score,
            recommended_path_id=str(assessment.recommended_path_id) if assessment.recommended_path_id else "",
            recommended_path_name=assessment.recommended_path.name if assessment.recommended_path else "Unknown",
            strengths=assessment.strengths or [],
            interests=assessment.interests or [],
            total_time_minutes=assessment.time_spent_minutes
        ) for assessment in assessments
    ]

@router.get("/recommendations/{student_id}", response_model=List[PathRecommendation])
@rate_limit_normal(requests=10, window=60)
async def get_path_recommendations(
    request: Request,
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get learning path recommendations for a student"""
    
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
    
    # Get student's latest assessment
    latest_assessment_stmt = select(StudentAssessment).where(
        StudentAssessment.student_id == student.id,
        StudentAssessment.is_completed == True
    ).order_by(StudentAssessment.completed_at.desc()).limit(1)
    
    latest_result = await db.execute(latest_assessment_stmt)
    latest_assessment = latest_result.scalar_one_or_none()
    
    # Get all available learning paths
    paths_stmt = select(LearningPath).where(LearningPath.is_active == True).order_by(LearningPath.sort_order)
    paths_result = await db.execute(paths_stmt)
    all_paths = paths_result.scalars().all()
    
    recommendations = []
    
    for path in all_paths:
        # Calculate match score based on assessment data
        match_score = 70  # Default score
        reasons = ["Great introduction to programming concepts"]
        
        if latest_assessment:
            # Boost score for recommended path
            if latest_assessment.recommended_path_id == path.id:
                match_score = latest_assessment.assessment_score
                reasons = [f"Based on your assessment results showing strengths in {', '.join(latest_assessment.strengths or ['problem solving'])}"]
            
            # Adjust score based on interests
            if latest_assessment.interests:
                path_keywords = {
                    "game-development": ["games", "interactive", "storytelling"],
                    "ai-machine-learning": ["ai", "data", "patterns", "decisions"],
                    "web-development": ["websites", "web", "online"],
                    "robotics": ["robots", "physical", "automation"],
                    "data-science": ["data", "statistics", "analysis"],
                    "mobile-app-development": ["mobile", "apps", "phones"]
                }
                
                keywords = path_keywords.get(path.slug, [])
                interest_matches = sum(1 for interest in latest_assessment.interests if any(keyword in interest.lower() for keyword in keywords))
                if interest_matches > 0:
                    match_score += interest_matches * 10
                    reasons.append(f"Matches your interest in {', '.join(latest_assessment.interests)}")
        
        # Cap the score at 100
        match_score = min(match_score, 100)
        
        recommendations.append(PathRecommendation(
            path_id=str(path.id),
            path_name=path.name,
            match_score=match_score,
            reasons=reasons,
            description=path.description,
            estimated_hours=path.estimated_hours
        ))
    
    # Sort by match score descending
    recommendations.sort(key=lambda x: x.match_score, reverse=True)
    
    return recommendations

@router.post("/retake/{student_id}")
@rate_limit_strict(requests=2, window=3600)  # Max 2 retakes per hour
async def retake_assessment(
    request: Request,
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Allow student to retake assessment"""
    
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
    
    # Deactivate current assessments
    update_stmt = select(StudentAssessment).where(
        StudentAssessment.student_id == student.id,
        StudentAssessment.is_completed == True
    )
    assessments_result = await db.execute(update_stmt)
    assessments = assessments_result.scalars().all()
    
    # Mark old assessments as inactive (don't delete for analytics)
    for assessment in assessments:
        assessment.is_completed = False  # Allow new assessment
    
    await db.commit()
    
    # Track retake request
    await analytics.track_user_action(
        user_id=current_user.id,
        action_type="assessment_retake",
        action_name="Assessment Retake Requested",
        metadata={"student_id": student_id}
    )
    
    return {"message": "Assessment reset successfully. Student can now retake the assessment."}

@router.get("/analytics/{student_id}")
@rate_limit_normal(requests=10, window=60)
async def get_assessment_analytics(
    request: Request,
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed assessment analytics for a student"""
    
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
    
    # Get assessment analytics
    analytics_stmt = select(AssessmentAnalytics).join(StudentAssessment).where(
        StudentAssessment.student_id == student.id,
        StudentAssessment.is_completed == True
    ).order_by(AssessmentAnalytics.created_at.desc())
    
    analytics_result = await db.execute(analytics_stmt)
    analytics_data = analytics_result.scalars().all()
    
    # Aggregate analytics
    total_assessments = len(analytics_data)
    avg_time = sum(a.total_time_seconds for a in analytics_data if a.total_time_seconds) / total_assessments if total_assessments > 0 else 0
    avg_score = sum(a.assessment.assessment_score for a in analytics_data if hasattr(a, 'assessment') and a.assessment.assessment_score) / total_assessments if total_assessments > 0 else 0
    
    return {
        "student_id": student_id,
        "total_assessments": total_assessments,
        "average_completion_time_minutes": round(avg_time / 60, 2) if avg_time else 0,
        "average_score": round(avg_score, 2),
        "assessment_history": [
            {
                "completed_at": a.completed_at,
                "time_seconds": a.total_time_seconds,
                "questions_answered": a.questions_answered,
                "pause_count": a.pause_count,
                "focus_lost_count": a.window_focus_lost
            } for a in analytics_data
        ]
    }