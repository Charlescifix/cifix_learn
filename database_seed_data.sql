-- CIFIX LEARN Database Seed Data
-- Sample data for testing and initial setup
-- Run this after creating the main schema

-- =============================================
-- LEARNING PATHS DATA
-- =============================================

INSERT INTO learning_paths (id, name, slug, description, icon, difficulty_level, estimated_hours, sort_order) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Game Development', 'game-development', 'Learn to create engaging games and interactive experiences using modern programming languages and game engines.', '🎮', 'Beginner', 30, 1),
('550e8400-e29b-41d4-a716-446655440002', 'AI & Machine Learning', 'ai-machine-learning', 'Discover the fascinating world of artificial intelligence and machine learning through hands-on projects.', '🤖', 'Beginner', 26, 2),
('550e8400-e29b-41d4-a716-446655440003', 'Web Development', 'web-development', 'Create amazing websites and web applications that millions of people can use and enjoy.', '🌐', 'Beginner', 32, 3),
('550e8400-e29b-41d4-a716-446655440004', 'Robotics', 'robotics', 'Build and program robots that can move, sense their environment, and perform tasks autonomously.', '🤖', 'Beginner', 30, 4),
('550e8400-e29b-41d4-a716-446655440005', 'Data Science', 'data-science', 'Learn to collect, analyze, and visualize data to discover patterns and make informed decisions.', '📊', 'Beginner', 27, 5),
('550e8400-e29b-41d4-a716-446655440006', 'Mobile App Development', 'mobile-app-development', 'Create mobile applications for smartphones and tablets that people use every day.', '📱', 'Beginner', 30, 6),
('550e8400-e29b-41d4-a716-446655440007', 'General Programming', 'general-programming', 'Build a strong foundation in programming concepts and multiple languages to become a versatile developer.', '💻', 'Beginner', 32, 7);

-- =============================================
-- LEARNING MODULES DATA
-- =============================================

