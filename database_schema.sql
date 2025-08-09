-- CIFIX LEARN Database Schema
-- Complete database structure for the learning management system
-- Designed for PostgreSQL on Railway

-- =============================================
-- CORE TABLES
-- =============================================

-- Users table - stores parent/guardian information
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Students table - stores student information
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_name VARCHAR(100) NOT NULL,
    age INTEGER CHECK (age >= 5 AND age <= 18),
    grade_level VARCHAR(20),
    school_name VARCHAR(200),
    parent_name VARCHAR(100),
    emergency_contact VARCHAR(20),
    medical_conditions TEXT,
    dietary_restrictions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- =============================================
-- LEARNING PATHS & MODULES
-- =============================================

-- Learning paths - predefined learning tracks
CREATE TABLE learning_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    icon VARCHAR(20),
    difficulty_level VARCHAR(20) DEFAULT 'Beginner',
    estimated_hours INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sort_order INTEGER DEFAULT 0
);

-- Learning modules - individual lessons within paths
CREATE TABLE learning_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    path_id UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    content TEXT, -- Module content/curriculum
    icon VARCHAR(20),
    difficulty_level VARCHAR(20) DEFAULT 'Beginner',
    estimated_hours DECIMAL(4,2) DEFAULT 0,
    sort_order INTEGER NOT NULL,
    prerequisites TEXT[], -- Array of prerequisite module IDs
    learning_objectives TEXT[],
    topics TEXT[],
    is_locked BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- ASSESSMENT SYSTEM
-- =============================================

-- Assessment questions - stores all assessment questions
CREATE TABLE assessment_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) DEFAULT 'multiple_choice', -- multiple_choice, true_false, rating
    options JSONB, -- Store answer options as JSON
    category VARCHAR(50), -- e.g., 'problem_solving', 'creativity', 'logic'
    skill_area VARCHAR(50), -- e.g., 'game_dev', 'ai', 'web_dev'
    difficulty_level INTEGER DEFAULT 1, -- 1-5 scale
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Student assessments - records of completed assessments
CREATE TABLE student_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    assessment_type VARCHAR(50) DEFAULT 'pathway_finder',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_questions INTEGER,
    questions_answered INTEGER DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    recommended_path_id UUID REFERENCES learning_paths(id),
    assessment_score INTEGER, -- Overall score (0-100)
    strengths TEXT[], -- Array of identified strengths
    interests TEXT[], -- Array of identified interests
    raw_results JSONB, -- Store complete assessment results
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Assessment responses - individual question answers
CREATE TABLE assessment_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES student_assessments(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES assessment_questions(id) ON DELETE CASCADE,
    selected_option VARCHAR(500), -- The chosen answer
    response_value INTEGER, -- Numeric value for scoring
    time_spent_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(assessment_id, question_id)
);

-- =============================================
-- STUDENT PROGRESS TRACKING
-- =============================================

-- Student learning paths - tracks which paths students are enrolled in
CREATE TABLE student_learning_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    path_id UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(student_id, path_id)
);

-- Module progress - tracks progress through individual modules
CREATE TABLE student_module_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    module_id UUID NOT NULL REFERENCES learning_modules(id) ON DELETE CASCADE,
    student_path_id UUID NOT NULL REFERENCES student_learning_paths(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'not_started', -- not_started, in_progress, completed, paused
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    time_spent_minutes INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, module_id)
);

-- =============================================
-- ACTIVITIES & ACHIEVEMENTS
-- =============================================

-- Student activities - log of all student actions
CREATE TABLE student_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL, -- login, module_start, module_complete, assessment_complete, etc.
    activity_description TEXT NOT NULL,
    related_entity_type VARCHAR(50), -- module, path, assessment, etc.
    related_entity_id UUID,
    metadata JSONB, -- Additional activity data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Achievement types - predefined achievements
