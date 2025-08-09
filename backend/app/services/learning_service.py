"""
Learning service for CIFIX LEARN
Handle learning paths, modules, and progress tracking
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from app.models.user import (
    LearningPath, LearningModule, StudentLearningPath, 
    StudentModuleProgress, Student, AchievementType, StudentAchievement
)
from app.services.analytics_service import AnalyticsService

class LearningService:
    """Service for managing learning paths and progress"""
    
    def __init__(self):
        self.analytics = AnalyticsService()
    
    async def find_learning_path_by_name(
        self, 
        path_name: str, 
        db: AsyncSession
    ) -> Optional[LearningPath]:
        """Find learning path by name or slug"""
        # Try exact name match first
        stmt = select(LearningPath).where(
            and_(
                LearningPath.name == path_name,
                LearningPath.is_active == True
            )
        )
        result = await db.execute(stmt)
        path = result.scalar_one_or_none()
        
        if path:
            return path
        
        # Try slug match
        slug = path_name.lower().replace(' ', '-').replace('&', '').replace('  ', '-')
        stmt = select(LearningPath).where(
            and_(
                LearningPath.slug == slug,
                LearningPath.is_active == True
            )
        )
        result = await db.execute(stmt)
        path = result.scalar_one_or_none()
        
        if path:
            return path
        
        # Try partial name match for common mappings
        name_mappings = {
            "game": "game-development",
            "gaming": "game-development", 
            "games": "game-development",
            "ai": "ai-machine-learning",
            "artificial intelligence": "ai-machine-learning",
            "machine learning": "ai-machine-learning",
            "web": "web-development",
            "website": "web-development",
            "websites": "web-development",
            "robot": "robotics",
            "robots": "robotics",
            "data": "data-science",
            "analytics": "data-science",
            "mobile": "mobile-app-development",
            "app": "mobile-app-development",
            "apps": "mobile-app-development",
            "programming": "general-programming",
            "coding": "general-programming"
        }
        
        path_key = path_name.lower()
        for key, slug in name_mappings.items():
            if key in path_key:
                stmt = select(LearningPath).where(
                    and_(
                        LearningPath.slug == slug,
                        LearningPath.is_active == True
                    )
                )
                result = await db.execute(stmt)
                return result.scalar_one_or_none()
        
        return None
    
    async def assign_learning_path(
        self,
        student_id: uuid.UUID,
        path_id: uuid.UUID,
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None
    ) -> StudentLearningPath:
        """Assign a learning path to a student"""
        
        # Check if student already has this path
        existing_stmt = select(StudentLearningPath).where(
            and_(
                StudentLearningPath.student_id == student_id,
                StudentLearningPath.path_id == path_id
            )
        )
        result = await db.execute(existing_stmt)
        existing_path = result.scalar_one_or_none()
        
        if existing_path:
            # Reactivate if inactive
            existing_path.is_active = True
            existing_path.assigned_at = datetime.utcnow()
            await db.commit()
            return existing_path
        
        # Create new path assignment
        student_path = StudentLearningPath(
            student_id=student_id,
            path_id=path_id,
            assigned_at=datetime.utcnow(),
            is_active=True
        )
        
        db.add(student_path)
        await db.commit()
        
        # Track path assignment
        if user_id:
            await self.analytics.track_user_action(
                user_id=user_id,
                action_type="learning_path_assigned",
                action_name="Learning Path Assigned",
                metadata={
                    "student_id": str(student_id),
                    "path_id": str(path_id)
                }
            )
        
        return student_path
    
    async def start_module(
        self,
        student_id: uuid.UUID,
        module_id: uuid.UUID,
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[str] = None
    ) -> StudentModuleProgress:
        """Start a learning module for a student"""
        
        # Get module information
        module_stmt = select(LearningModule).options(
            selectinload(LearningModule.path)
        ).where(LearningModule.id == module_id)
        module_result = await db.execute(module_stmt)
        module = module_result.scalar_one_or_none()
        
        if not module:
            raise ValueError("Module not found")
        
        # Check if student has access to this module's path
        path_stmt = select(StudentLearningPath).where(
            and_(
                StudentLearningPath.student_id == student_id,
                StudentLearningPath.path_id == module.path_id,
                StudentLearningPath.is_active == True
            )
        )
        path_result = await db.execute(path_stmt)
        student_path = path_result.scalar_one_or_none()
        
        if not student_path:
            raise ValueError("Student does not have access to this module's learning path")
        
        # Check if module is locked (need to complete previous modules)
        if await self._is_module_locked(student_id, module, db):
            raise ValueError("Module is locked. Complete previous modules first.")
        
        # Check if progress already exists
        progress_stmt = select(StudentModuleProgress).where(
            and_(
                StudentModuleProgress.student_id == student_id,
                StudentModuleProgress.module_id == module_id
            )
        )
        progress_result = await db.execute(progress_stmt)
        existing_progress = progress_result.scalar_one_or_none()
        
        if existing_progress:
            # Update existing progress
            if existing_progress.status == "not_started":
                existing_progress.status = "in_progress"
                existing_progress.started_at = datetime.utcnow()
            existing_progress.last_accessed = datetime.utcnow()
            await db.commit()
            progress = existing_progress
        else:
            # Create new progress record
            progress = StudentModuleProgress(
                student_id=student_id,
                module_id=module_id,
                student_path_id=student_path.id,
                status="in_progress",
                started_at=datetime.utcnow(),
                last_accessed=datetime.utcnow()
            )
            db.add(progress)
            await db.commit()
        
        # Track module start
        await self.analytics.track_student_activity(
            student_id=student_id,
            activity_type="module_start",
            activity_data={
                "module_id": str(module_id),
                "module_title": module.title,
                "path_name": module.path.name,
                "progress_percentage": progress.progress_percentage
            },
            user_id=user_id,
            session_id=session_id
        )
        
        return progress
    
    async def update_module_progress(
        self,
        student_id: uuid.UUID,
        module_id: uuid.UUID,
        progress_percentage: float,
        time_spent_minutes: int = 0,
        notes: str = None,
        db: AsyncSession = None,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[str] = None
    ) -> StudentModuleProgress:
        """Update progress on a learning module"""
        
        # Get existing progress
        stmt = select(StudentModuleProgress).where(
            and_(
                StudentModuleProgress.student_id == student_id,
                StudentModuleProgress.module_id == module_id
            )
        )
        result = await db.execute(stmt)
        progress = result.scalar_one_or_none()
        
        if not progress:
            raise ValueError("Module progress not found. Start the module first.")
        
        # Update progress
        old_percentage = progress.progress_percentage
        progress.progress_percentage = max(progress.progress_percentage, progress_percentage)
        progress.time_spent_minutes += time_spent_minutes
        progress.last_accessed = datetime.utcnow()
        
        if notes:
            progress.notes = notes
        
        # Check if module is completed
        if progress.progress_percentage >= 100 and progress.status != "completed":
            progress.status = "completed"
            progress.completed_at = datetime.utcnow()
            
            # Update overall path progress
            await self._update_path_progress(student_id, progress.student_path_id, db)
            
            # Check for achievements
            await self._check_achievements(student_id, db)
        
        await db.commit()
        
        # Track progress update
        await self.analytics.track_student_activity(
            student_id=student_id,
            activity_type="module_progress",
            activity_data={
                "module_id": str(module_id),
                "old_progress": old_percentage,
                "new_progress": progress.progress_percentage,
                "time_spent": time_spent_minutes,
                "status": progress.status
            },
            user_id=user_id,
            session_id=session_id
        )
        
        return progress
    
    async def complete_module(
        self,
        student_id: uuid.UUID,
        module_id: uuid.UUID,
        final_time_spent: int = 0,
        difficulty_rating: int = None,
        feedback: str = None,
        db: AsyncSession = None,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[str] = None
    ) -> StudentModuleProgress:
        """Mark a module as completed"""
        
        # Update progress to 100% and mark as completed
        progress = await self.update_module_progress(
            student_id=student_id,
            module_id=module_id,
            progress_percentage=100.0,
            time_spent_minutes=final_time_spent,
            db=db,
            user_id=user_id,
            session_id=session_id
        )
        
        # Track completion
        await self.analytics.track_student_activity(
            student_id=student_id,
            activity_type="module_complete",
            activity_data={
                "module_id": str(module_id),
                "total_time_spent": progress.time_spent_minutes,
                "difficulty_rating": difficulty_rating,
                "feedback": feedback
            },
            user_id=user_id,
            session_id=session_id
        )
        
        # Track content engagement
        module_stmt = select(LearningModule).where(LearningModule.id == module_id)
        module_result = await db.execute(module_stmt)
        module = module_result.scalar_one_or_none()
        
        if module:
            await self.analytics.track_content_engagement(
                content_type="module",
                content_id=str(module_id),
                content_title=module.title,
                student_id=student_id,
                session_id=session_id,
                time_spent=final_time_spent * 60,  # Convert to seconds
                completion_percentage=100.0,
                rating=difficulty_rating,
                feedback=feedback
            )
        
        return progress
    
    async def _is_module_locked(
        self, 
        student_id: uuid.UUID, 
        module: LearningModule, 
        db: AsyncSession
    ) -> bool:
        """Check if a module is locked for a student"""
        
        # First module in path is never locked
        if module.sort_order <= 1:
            return False
        
        # Check if previous module is completed
        previous_module_stmt = select(LearningModule).where(
            and_(
                LearningModule.path_id == module.path_id,
                LearningModule.sort_order == module.sort_order - 1,
                LearningModule.is_active == True
            )
        )
        previous_result = await db.execute(previous_module_stmt)
        previous_module = previous_result.scalar_one_or_none()
        
        if not previous_module:
            return False  # No previous module found
        
        # Check if student completed the previous module
        progress_stmt = select(StudentModuleProgress).where(
            and_(
                StudentModuleProgress.student_id == student_id,
                StudentModuleProgress.module_id == previous_module.id,
                StudentModuleProgress.status == "completed"
            )
        )
        progress_result = await db.execute(progress_stmt)
        previous_progress = progress_result.scalar_one_or_none()
        
        return previous_progress is None
    
    async def _update_path_progress(
        self, 
        student_id: uuid.UUID, 
        student_path_id: uuid.UUID, 
        db: AsyncSession
    ):
        """Update overall progress for a learning path"""
        
        # Get total modules in path
        total_modules_stmt = select(func.count(LearningModule.id)).join(
            StudentLearningPath
        ).where(
            and_(
                StudentLearningPath.id == student_path_id,
                LearningModule.is_active == True
            )
        )
        total_result = await db.execute(total_modules_stmt)
        total_modules = total_result.scalar() or 0
        
        # Get completed modules
        completed_modules_stmt = select(func.count(StudentModuleProgress.id)).where(
            and_(
                StudentModuleProgress.student_id == student_id,
                StudentModuleProgress.student_path_id == student_path_id,
                StudentModuleProgress.status == "completed"
            )
        )
        completed_result = await db.execute(completed_modules_stmt)
        completed_modules = completed_result.scalar() or 0
        
        # Calculate progress percentage
        if total_modules > 0:
            progress_percentage = int((completed_modules / total_modules) * 100)
        else:
            progress_percentage = 0
        
        # Update student learning path
        update_stmt = update(StudentLearningPath).where(
            StudentLearningPath.id == student_path_id
        ).values(
            progress_percentage=progress_percentage,
            started_at=func.coalesce(StudentLearningPath.started_at, datetime.utcnow())
        )
        
        await db.execute(update_stmt)
        
        # Mark as completed if 100%
        if progress_percentage >= 100:
            complete_stmt = update(StudentLearningPath).where(
                StudentLearningPath.id == student_path_id
            ).values(completed_at=datetime.utcnow())
            await db.execute(complete_stmt)
    
    async def _check_achievements(self, student_id: uuid.UUID, db: AsyncSession):
        """Check and award achievements for student progress"""
        
        # Get student's progress statistics
        total_completed_stmt = select(func.count(StudentModuleProgress.id)).where(
            and_(
                StudentModuleProgress.student_id == student_id,
                StudentModuleProgress.status == "completed"
            )
        )
        total_result = await db.execute(total_completed_stmt)
        total_completed = total_result.scalar() or 0
        
        # Check for "First Steps" achievement (complete 1 module)
        if total_completed >= 1:
            await self._award_achievement_if_new(
                student_id, 
                "First Steps", 
                db
            )
        
        # Check for "Quick Learner" achievement (complete 3 modules in one day)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_completed_stmt = select(func.count(StudentModuleProgress.id)).where(
            and_(
                StudentModuleProgress.student_id == student_id,
                StudentModuleProgress.status == "completed",
                StudentModuleProgress.completed_at >= today_start
            )
        )
        today_result = await db.execute(today_completed_stmt)
        today_completed = today_result.scalar() or 0
        
        if today_completed >= 3:
            await self._award_achievement_if_new(
                student_id, 
                "Quick Learner", 
                db
            )
        
        # Check for "Path Completer" achievement (complete entire learning path)
        completed_paths_stmt = select(func.count(StudentLearningPath.id)).where(
            and_(
                StudentLearningPath.student_id == student_id,
                StudentLearningPath.completed_at.isnot(None)
            )
        )
        paths_result = await db.execute(completed_paths_stmt)
        completed_paths = paths_result.scalar() or 0
        
        if completed_paths >= 1:
            await self._award_achievement_if_new(
                student_id, 
                "Path Completer", 
                db
            )
    
    async def _award_achievement_if_new(
        self, 
        student_id: uuid.UUID, 
        achievement_name: str, 
        db: AsyncSession
    ):
        """Award achievement if student doesn't already have it"""
        
        # Get achievement type
        achievement_type_stmt = select(AchievementType).where(
            AchievementType.name == achievement_name
        )
        type_result = await db.execute(achievement_type_stmt)
        achievement_type = type_result.scalar_one_or_none()
        
        if not achievement_type:
            return  # Achievement type not found
        
        # Check if student already has this achievement
        existing_stmt = select(StudentAchievement).where(
            and_(
                StudentAchievement.student_id == student_id,
                StudentAchievement.achievement_type_id == achievement_type.id
            )
        )
        existing_result = await db.execute(existing_stmt)
        existing_achievement = existing_result.scalar_one_or_none()
        
        if existing_achievement:
            return  # Already has this achievement
        
        # Award the achievement
        new_achievement = StudentAchievement(
            student_id=student_id,
            achievement_type_id=achievement_type.id,
            earned_at=datetime.utcnow()
        )
        
        db.add(new_achievement)
        
        # Track achievement earned
        await self.analytics.track_student_activity(
            student_id=student_id,
            activity_type="achievement_earned",
            activity_data={
                "achievement_name": achievement_name,
                "achievement_points": achievement_type.points
            }
        )