-- Game Development Modules
INSERT INTO learning_modules (id, path_id, title, description, icon, difficulty_level, estimated_hours, sort_order, learning_objectives, topics, is_locked) VALUES
('650e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'Programming Fundamentals', 'Learn the basics of programming with Python - variables, loops, functions, and basic algorithms.', '💻', 'Beginner', 4, 1, ARRAY['Understand variables and data types', 'Write functions and use parameters', 'Implement loops and conditionals'], ARRAY['Variables', 'Functions', 'Loops', 'Conditionals', 'Data Types'], false),
('650e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'Game Logic & Algorithms', 'Understanding game mechanics, player input, collision detection, and basic AI behaviors.', '🧩', 'Beginner', 5, 2, ARRAY['Implement game loops', 'Handle user input', 'Detect collisions'], ARRAY['Game Loops', 'Input Handling', 'Collision Detection', 'Basic AI', 'State Management'], false),
('650e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 'Graphics & Animation', 'Create visual elements, sprites, animations, and learn about 2D graphics programming.', '🎨', 'Intermediate', 6, 3, ARRAY['Create sprites and animations', 'Implement visual effects', 'Design user interfaces'], ARRAY['Sprites', '2D Graphics', 'Animation', 'Visual Effects', 'UI Design'], true),
('650e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440001', 'Game Engines (Scratch/GameMaker)', 'Hands-on experience with beginner-friendly game development tools and engines.', '🔧', 'Intermediate', 4, 4, ARRAY['Use visual programming tools', 'Manage game assets', 'Design game scenes'], ARRAY['Scratch Programming', 'GameMaker Basics', 'Asset Management', 'Scene Design'], true),
('650e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440001', 'Sound & Music Integration', 'Add audio effects, background music, and create immersive soundscapes for your games.', '🎵', 'Intermediate', 3, 5, ARRAY['Integrate sound effects', 'Add background music', 'Create audio systems'], ARRAY['Sound Effects', 'Background Music', 'Audio Programming', 'Sound Design'], true),
('650e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440001', 'Complete Game Project', 'Build a complete game from concept to finished product, including testing and polishing.', '🚀', 'Advanced', 8, 6, ARRAY['Design complete game', 'Implement full gameplay', 'Test and polish'], ARRAY['Game Design', 'Project Management', 'Testing', 'Publishing', 'Portfolio'], true);

-- AI & Machine Learning Modules
INSERT INTO learning_modules (id, path_id, title, description, icon, difficulty_level, estimated_hours, sort_order, learning_objectives, topics, is_locked) VALUES
('650e8400-e29b-41d4-a716-446655440011', '550e8400-e29b-41d4-a716-446655440002', 'Introduction to AI', 'Understanding what AI is, how it works, and exploring real-world applications.', '🧠', 'Beginner', 3, 1, ARRAY['Define artificial intelligence', 'Identify AI in daily life', 'Understand AI ethics'], ARRAY['What is AI?', 'Types of AI', 'AI in Daily Life', 'Ethics in AI', 'Future of AI'], false),
('650e8400-e29b-41d4-a716-446655440012', '550e8400-e29b-41d4-a716-446655440002', 'Data and Patterns', 'Learn how computers recognize patterns in data and make predictions.', '📊', 'Beginner', 4, 2, ARRAY['Collect and organize data', 'Recognize patterns', 'Create visualizations'], ARRAY['Data Collection', 'Pattern Recognition', 'Data Visualization', 'Statistics Basics'], false),
('650e8400-e29b-41d4-a716-446655440013', '550e8400-e29b-41d4-a716-446655440002', 'Machine Learning Basics', 'Build your first machine learning models using kid-friendly tools and platforms.', '⚙️', 'Intermediate', 5, 3, ARRAY['Train machine learning models', 'Make predictions', 'Evaluate model performance'], ARRAY['Supervised Learning', 'Training Models', 'Making Predictions', 'Model Evaluation'], true),
('650e8400-e29b-41d4-a716-446655440014', '550e8400-e29b-41d4-a716-446655440002', 'Computer Vision', 'Teach computers to "see" and recognize images, faces, and objects.', '👁️', 'Intermediate', 4, 4, ARRAY['Implement image recognition', 'Detect objects', 'Build visual AI systems'], ARRAY['Image Recognition', 'Object Detection', 'Face Recognition', 'Visual AI'], true),
('650e8400-e29b-41d4-a716-446655440015', '550e8400-e29b-41d4-a716-446655440002', 'Natural Language Processing', 'Help computers understand and generate human language - build chatbots and language tools.', '💬', 'Intermediate', 4, 5, ARRAY['Analyze text data', 'Build chatbots', 'Implement language translation'], ARRAY['Text Analysis', 'Chatbots', 'Language Translation', 'Sentiment Analysis'], true),
('650e8400-e29b-41d4-a716-446655440016', '550e8400-e29b-41d4-a716-446655440002', 'AI Project Showcase', 'Create your own AI application and present it to showcase your skills.', '🎯', 'Advanced', 6, 6, ARRAY['Plan AI project', 'Implement AI solution', 'Present project'], ARRAY['Project Planning', 'AI Implementation', 'Testing & Debugging', 'Presentation Skills'], true);

-- Web Development Modules
INSERT INTO learning_modules (id, path_id, title, description, icon, difficulty_level, estimated_hours, sort_order, learning_objectives, topics, is_locked) VALUES
('650e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440003', 'HTML Fundamentals', 'Learn the building blocks of websites - create your first web pages with HTML.', '📄', 'Beginner', 4, 1, ARRAY['Create HTML documents', 'Use semantic elements', 'Build web forms'], ARRAY['HTML Structure', 'Tags & Elements', 'Links & Images', 'Forms', 'Semantic HTML'], false),
('650e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440003', 'CSS Styling', 'Make your websites beautiful with colors, fonts, layouts, and animations.', '🎨', 'Beginner', 5, 2, ARRAY['Style web pages', 'Create layouts', 'Add animations'], ARRAY['CSS Selectors', 'Colors & Fonts', 'Layout', 'Flexbox', 'Animations'], false),
('650e8400-e29b-41d4-a716-446655440023', '550e8400-e29b-41d4-a716-446655440003', 'JavaScript Interactivity', 'Add interactive features, buttons, forms, and dynamic content to your websites.', '⚡', 'Intermediate', 6, 3, ARRAY['Write interactive JavaScript', 'Manipulate web pages', 'Handle user events'], ARRAY['Variables & Functions', 'DOM Manipulation', 'Event Handling', 'Interactive Features'], true),
('650e8400-e29b-41d4-a716-446655440024', '550e8400-e29b-41d4-a716-446655440003', 'Responsive Design', 'Make websites that look great on phones, tablets, and computers.', '📱', 'Intermediate', 4, 4, ARRAY['Create mobile-first designs', 'Use media queries', 'Build responsive layouts'], ARRAY['Mobile-First Design', 'Media Queries', 'Grid Systems', 'Touch Interfaces'], true),
('650e8400-e29b-41d4-a716-446655440025', '550e8400-e29b-41d4-a716-446655440003', 'Web APIs & Data', 'Connect your websites to external data sources and services.', '🔌', 'Intermediate', 5, 5, ARRAY['Use web APIs', 'Fetch external data', 'Store data locally'], ARRAY['API Basics', 'Fetching Data', 'JSON', 'Local Storage', 'Third-party Services'], true),
('650e8400-e29b-41d4-a716-446655440026', '550e8400-e29b-41d4-a716-446655440003', 'Final Web Project', 'Build a complete website or web application from start to finish.', '🚀', 'Advanced', 8, 6, ARRAY['Plan web project', 'Develop complete website', 'Deploy to web'], ARRAY['Project Planning', 'Full Development', 'Testing', 'Deployment', 'Portfolio'], true);

-- =============================================
-- ASSESSMENT QUESTIONS DATA
-- =============================================

INSERT INTO assessment_questions (id, question_text, question_type, options, category, skill_area, difficulty_level) VALUES
('750e8400-e29b-41d4-a716-446655440001', 'What sounds most exciting to you?', 'multiple_choice', '{"options": ["Creating fun games and interactive stories", "Teaching computers to think and learn like humans", "Building websites that millions of people can visit", "Programming robots to move and perform tasks", "Analyzing data to discover hidden patterns", "Making mobile apps for phones and tablets"]}', 'interest', 'general', 1),
('750e8400-e29b-41d4-a716-446655440002', 'When you see a problem, you usually...', 'multiple_choice', '{"options": ["Break it down into smaller, manageable pieces", "Look for patterns or similar problems you''ve solved before", "Try different approaches until something works", "Ask for help or look up solutions online", "Think about it step by step logically"]}', 'problem_solving', 'general', 2),
('750e8400-e29b-41d4-a716-446655440003', 'Which type of math do you enjoy most?', 'multiple_choice', '{"options": ["Geometry and shapes", "Statistics and probability", "Algebra and equations", "Logic puzzles", "I don''t really enjoy math"]}', 'academic_preference', 'general', 1),
('750e8400-e29b-41d4-a716-446655440004', 'What do you like to do in your free time?', 'multiple_choice', '{"options": ["Play video games", "Build things with blocks or LEGO", "Draw, paint, or design", "Read books or research topics online", "Play sports or be active", "Hang out with friends and family"]}', 'interest', 'general', 1),
('750e8400-e29b-41d4-a716-446655440005', 'If you could create something amazing, what would it be?', 'multiple_choice', '{"options": ["A fun game that everyone wants to play", "A robot that can help people with daily tasks", "A website that solves a real problem", "An app that makes life easier", "A system that can predict the future", "A tool that helps people learn better"]}', 'creativity', 'general', 1),
('750e8400-e29b-41d4-a716-446655440006', 'How do you prefer to learn new things?', 'multiple_choice', '{"options": ["Hands-on practice and experimentation", "Reading instructions and following steps", "Watching videos and demonstrations", "Working with others in groups", "Figuring things out on my own"]}', 'learning_style', 'general', 1),
('750e8400-e29b-41d4-a716-446655440007', 'What type of projects excite you most?', 'multiple_choice', '{"options": ["Interactive games and animations", "Smart systems that can make decisions", "Beautiful websites and user interfaces", "Physical devices that move and respond", "Charts and graphs that show insights", "Apps that people use every day"]}', 'interest', 'specific', 2),
('750e8400-e29b-41d4-a716-446655440008', 'When working on a challenging task, you...', 'multiple_choice', '{"options": ["Keep trying different approaches until it works", "Take breaks and come back with fresh ideas", "Ask for help when you get stuck", "Research similar solutions online", "Break it into smaller, easier parts"]}', 'persistence', 'general', 2),
('750e8400-e29b-41d4-a716-446655440009', 'Which superpower would you choose?', 'multiple_choice', '{"options": ["Control technology with your mind", "See patterns and connections others miss", "Create anything you imagine", "Communicate with any device", "Predict what will happen next", "Make complex things simple"]}', 'personality', 'general', 1),
('750e8400-e29b-41d4-a716-446655440010', 'What motivates you to keep learning?', 'multiple_choice', '{"options": ["Seeing my creations come to life", "Solving puzzles and challenges", "Helping others with my skills", "Being recognized for my work", "Understanding how things work", "Building something useful"]}', 'motivation', 'general', 2);

-- =============================================
-- ACHIEVEMENT TYPES DATA
-- =============================================

INSERT INTO achievement_types (id, name, description, icon, badge_color, criteria, points) VALUES
('850e8400-e29b-41d4-a716-446655440001', 'First Steps', 'Complete your first learning module', '🌟', '#FFD93D', '{"type": "module_completion", "count": 1}', 100),
('850e8400-e29b-41d4-a716-446655440002', '7-Day Streak', 'Learn for 7 consecutive days', '🔥', '#FF8C42', '{"type": "consecutive_days", "count": 7}', 200),
('850e8400-e29b-41d4-a716-446655440003', 'Quick Learner', 'Complete 3 modules in one day', '🎯', '#5B47B0', '{"type": "modules_per_day", "count": 3}', 150),
('850e8400-e29b-41d4-a716-446655440004', 'Problem Solver', 'Complete 5 coding challenges', '💡', '#00D9C0', '{"type": "challenges_completed", "count": 5}', 250),
('850e8400-e29b-41d4-a716-446655440005', 'Team Player', 'Help another student in the forums', '🤝', '#FF6B9D', '{"type": "forum_help", "count": 1}', 150),
('850e8400-e29b-41d4-a716-446655440006', 'Path Completer', 'Finish an entire learning path', '🏆', '#10B981', '{"type": "path_completion", "count": 1}', 500),
('850e8400-e29b-41d4-a716-446655440007', 'Code Creator', 'Submit your first project', '🛠️', '#8B5CF6', '{"type": "project_submission", "count": 1}', 200),
('850e8400-e29b-41d4-a716-446655440008', 'Early Bird', 'Complete a lesson before 9 AM', '🌅', '#F59E0B', '{"type": "early_completion", "hour": 9}', 100),
('850e8400-e29b-41d4-a716-446655440009', 'Night Owl', 'Complete a lesson after 9 PM', '🦉', '#6366F1', '{"type": "late_completion", "hour": 21}', 100),
('850e8400-e29b-41d4-a716-446655440010', 'Explorer', 'Try modules from 3 different paths', '🗺️', '#EC4899', '{"type": "path_diversity", "count": 3}', 300);

-- =============================================
-- SYSTEM SETTINGS DATA
-- =============================================

-- IMPORTANT: System settings should be populated from environment variables
-- Run the secure_settings_setup.sql script after this to set values from environment variables
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, is_public) VALUES
('app_name', 'CIFIX LEARN', 'string', 'Application name', true),
('app_version', '1.0.0', 'string', 'Current application version', true),
('maintenance_mode', 'false', 'boolean', 'Enable maintenance mode', false),
('max_assessment_time_minutes', '30', 'integer', 'Maximum time allowed for assessment completion', false),
('email_verification_required', 'true', 'boolean', 'Require email verification for new accounts', false),
('openai_api_key', '', 'string', 'OpenAI API key for AI features - SET FROM ENV VAR', false),
('aws_access_key_id', '', 'string', 'AWS Access Key ID - SET FROM ENV VAR', false),
('aws_secret_access_key', '', 'string', 'AWS Secret Access Key - SET FROM ENV VAR', false),
('aws_region', '', 'string', 'AWS region for SES email service - SET FROM ENV VAR', false),
('ses_source_email', '', 'string', 'Source email for SES notifications - SET FROM ENV VAR', false),
('ses_reply_to_email', '', 'string', 'Reply-to email for notifications - SET FROM ENV VAR', false),
('ses_configuration_set', '', 'string', 'SES configuration set - SET FROM ENV VAR', false),
('jwt_secret_key', '', 'string', 'JWT secret key for authentication - SET FROM ENV VAR', false),
('encryption_key', '', 'string', 'Database encryption key - SET FROM ENV VAR', false),
('default_learning_path', 'general-programming', 'string', 'Default learning path for new students', false),
('assessment_pass_percentage', '70', 'integer', 'Minimum percentage to pass assessments', false);

-- =============================================
-- SAMPLE TEST DATA (Optional - for development)
-- =============================================

-- Sample user account
INSERT INTO users (id, email, password_hash, first_name, last_name, phone, email_verified) VALUES
('450e8400-e29b-41d4-a716-446655440001', 'parent@example.com', '$2b$10$example_hash_here', 'John', 'Smith', '+1234567890', true);

-- Sample student
INSERT INTO students (id, user_id, student_name, age, grade_level, school_name, parent_name) VALUES
('350e8400-e29b-41d4-a716-446655440001', '450e8400-e29b-41d4-a716-446655440001', 'Alex Smith', 12, '7th Grade', 'Lincoln Middle School', 'John Smith');

-- Sample assessment
INSERT INTO student_assessments (id, student_id, assessment_type, completed_at, total_questions, questions_answered, recommended_path_id, assessment_score, strengths, interests, is_completed) VALUES
('950e8400-e29b-41d4-a716-446655440001', '350e8400-e29b-41d4-a716-446655440001', 'pathway_finder', CURRENT_TIMESTAMP, 10, 10, '550e8400-e29b-41d4-a716-446655440001', 85, ARRAY['Problem Solving', 'Creativity', 'Logical Thinking'], ARRAY['Games', 'Interactive Media', 'Storytelling'], true);

-- Sample learning path enrollment
INSERT INTO student_learning_paths (id, student_id, path_id, assigned_at, started_at, progress_percentage) VALUES
('250e8400-e29b-41d4-a716-446655440001', '350e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 25.00);

-- Sample module progress
INSERT INTO student_module_progress (id, student_id, module_id, student_path_id, status, started_at, completed_at, progress_percentage, time_spent_minutes) VALUES
('150e8400-e29b-41d4-a716-446655440001', '350e8400-e29b-41d4-a716-446655440001', '650e8400-e29b-41d4-a716-446655440001', '250e8400-e29b-41d4-a716-446655440001', 'completed', CURRENT_TIMESTAMP - INTERVAL '2 days', CURRENT_TIMESTAMP - INTERVAL '1 day', 100.00, 240),
('150e8400-e29b-41d4-a716-446655440002', '350e8400-e29b-41d4-a716-446655440001', '650e8400-e29b-41d4-a716-446655440002', '250e8400-e29b-41d4-a716-446655440001', 'in_progress', CURRENT_TIMESTAMP - INTERVAL '1 day', NULL, 45.00, 120);

-- Sample activities
INSERT INTO student_activities (student_id, activity_type, activity_description, related_entity_type, related_entity_id) VALUES
('350e8400-e29b-41d4-a716-446655440001', 'assessment_complete', 'Completed pathway finder assessment', 'assessment', '950e8400-e29b-41d4-a716-446655440001'),
('350e8400-e29b-41d4-a716-446655440001', 'module_complete', 'Completed "Programming Fundamentals" module', 'module', '650e8400-e29b-41d4-a716-446655440001'),
('350e8400-e29b-41d4-a716-446655440001', 'module_start', 'Started "Game Logic & Algorithms" module', 'module', '650e8400-e29b-41d4-a716-446655440002');

-- Sample achievements
INSERT INTO student_achievements (student_id, achievement_type_id, earned_at) VALUES
('350e8400-e29b-41d4-a716-446655440001', '850e8400-e29b-41d4-a716-446655440001', CURRENT_TIMESTAMP - INTERVAL '1 day'),
('350e8400-e29b-41d4-a716-446655440001', '850e8400-e29b-41d4-a716-446655440007', CURRENT_TIMESTAMP);

-- =============================================
-- UTILITY FUNCTIONS
-- =============================================

-- Function to get student progress summary
CREATE OR REPLACE FUNCTION get_student_progress_summary(student_uuid UUID)
RETURNS TABLE (
    path_name VARCHAR,
    total_modules INTEGER,
    completed_modules INTEGER,
    progress_percentage DECIMAL,
    current_module VARCHAR,
    total_time_spent INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        lp.name as path_name,
        COUNT(lm.id)::INTEGER as total_modules,
        COUNT(CASE WHEN smp.status = 'completed' THEN 1 END)::INTEGER as completed_modules,
        COALESCE(slp.progress_percentage, 0) as progress_percentage,
        COALESCE(current_mod.title, 'No module in progress') as current_module,
        COALESCE(SUM(smp.time_spent_minutes)::INTEGER, 0) as total_time_spent
    FROM student_learning_paths slp
    JOIN learning_paths lp ON slp.path_id = lp.id
    LEFT JOIN learning_modules lm ON lp.id = lm.path_id AND lm.is_active = true
    LEFT JOIN student_module_progress smp ON slp.student_id = smp.student_id AND lm.id = smp.module_id
    LEFT JOIN learning_modules current_mod ON current_mod.id = (
        SELECT module_id FROM student_module_progress 
        WHERE student_id = student_uuid AND status = 'in_progress' 
        LIMIT 1
    )
    WHERE slp.student_id = student_uuid AND slp.is_active = true
    GROUP BY lp.name, slp.progress_percentage, current_mod.title;
END;
$$ LANGUAGE plpgsql;

-- Function to check if module can be unlocked
CREATE OR REPLACE FUNCTION can_unlock_module(student_uuid UUID, module_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    module_sort_order INTEGER;
    previous_completed BOOLEAN;
BEGIN
    -- Get the sort order of the requested module
    SELECT sort_order INTO module_sort_order
    FROM learning_modules
    WHERE id = module_uuid;
    
    -- If this is the first module (sort_order = 1), it's always unlocked
    IF module_sort_order = 1 THEN
        RETURN TRUE;
    END IF;
    
    -- Check if the previous module is completed
    SELECT EXISTS(
        SELECT 1 
        FROM student_module_progress smp
        JOIN learning_modules lm ON smp.module_id = lm.id
        WHERE smp.student_id = student_uuid 
        AND lm.path_id = (SELECT path_id FROM learning_modules WHERE id = module_uuid)
        AND lm.sort_order = module_sort_order - 1
        AND smp.status = 'completed'
    ) INTO previous_completed;
    
    RETURN previous_completed;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- COMMENTS FOR SEED DATA
-- =============================================

COMMENT ON FUNCTION get_student_progress_summary IS 'Returns comprehensive progress summary for a student';
COMMENT ON FUNCTION can_unlock_module IS 'Checks if a student can unlock a specific module based on prerequisites';