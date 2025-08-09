# CIFIX LEARN Database Setup Instructions

## 🚨 SECURITY FIRST - IMPORTANT NOTICE

**NEVER hardcode passwords or sensitive information in your code or documentation!**

## Database Connection Information
- **Host**: Set in environment variable `DB_HOST`
- **Port**: Set in environment variable `DB_PORT`
- **Database**: Set in environment variable `DB_NAME`
- **Username**: Set in environment variable `DB_USER`
- **Password**: Set in environment variable `DB_PASSWORD`

## Environment Variable Setup

### 1. Copy Environment Template
```bash
cp .env.example .env
```

### 2. Fill in Secure Values
Edit `.env` with your actual credentials:
```bash
# Database Configuration
DB_HOST=switchback.proxy.rlwy.net
DB_PORT=45644
DB_NAME=railway
DB_USER=postgres
DB_PASSWORD=YOUR_ACTUAL_DATABASE_PASSWORD_HERE

# Generate secure keys
JWT_SECRET=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Add your API keys
OPENAI_API_KEY=your_actual_openai_key_here
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
```

## Database Connection Commands

### 1. Connect to Database (Using Environment Variables)
```bash
# Load environment variables first
source .env

# Connect using environment variables
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -p $DB_PORT -d $DB_NAME
```

### 2. Create Schema (Run First)
```sql
\i database_schema.sql
```

### 3. Insert Sample Data (Run Second)
```sql
\i database_seed_data.sql
```

### 4. Set Up Security Features (Run Third)
```sql
\i secure_settings_setup.sql
```

## Alternative Setup Method

If you prefer to run the SQL files directly without `\i` command:

### Step 1: Create Tables
Copy and paste the entire contents of `database_schema.sql` into your PostgreSQL client.

### Step 2: Insert Data  
Copy and paste the entire contents of `database_seed_data.sql` into your PostgreSQL client.

## Verify Installation

After running both SQL files, verify the setup:

```sql
-- Check if all tables were created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check learning paths
SELECT name, description, estimated_hours FROM learning_paths ORDER BY sort_order;

-- Check sample student data
SELECT s.student_name, u.email, lp.name as learning_path
FROM students s
JOIN users u ON s.user_id = u.id
LEFT JOIN student_learning_paths slp ON s.id = slp.student_id
LEFT JOIN learning_paths lp ON slp.path_id = lp.id;
```

## Database Schema Overview

### Core Tables
- **users**: Parent/guardian accounts
- **students**: Student profiles linked to parents
- **learning_paths**: 7 predefined learning tracks
- **learning_modules**: 42 individual lessons (6 per path)

### Assessment System
- **assessment_questions**: 10 pathway finder questions
- **student_assessments**: Assessment completion records
- **assessment_responses**: Individual question answers

### Progress Tracking
- **student_learning_paths**: Path enrollments
- **student_module_progress**: Module completion tracking
- **student_activities**: Activity logging
- **student_achievements**: Achievement system

### Security Features
- **security_audit_log**: Security event monitoring
- **rate_limiting**: Prevent abuse and brute force attacks
- **email_verifications**: Email verification system
- **password_resets**: Secure password reset tokens
- **system_settings**: Secure app configuration (NO hardcoded secrets)

### Additional Features
- **student_projects**: Coding project submissions
- **password validation**: Enforce strong passwords
- **encryption functions**: Protect sensitive data

## Key Features Included

### 1. Complete Assessment System
- 10 carefully crafted questions for pathway finding
- Support for multiple choice, rating, and true/false questions
- Automatic learning path recommendation based on responses

### 2. 7 Learning Paths with 42 Modules
- **Game Development** (30 hours, 6 modules)
- **AI & Machine Learning** (26 hours, 6 modules)  
- **Web Development** (32 hours, 6 modules)
- **Robotics** (30 hours, 6 modules)
- **Data Science** (27 hours, 6 modules)
- **Mobile App Development** (30 hours, 6 modules)
- **General Programming** (32 hours, 6 modules)

### 3. Progress Tracking
- Module completion status
- Time spent tracking
- Progress percentages
- Activity logging