CREATE TABLE achievement_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    icon VARCHAR(20),
    badge_color VARCHAR(20),
    criteria JSONB, -- Conditions for earning this achievement
    points INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Student achievements - earned achievements
CREATE TABLE student_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    achievement_type_id UUID NOT NULL REFERENCES achievement_types(id) ON DELETE CASCADE,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    progress_data JSONB, -- Data about how achievement was earned
    UNIQUE(student_id, achievement_type_id)
);

-- =============================================
-- PROJECTS & SUBMISSIONS
-- =============================================

-- Student projects - coding projects and assignments
CREATE TABLE student_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    module_id UUID REFERENCES learning_modules(id) ON DELETE CASCADE,
    project_name VARCHAR(200) NOT NULL,
    description TEXT,
    project_type VARCHAR(50), -- game, website, app, etc.
    status VARCHAR(20) DEFAULT 'in_progress', -- in_progress, completed, submitted, reviewed
    code_content TEXT, -- Project code/content
    project_url VARCHAR(500), -- Link to hosted project
    submission_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- SYSTEM & CONFIGURATION
-- =============================================

-- Email verification tokens
CREATE TABLE email_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Password reset tokens
CREATE TABLE password_resets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System settings
CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT,
    setting_type VARCHAR(20) DEFAULT 'string', -- string, integer, boolean, json
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================

-- User-related indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_active ON users(is_active);

-- Student-related indexes
CREATE INDEX idx_students_user_id ON students(user_id);
CREATE INDEX idx_students_age ON students(age);
CREATE INDEX idx_students_active ON students(is_active);

-- Learning path indexes
CREATE INDEX idx_learning_paths_slug ON learning_paths(slug);
CREATE INDEX idx_learning_paths_active ON learning_paths(is_active);
CREATE INDEX idx_learning_modules_path_id ON learning_modules(path_id);
CREATE INDEX idx_learning_modules_sort_order ON learning_modules(sort_order);

-- Assessment indexes
CREATE INDEX idx_student_assessments_student_id ON student_assessments(student_id);
CREATE INDEX idx_student_assessments_completed ON student_assessments(is_completed);
CREATE INDEX idx_student_assessments_path ON student_assessments(recommended_path_id);
CREATE INDEX idx_assessment_responses_assessment ON assessment_responses(assessment_id);

-- Progress tracking indexes
CREATE INDEX idx_student_paths_student_id ON student_learning_paths(student_id);
CREATE INDEX idx_student_paths_path_id ON student_learning_paths(path_id);
CREATE INDEX idx_module_progress_student_id ON student_module_progress(student_id);
CREATE INDEX idx_module_progress_module_id ON student_module_progress(module_id);
CREATE INDEX idx_module_progress_status ON student_module_progress(status);

-- Activity indexes
CREATE INDEX idx_activities_student_id ON student_activities(student_id);
CREATE INDEX idx_activities_type ON student_activities(activity_type);
CREATE INDEX idx_activities_created_at ON student_activities(created_at);

-- Achievement indexes
CREATE INDEX idx_student_achievements_student_id ON student_achievements(student_id);
CREATE INDEX idx_student_achievements_type ON student_achievements(achievement_type_id);

-- Project indexes
CREATE INDEX idx_projects_student_id ON student_projects(student_id);
CREATE INDEX idx_projects_module_id ON student_projects(module_id);
CREATE INDEX idx_projects_status ON student_projects(status);

-- Token indexes
CREATE INDEX idx_email_verifications_token ON email_verifications(token);
CREATE INDEX idx_email_verifications_user ON email_verifications(user_id);
CREATE INDEX idx_password_resets_token ON password_resets(token);
CREATE INDEX idx_password_resets_user ON password_resets(user_id);

-- =============================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_paths_updated_at BEFORE UPDATE ON learning_paths
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_modules_updated_at BEFORE UPDATE ON learning_modules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_assessment_questions_updated_at BEFORE UPDATE ON assessment_questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_module_progress_updated_at BEFORE UPDATE ON student_module_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON student_projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- VIEWS FOR COMMON QUERIES
-- =============================================

