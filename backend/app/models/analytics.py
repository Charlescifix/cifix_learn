"""
Analytics and data collection models for CIFIX LEARN
Comprehensive tracking for insights even with small user base
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class UserSession(Base):
    """Track user sessions for analytics"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Session details
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    browser = Column(String(50), nullable=True)
    os = Column(String(50), nullable=True)
    
    # Geographic data (if available)
    country = Column(String(50), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Session tracking
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, default=0)
    
    # Activity metrics
    page_views = Column(Integer, default=0)
    actions_performed = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<UserSession {self.session_id}>"

class PageView(Base):
    """Track individual page views"""
    __tablename__ = "page_views"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), ForeignKey("user_sessions.session_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Page details
    page_path = Column(String(500), nullable=False)
    page_title = Column(String(200), nullable=True)
    referrer = Column(String(500), nullable=True)
    
    # Timing
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
    time_on_page = Column(Integer, nullable=True)  # seconds
    
    # Engagement metrics
    scroll_percentage = Column(Integer, default=0)
    interactions = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<PageView {self.page_path}>"

class UserAction(Base):
    """Track specific user actions"""
    __tablename__ = "user_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Action details
    action_type = Column(String(100), nullable=False, index=True)
    action_category = Column(String(50), nullable=True)  # authentication, learning, assessment, etc.
    action_name = Column(String(200), nullable=False)
    action_description = Column(Text, nullable=True)
    
    # Context
    page_path = Column(String(500), nullable=True)
    element_id = Column(String(100), nullable=True)
    element_type = Column(String(50), nullable=True)
    
    # Additional data
    metadata = Column(JSONB, nullable=True)
    
    # Timing
    performed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<UserAction {self.action_type}: {self.action_name}>"

class AssessmentAnalytics(Base):
    """Detailed assessment analytics"""
    __tablename__ = "assessment_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("student_assessments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    
    # Timing analytics
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_time_seconds = Column(Integer, nullable=True)
    average_time_per_question = Column(Float, nullable=True)
    
    # Question analytics
    questions_answered = Column(Integer, default=0)
    questions_skipped = Column(Integer, default=0)
    questions_changed = Column(Integer, default=0)  # how many answers were changed
    
    # Engagement metrics
    pause_count = Column(Integer, default=0)  # how many times student paused
    total_pause_time = Column(Integer, default=0)  # total pause time in seconds
    window_focus_lost = Column(Integer, default=0)  # times window lost focus
    
    # Results analytics
    confidence_scores = Column(JSONB, nullable=True)  # per question confidence if available
    response_patterns = Column(JSONB, nullable=True)  # analysis of response patterns
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AssessmentAnalytics {self.assessment_id}>"

class LearningAnalytics(Base):
    """Learning behavior analytics"""
    __tablename__ = "learning_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(UUID(as_uuid=True), ForeignKey("learning_modules.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(255), nullable=True)
    
    # Learning session details
    session_start = Column(DateTime(timezone=True), server_default=func.now())
    session_end = Column(DateTime(timezone=True), nullable=True)
    session_duration = Column(Integer, nullable=True)  # seconds
    
    # Engagement metrics
    content_interactions = Column(Integer, default=0)
    scroll_events = Column(Integer, default=0)
    pause_events = Column(Integer, default=0)
    resume_events = Column(Integer, default=0)
    
    # Progress tracking
    content_percentage_viewed = Column(Float, default=0.0)
    exercises_attempted = Column(Integer, default=0)
    exercises_completed = Column(Integer, default=0)
    
    # Performance indicators
    difficulty_rating = Column(Integer, nullable=True)  # 1-5 if student provides
    help_requests = Column(Integer, default=0)
    errors_made = Column(Integer, default=0)
    
    # Additional data
    learning_path = Column(JSONB, nullable=True)  # track learning progression
    notes_taken = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<LearningAnalytics {self.student_id}: {self.module_id}>"

class SystemMetrics(Base):
    """System performance and usage metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric details
    metric_name = Column(String(100), nullable=False)
    metric_category = Column(String(50), nullable=False)  # performance, usage, error, etc.
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)  # seconds, count, percentage, etc.
    
    # Context
    endpoint = Column(String(200), nullable=True)
    method = Column(String(10), nullable=True)
    status_code = Column(Integer, nullable=True)
    
    # Additional data
    metadata = Column(JSONB, nullable=True)
    
    # Timing
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SystemMetric {self.metric_name}: {self.metric_value}>"

class ErrorLog(Base):
    """Comprehensive error logging"""
    __tablename__ = "error_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Error classification
    error_type = Column(String(100), nullable=False)
    error_category = Column(String(50), nullable=False)  # system, user, integration, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Error details
    error_message = Column(Text, nullable=False)
    error_code = Column(String(50), nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # Context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(255), nullable=True)
    endpoint = Column(String(200), nullable=True)
    request_method = Column(String(10), nullable=True)
    request_data = Column(JSONB, nullable=True)
    
    # Environment
    user_agent = Column(Text, nullable=True)
    ip_address = Column(INET, nullable=True)
    
    # Resolution
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Timing
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ErrorLog {self.error_type}: {self.severity}>"

class FeatureUsage(Base):
    """Track usage of different features"""
    __tablename__ = "feature_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Feature details
    feature_name = Column(String(100), nullable=False, index=True)
    feature_category = Column(String(50), nullable=False)
    
    # Usage details
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Metrics
    usage_count = Column(Integer, default=1)
    time_spent = Column(Integer, nullable=True)  # seconds
    success_rate = Column(Float, nullable=True)
    
    # Additional data
    configuration = Column(JSONB, nullable=True)
    results = Column(JSONB, nullable=True)
    
    # Timing
    first_used = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<FeatureUsage {self.feature_name}: {self.usage_count} uses>"

class ContentEngagement(Base):
    """Track engagement with learning content"""
    __tablename__ = "content_engagement"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Content identification
    content_type = Column(String(50), nullable=False)  # module, video, exercise, etc.
    content_id = Column(String(255), nullable=False)
    content_title = Column(String(200), nullable=True)
    
    # User context
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(255), nullable=True)
    
    # Engagement metrics
    view_count = Column(Integer, default=1)
    total_time_spent = Column(Integer, default=0)  # seconds
    completion_percentage = Column(Float, default=0.0)
    
    # Interaction metrics
    interactions = Column(Integer, default=0)
    replays = Column(Integer, default=0)
    bookmarks = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    
    # Quality indicators
    rating = Column(Integer, nullable=True)  # 1-5 if provided
    feedback = Column(Text, nullable=True)
    difficulty_reported = Column(Integer, nullable=True)  # 1-5
    
    # Timing
    first_accessed = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ContentEngagement {self.content_type}: {self.content_title}>"