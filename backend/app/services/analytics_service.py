"""
Analytics service for CIFIX LEARN
Comprehensive data collection and tracking
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uuid
import json

from app.database import AsyncSessionLocal
from app.models.user import User, Student
from app.models.analytics import (
    UserSession, PageView, UserAction, AssessmentAnalytics, 
    LearningAnalytics, SystemMetrics, ErrorLog, FeatureUsage, ContentEngagement
)

class AnalyticsService:
    """Service for tracking and analyzing user behavior"""
    
    async def track_user_action(
        self, 
        user_id: uuid.UUID, 
        action_type: str, 
        action_name: str,
        action_category: str = "general",
        page_path: str = None,
        element_id: str = None,
        element_type: str = None,
        metadata: Dict[str, Any] = None,
        session_id: str = None
    ):
        """Track a user action"""
        async with AsyncSessionLocal() as db:
            try:
                action = UserAction(
                    user_id=user_id,
                    session_id=session_id,
                    action_type=action_type,
                    action_category=action_category,
                    action_name=action_name,
                    page_path=page_path,
                    element_id=element_id,
                    element_type=element_type,
                    metadata=metadata
                )
                
                db.add(action)
                await db.commit()
                
            except Exception as e:
                await db.rollback()
                print(f"Failed to track user action: {e}")
    
    async def track_page_view(
        self,
        session_id: str,
        page_path: str,
        page_title: str = None,
        referrer: str = None,
        user_id: uuid.UUID = None,
        time_on_page: int = None,
        scroll_percentage: int = 0,
        interactions: int = 0
    ):
        """Track a page view"""
        async with AsyncSessionLocal() as db:
            try:
                page_view = PageView(
                    session_id=session_id,
                    user_id=user_id,
                    page_path=page_path,
                    page_title=page_title,
                    referrer=referrer,
                    time_on_page=time_on_page,
                    scroll_percentage=scroll_percentage,
                    interactions=interactions
                )
                
                db.add(page_view)
                await db.commit()
                
            except Exception as e:
                await db.rollback()
                print(f"Failed to track page view: {e}")
    
    async def track_student_activity(
        self,
        student_id: uuid.UUID,
        activity_type: str,
        activity_data: Dict[str, Any],
        user_id: uuid.UUID = None,
        session_id: str = None
    ):
        """Track student-specific activity"""
        async with AsyncSessionLocal() as db:
            try:
                # Track as user action
                action = UserAction(
                    user_id=user_id,
                    session_id=session_id,
                    action_type=f"student_{activity_type}",
                    action_category="learning",
                    action_name=f"Student {activity_type.replace('_', ' ').title()}",
                    metadata={
                        "student_id": str(student_id),
                        **activity_data
                    }
                )
                
                db.add(action)
                
                # If it's learning-related, also track in learning analytics
                if activity_type in ["module_start", "module_progress", "module_complete"]:
                    await self._track_learning_analytics(
                        student_id, 
                        activity_data, 
                        session_id,
                        db
                    )
                
                await db.commit()
                
            except Exception as e:
                await db.rollback()
                print(f"Failed to track student activity: {e}")
    
    async def _track_learning_analytics(
        self,
        student_id: uuid.UUID,
        activity_data: Dict[str, Any],
        session_id: str,
        db: AsyncSession
    ):
        """Track detailed learning analytics"""
        try:
            module_id = activity_data.get("module_id")
            if not module_id:
                return
            
            # Check if we have an existing learning analytics record for this session
            stmt = select(LearningAnalytics).where(
                and_(
                    LearningAnalytics.student_id == student_id,
                    LearningAnalytics.module_id == uuid.UUID(module_id),
                    LearningAnalytics.session_id == session_id,
                    LearningAnalytics.session_end.is_(None)
                )
            )
            result = await db.execute(stmt)
            learning_session = result.scalar_one_or_none()
            
            if not learning_session:
                # Create new learning session
                learning_session = LearningAnalytics(
                    student_id=student_id,
                    module_id=uuid.UUID(module_id),
                    session_id=session_id,
                    content_interactions=1,
                    progress_percentage=activity_data.get("progress_percentage", 0.0),
                    learning_path=activity_data.get("learning_path", {})
                )
                db.add(learning_session)
            else:
                # Update existing session
                learning_session.content_interactions += 1
                learning_session.progress_percentage = max(
                    learning_session.progress_percentage,
                    activity_data.get("progress_percentage", 0.0)
                )
                
                # Update session duration
                if learning_session.session_start:
                    duration = datetime.utcnow() - learning_session.session_start
                    learning_session.session_duration = int(duration.total_seconds())
        
        except Exception as e:
            print(f"Failed to track learning analytics: {e}")
    
    async def track_feature_usage(
        self,
        feature_name: str,
        feature_category: str,
        user_id: uuid.UUID = None,
        student_id: uuid.UUID = None,
        session_id: str = None,
        time_spent: int = None,
        success_rate: float = None,
        configuration: Dict[str, Any] = None,
        results: Dict[str, Any] = None
    ):
        """Track usage of specific features"""
        async with AsyncSessionLocal() as db:
            try:
                # Check if feature usage already exists for this user/session
                stmt = select(FeatureUsage).where(
                    and_(
                        FeatureUsage.feature_name == feature_name,
                        FeatureUsage.user_id == user_id,
                        FeatureUsage.session_id == session_id
                    )
                )
                result = await db.execute(stmt)
                existing_usage = result.scalar_one_or_none()
                
                if existing_usage:
                    # Update existing record
                    existing_usage.usage_count += 1
                    existing_usage.last_used = datetime.utcnow()
                    if time_spent:
                        existing_usage.time_spent = (existing_usage.time_spent or 0) + time_spent
                    if success_rate is not None:
                        # Calculate average success rate
                        old_rate = existing_usage.success_rate or 0
                        existing_usage.success_rate = (old_rate + success_rate) / 2
                else:
                    # Create new record
                    feature_usage = FeatureUsage(
                        feature_name=feature_name,
                        feature_category=feature_category,
                        user_id=user_id,
                        student_id=student_id,
                        session_id=session_id,
                        time_spent=time_spent,
                        success_rate=success_rate,
                        configuration=configuration,
                        results=results
                    )
                    db.add(feature_usage)
                
                await db.commit()
                
            except Exception as e:
                await db.rollback()
                print(f"Failed to track feature usage: {e}")
    
    async def track_content_engagement(
        self,
        content_type: str,
        content_id: str,
        content_title: str,
        student_id: uuid.UUID,
        session_id: str = None,
        time_spent: int = None,
        completion_percentage: float = 0.0,
        interactions: int = 0,
        rating: int = None,
        feedback: str = None,
        difficulty_reported: int = None
    ):
        """Track engagement with learning content"""
        async with AsyncSessionLocal() as db:
            try:
                # Check if content engagement already exists
                stmt = select(ContentEngagement).where(
                    and_(
                        ContentEngagement.content_type == content_type,
                        ContentEngagement.content_id == content_id,
                        ContentEngagement.student_id == student_id
                    )
                )
                result = await db.execute(stmt)
                existing_engagement = result.scalar_one_or_none()
                
                if existing_engagement:
                    # Update existing record
                    existing_engagement.view_count += 1
                    existing_engagement.last_accessed = datetime.utcnow()
                    if time_spent:
                        existing_engagement.total_time_spent += time_spent
                    existing_engagement.completion_percentage = max(
                        existing_engagement.completion_percentage,
                        completion_percentage
                    )
                    existing_engagement.interactions += interactions
                    if rating:
                        existing_engagement.rating = rating
                    if feedback:
                        existing_engagement.feedback = feedback
                    if difficulty_reported:
                        existing_engagement.difficulty_reported = difficulty_reported
                else:
                    # Create new record
                    content_engagement = ContentEngagement(
                        content_type=content_type,
                        content_id=content_id,
                        content_title=content_title,
                        student_id=student_id,
                        session_id=session_id,
                        total_time_spent=time_spent or 0,
                        completion_percentage=completion_percentage,
                        interactions=interactions,
                        rating=rating,
                        feedback=feedback,
                        difficulty_reported=difficulty_reported
                    )
                    db.add(content_engagement)
                
                await db.commit()
                
            except Exception as e:
                await db.rollback()
                print(f"Failed to track content engagement: {e}")
    
    async def log_error(
        self,
        error_type: str,
        error_message: str,
        error_category: str = "system",
        severity: str = "medium",
        error_code: str = None,
        stack_trace: str = None,
        user_id: uuid.UUID = None,
        session_id: str = None,
        endpoint: str = None,
        request_method: str = None,
        request_data: Dict[str, Any] = None,
        user_agent: str = None,
        ip_address: str = None
    ):
        """Log system errors for monitoring"""
        async with AsyncSessionLocal() as db:
            try:
                error_log = ErrorLog(
                    error_type=error_type,
                    error_category=error_category,
                    severity=severity,
                    error_message=error_message[:1000],  # Truncate long messages
                    error_code=error_code,
                    stack_trace=stack_trace,
                    user_id=user_id,
                    session_id=session_id,
                    endpoint=endpoint,
                    request_method=request_method,
                    request_data=request_data,
                    user_agent=user_agent,
                    ip_address=ip_address
                )
                
                db.add(error_log)
                await db.commit()
                
            except Exception as e:
                print(f"Failed to log error: {e}")
    
    async def record_system_metric(
        self,
        metric_name: str,
        metric_category: str,
        metric_value: float,
        metric_unit: str = None,
        endpoint: str = None,
        method: str = None,
        status_code: int = None,
        metadata: Dict[str, Any] = None
    ):
        """Record system performance metrics"""
        async with AsyncSessionLocal() as db:
            try:
                metric = SystemMetrics(
                    metric_name=metric_name,
                    metric_category=metric_category,
                    metric_value=metric_value,
                    metric_unit=metric_unit,
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    metadata=metadata
                )
                
                db.add(metric)
                await db.commit()
                
            except Exception as e:
                await db.rollback()
                print(f"Failed to record system metric: {e}")
    
    async def get_user_analytics_summary(
        self, 
        user_id: uuid.UUID, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics summary for a user"""
        async with AsyncSessionLocal() as db:
            try:
                since_date = datetime.utcnow() - timedelta(days=days)
                
                # Get total actions
                actions_stmt = select(func.count(UserAction.id)).where(
                    and_(
                        UserAction.user_id == user_id,
                        UserAction.performed_at >= since_date
                    )
                )
                actions_result = await db.execute(actions_stmt)
                total_actions = actions_result.scalar() or 0
                
                # Get most used features
                features_stmt = select(
                    UserAction.action_type,
                    func.count(UserAction.id).label('count')
                ).where(
                    and_(
                        UserAction.user_id == user_id,
                        UserAction.performed_at >= since_date
                    )
                ).group_by(UserAction.action_type).order_by(func.count(UserAction.id).desc()).limit(5)
                
                features_result = await db.execute(features_stmt)
                top_features = [
                    {"feature": row.action_type, "usage_count": row.count}
                    for row in features_result
                ]
                
                return {
                    "user_id": str(user_id),
                    "period_days": days,
                    "total_actions": total_actions,
                    "top_features": top_features,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                print(f"Failed to get user analytics summary: {e}")
                return {}
    
    async def get_student_learning_analytics(
        self, 
        student_id: uuid.UUID, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get learning analytics for a student"""
        async with AsyncSessionLocal() as db:
            try:
                since_date = datetime.utcnow() - timedelta(days=days)
                
                # Get total learning time
                time_stmt = select(func.coalesce(func.sum(LearningAnalytics.session_duration), 0)).where(
                    and_(
                        LearningAnalytics.student_id == student_id,
                        LearningAnalytics.session_start >= since_date
                    )
                )
                time_result = await db.execute(time_stmt)
                total_time_seconds = time_result.scalar() or 0
                
                # Get engagement metrics
                engagement_stmt = select(
                    func.avg(LearningAnalytics.content_interactions),
                    func.avg(LearningAnalytics.progress_percentage),
                    func.count(LearningAnalytics.id)
                ).where(
                    and_(
                        LearningAnalytics.student_id == student_id,
                        LearningAnalytics.session_start >= since_date
                    )
                )
                engagement_result = await db.execute(engagement_stmt)
                avg_interactions, avg_progress, session_count = engagement_result.first()
                
                return {
                    "student_id": str(student_id),
                    "period_days": days,
                    "total_learning_time_hours": round((total_time_seconds or 0) / 3600, 2),
                    "average_interactions_per_session": round(avg_interactions or 0, 2),
                    "average_progress_percentage": round(avg_progress or 0, 2),
                    "total_learning_sessions": session_count or 0,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                print(f"Failed to get student learning analytics: {e}")
                return {}
    
    async def get_system_health_metrics(self) -> Dict[str, Any]:
        """Get system health and performance metrics"""
        async with AsyncSessionLocal() as db:
            try:
                # Get recent error count
                recent_errors_stmt = select(func.count(ErrorLog.id)).where(
                    ErrorLog.occurred_at >= datetime.utcnow() - timedelta(hours=24)
                )
                recent_errors_result = await db.execute(recent_errors_stmt)
                recent_errors = recent_errors_result.scalar() or 0
                
                # Get critical errors
                critical_errors_stmt = select(func.count(ErrorLog.id)).where(
                    and_(
                        ErrorLog.severity == "critical",
                        ErrorLog.occurred_at >= datetime.utcnow() - timedelta(hours=24),
                        ErrorLog.resolved == False
                    )
                )
                critical_errors_result = await db.execute(critical_errors_stmt)
                critical_errors = critical_errors_result.scalar() or 0
                
                # Get average response time (if recorded)
                response_time_stmt = select(func.avg(SystemMetrics.metric_value)).where(
                    and_(
                        SystemMetrics.metric_name == "response_time",
                        SystemMetrics.recorded_at >= datetime.utcnow() - timedelta(hours=1)
                    )
                )
                response_time_result = await db.execute(response_time_stmt)
                avg_response_time = response_time_result.scalar()
                
                # Get active users in last hour
                active_users_stmt = select(func.count(func.distinct(UserAction.user_id))).where(
                    UserAction.performed_at >= datetime.utcnow() - timedelta(hours=1)
                )
                active_users_result = await db.execute(active_users_stmt)
                active_users = active_users_result.scalar() or 0
                
                return {
                    "errors_last_24h": recent_errors,
                    "critical_errors_unresolved": critical_errors,
                    "average_response_time_ms": round(avg_response_time or 0, 2),
                    "active_users_last_hour": active_users,
                    "system_status": "healthy" if critical_errors == 0 else "degraded",
                    "generated_at": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                print(f"Failed to get system health metrics: {e}")
                return {}