-- Student dashboard view
CREATE VIEW student_dashboard_view AS
SELECT 
    s.id as student_id,
    s.student_name,
    s.age,
    u.email as parent_email,
    slp.path_id,
    lp.name as path_name,
    lp.icon as path_icon,
    slp.progress_percentage as path_progress,
    COUNT(smp.id) as total_modules,
    COUNT(CASE WHEN smp.status = 'completed' THEN 1 END) as completed_modules,
    MAX(sa.completed_at) as last_assessment_date,
    sa.recommended_path_id,
    sa.assessment_score
FROM students s
JOIN users u ON s.user_id = u.id
LEFT JOIN student_learning_paths slp ON s.id = slp.student_id AND slp.is_active = true
LEFT JOIN learning_paths lp ON slp.path_id = lp.id
LEFT JOIN student_module_progress smp ON s.id = smp.student_id
LEFT JOIN student_assessments sa ON s.id = sa.student_id AND sa.is_completed = true
WHERE s.is_active = true AND u.is_active = true
GROUP BY s.id, s.student_name, s.age, u.email, slp.path_id, lp.name, lp.icon, 
         slp.progress_percentage, sa.recommended_path_id, sa.assessment_score;

-- Module progress view
CREATE VIEW module_progress_view AS
SELECT 
    smp.student_id,
    smp.module_id,
    lm.title as module_title,
    lm.description as module_description,
    lm.icon as module_icon,
    lm.difficulty_level,
    lm.estimated_hours,
    lm.sort_order,
    lp.name as path_name,
    smp.status,
    smp.progress_percentage,
    smp.time_spent_minutes,
    smp.started_at,
    smp.completed_at,
    smp.last_accessed
FROM student_module_progress smp
JOIN learning_modules lm ON smp.module_id = lm.id
JOIN learning_paths lp ON lm.path_id = lp.id
WHERE lm.is_active = true AND lp.is_active = true;

-- Recent activities view
CREATE VIEW recent_activities_view AS
SELECT 
    sa.student_id,
    s.student_name,
    sa.activity_type,
    sa.activity_description,
    sa.created_at,
    sa.metadata
FROM student_activities sa
JOIN students s ON sa.student_id = s.id
WHERE s.is_active = true
ORDER BY sa.created_at DESC;

-- =============================================
-- COMMENTS
-- =============================================

-- Core tables comments
COMMENT ON TABLE users IS 'Parent/guardian accounts who register students';
COMMENT ON TABLE students IS 'Student profiles linked to parent accounts';
COMMENT ON TABLE learning_paths IS 'Predefined learning tracks (Game Dev, AI, Web Dev, etc.)';
COMMENT ON TABLE learning_modules IS 'Individual lessons/modules within learning paths';

-- Assessment system comments
COMMENT ON TABLE assessment_questions IS 'Questions used in pathway finder assessments';
COMMENT ON TABLE student_assessments IS 'Records of completed pathway finder assessments';
COMMENT ON TABLE assessment_responses IS 'Individual answers to assessment questions';

-- Progress tracking comments
COMMENT ON TABLE student_learning_paths IS 'Links students to their assigned learning paths';
COMMENT ON TABLE student_module_progress IS 'Tracks student progress through individual modules';
COMMENT ON TABLE student_activities IS 'Activity log for analytics and progress tracking';

-- Achievement system comments
COMMENT ON TABLE achievement_types IS 'Predefined achievements students can earn';
COMMENT ON TABLE student_achievements IS 'Achievements earned by students';

-- Project system comments
COMMENT ON TABLE student_projects IS 'Student coding projects and assignments';

-- Security & utility comments
COMMENT ON TABLE email_verifications IS 'Email verification tokens for account activation';
COMMENT ON TABLE password_resets IS 'Password reset tokens for account recovery';
COMMENT ON TABLE system_settings IS 'Application configuration settings';