### 4. Achievement System
- 10 predefined achievement types
- Points-based system
- Automatic achievement detection

### 5. Project System
- Student project submissions
- Code storage and URLs
- Project status tracking

### 6. Security Features
- Email verification system
- Password reset functionality
- Encrypted password storage
- UUID-based primary keys

## Important Notes

### Security
- **NO sensitive data is hardcoded** - all credentials come from environment variables
- **Password hashing required** - implement bcrypt with 12+ rounds
- **Rate limiting built-in** - prevent brute force attacks  
- **Security audit logging** - monitor all security events
- **JWT authentication** - secure session management
- **Input validation functions** - prevent SQL injection
- **UUID primary keys** - prevent enumeration attacks
- **Email verification system** - verify user accounts

### Performance
- Comprehensive indexing on all major query columns
- Optimized views for common dashboard queries
- Triggers for automatic timestamp updates

### Scalability
- Designed to handle thousands of students
- JSONB fields for flexible data storage
- Proper foreign key constraints and cascading deletes

## Sample Data Included

The seed data includes:
- 1 sample parent account (parent@example.com)
- 1 sample student (Alex Smith, age 12)
- Complete assessment responses
- Progress in Game Development path
- Sample activities and achievements

## API Integration Points

The database is designed to work with:
- Your external assessment tool at `kid-assessment.streamlit.app`
- OpenAI API for AI-powered features
- AWS SES for email notifications
- Your frontend learning modules system

## 🔐 CRITICAL SECURITY SETUP

Before going to production, you MUST:

### 1. Generate Secure Keys
```bash
# Generate JWT secret
JWT_SECRET=$(openssl rand -base64 32)

# Generate encryption key  
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Add to your .env file
echo "JWT_SECRET=$JWT_SECRET" >> .env
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env
```

### 2. Verify Security Settings
```sql
-- Check all security settings are configured
SELECT * FROM verify_system_settings();
```

### 3. Test Security Functions
```sql
-- Test password validation
SELECT * FROM validate_password_strength('weakpass');
SELECT * FROM validate_password_strength('StrongP@ssw0rd123!');

-- Test rate limiting
SELECT * FROM check_rate_limit('192.168.1.100', 'login_attempt', 3, 5);
```

### 4. Enable Security Monitoring
```sql
-- View recent security events
SELECT * FROM security_audit_log 
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

## Next Steps

After setting up the secure database:

1. **Review security guide** - Read `security_implementation_guide.md`
2. **Implement password hashing** - Use bcrypt in your backend
3. **Set up JWT authentication** - Secure session management
4. **Enable HTTPS** - Never run production without SSL/TLS
5. **Implement rate limiting** - Use database functions in your API
6. **Set up monitoring** - Monitor security audit logs
7. **Update frontend** to use database instead of localStorage
8. **Create secure API endpoints** with proper validation
9. **Connect assessment tool** to store results securely
10. **Add learning content** with proper access controls

## 🚨 SECURITY WARNINGS

### DO NOT:
- ❌ Hardcode passwords or API keys in code
- ❌ Commit `.env` file to version control
- ❌ Run in production without HTTPS
- ❌ Skip password hashing implementation
- ❌ Ignore rate limiting on login endpoints
- ❌ Deploy without proper environment variable setup

### DO:
- ✅ Use environment variables for all sensitive data
- ✅ Implement bcrypt password hashing
- ✅ Enable JWT authentication
- ✅ Use HTTPS in production
- ✅ Monitor security audit logs
- ✅ Regularly update dependencies
- ✅ Use parameterized queries to prevent SQL injection
- ✅ Implement proper input validation

## Support

If you encounter any issues:
1. **Security Issues**: Read `security_implementation_guide.md` first
2. **Database Issues**: Check PostgreSQL client installation
3. **Connection Issues**: Verify network connection and credentials
4. **Setup Issues**: Ensure environment variables are properly set
5. **SQL Errors**: Check syntax and table dependencies

**Remember**: Security is not optional - it's essential for protecting student and parent data!

The schema includes comprehensive security features, comments, and is designed to be production-ready with proper setup.