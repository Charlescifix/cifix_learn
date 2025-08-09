"""
User and Student models for CIFIX LEARN
Simple models for 10-15 users
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class User(Base):
    """Parent/Guardian user account"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Email verification
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Security
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    students = relationship("Student", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"

class Student(Base):
    """Student profile linked to parent account"""
    __tablename__ = "students"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Student Information
    student_name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    grade_level = Column(String(20), nullable=True)
    school_name = Column(String(200), nullable=True)
    parent_name = Column(String(100), nullable=True)
    emergency_contact = Column(String(20), nullable=True)
    
    # Medical/Dietary (for summer classes)
    medical_conditions = Column(Text, nullable=True)
    dietary_restrictions = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="students")
    assessments = relationship("StudentAssessment", back_populates="student")
    learning_paths = relationship("StudentLearningPath", back_populates="student")
    achievements = relationship("StudentAchievement", back_populates="student")
    
    def __repr__(self):
        return f"<Student {self.student_name} (Age: {self.age})>"

class StudentAssessment(Base):
    """Student assessment results"""
    __tablename__ = "student_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    
    # Assessment Details
    assessment_type = Column(String(50), default="pathway_finder")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results
    total_questions = Column(Integer, nullable=True)
    questions_answered = Column(Integer, default=0)
    time_spent_minutes = Column(Integer, default=0)
    assessment_score = Column(Integer, nullable=True)  # 0-100
    
    # Recommendations
    recommended_path_id = Column(UUID(as_uuid=True), ForeignKey("learning_paths.id"), nullable=True)
    strengths = Column(ARRAY(String), nullable=True)
    interests = Column(ARRAY(String), nullable=True)
    
    # Status
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="assessments")
    recommended_path = relationship("LearningPath")
    
    def __repr__(self):
        return f"<Assessment {self.student.student_name}: {self.assessment_score}%>"

class LearningPath(Base):
    """Learning paths (Game Dev, AI, Web Dev, etc.)"""
    __tablename__ = "learning_paths"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(20), nullable=True)
    difficulty_level = Column(String(20), default="Beginner")
    estimated_hours = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    modules = relationship("LearningModule", back_populates="path", cascade="all, delete-orphan")
    student_paths = relationship("StudentLearningPath", back_populates="path")
    
    def __repr__(self):
        return f"<LearningPath {self.name}>"

class LearningModule(Base):
    """Individual learning modules within paths"""
    __tablename__ = "learning_modules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path_id = Column(UUID(as_uuid=True), ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    content = Column(Text, nullable=True)  # Module content
    icon = Column(String(20), nullable=True)
    difficulty_level = Column(String(20), default="Beginner")
    estimated_hours = Column(Integer, default=0)
    sort_order = Column(Integer, nullable=False)
    
    # Learning objectives and topics
    learning_objectives = Column(ARRAY(String), nullable=True)
    topics = Column(ARRAY(String), nullable=True)
    
    # Module settings
    is_locked = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    path = relationship("LearningPath", back_populates="modules")
    progress_records = relationship("StudentModuleProgress", back_populates="module")
    
    def __repr__(self):
        return f"<Module {self.title}>"

class StudentLearningPath(Base):
    """Student enrollment in learning paths"""
    __tablename__ = "student_learning_paths"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    path_id = Column(UUID(as_uuid=True), ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False)
    
    # Progress
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    progress_percentage = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    student = relationship("Student", back_populates="learning_paths")
    path = relationship("LearningPath", back_populates="student_paths")
    module_progress = relationship("StudentModuleProgress", back_populates="student_path")
    
    def __repr__(self):
        return f"<StudentPath {self.student.student_name}: {self.path.name}>"

class StudentModuleProgress(Base):
    """Student progress through individual modules"""
    __tablename__ = "student_module_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(UUID(as_uuid=True), ForeignKey("learning_modules.id", ondelete="CASCADE"), nullable=False)
    student_path_id = Column(UUID(as_uuid=True), ForeignKey("student_learning_paths.id", ondelete="CASCADE"), nullable=False)
    
    # Progress status
    status = Column(String(20), default="not_started")  # not_started, in_progress, completed
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    progress_percentage = Column(Integer, default=0)
    time_spent_minutes = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    student = relationship("Student")
    module = relationship("LearningModule", back_populates="progress_records")
    student_path = relationship("StudentLearningPath", back_populates="module_progress")
    
    def __repr__(self):
        return f"<ModuleProgress {self.module.title}: {self.status}>"

class AchievementType(Base):
    """Achievement types (badges students can earn)"""
    __tablename__ = "achievement_types"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(20), nullable=True)
    badge_color = Column(String(20), nullable=True)
    points = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    student_achievements = relationship("StudentAchievement", back_populates="achievement_type")
    
    def __repr__(self):
        return f"<Achievement {self.name}>"

class StudentAchievement(Base):
    """Achievements earned by students"""
    __tablename__ = "student_achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    achievement_type_id = Column(UUID(as_uuid=True), ForeignKey("achievement_types.id", ondelete="CASCADE"), nullable=False)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="achievements")
    achievement_type = relationship("AchievementType", back_populates="student_achievements")
    
    def __repr__(self):
        return f"<StudentAchievement {self.achievement_type.name}>"