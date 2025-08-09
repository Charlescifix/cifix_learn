# CIFIX LEARN Backend API

A secure, production-ready FastAPI backend for the CIFIX LEARN educational platform. Built for 10-15 users with comprehensive analytics and monitoring.

## 🚀 Features

- **Complete Authentication System** - JWT-based auth with email verification
- **Student Management** - Full student profiles and progress tracking
- **Assessment Integration** - Streamlit AI assessment tool integration
- **Learning Paths** - 7 comprehensive learning paths (Game Dev, AI/ML, Web Dev, etc.)
- **Progress Tracking** - Detailed learning analytics and achievement system
- **Admin Dashboard** - Comprehensive monitoring and user management
- **Email Service** - AWS SES integration with HTML templates
- **Security** - Rate limiting, input validation, secure headers
- **Analytics** - Comprehensive data collection for user behavior

## 📁 Project Structure

```
backend/
├── app/
│   ├── core/           # Core configurations and security
│   ├── models/         # Database models (SQLAlchemy)
│   ├── routers/        # API endpoints
│   ├── services/       # Business logic services
│   ├── middleware/     # Custom middleware
│   └── database.py     # Database configuration
├── init_db.py          # Database initialization script
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
└── main.py            # FastAPI application entry point
```

## 🛠️ Setup & Installation

### Prerequisites

- Python 3.9+
- PostgreSQL database (Railway recommended)
- AWS SES account (for emails)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd cifix_learn/backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your actual configuration values
```

### 5. Database Setup

```bash
# Initialize database with tables and sample data
python init_db.py
```

### 6. Start the Server

```bash
# Development server
uvicorn main:app --reload

# Production server
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🌐 API Endpoints

### Authentication (`/api/auth`)
- `POST /register` - Register new user
- `POST /login` - User login
- `POST /verify-email` - Verify email address
- `POST /refresh-token` - Refresh JWT token

### Students (`/api/students`)
- `GET /dashboard/{student_id}` - Get student dashboard data
- `POST /` - Create new student
- `GET /{student_id}` - Get student details
- `PUT /{student_id}` - Update student profile

### Assessments (`/api/assessments`)
- `POST /start/{student_id}` - Start new assessment
- `PUT /{assessment_id}/complete` - Complete assessment
- `GET /{assessment_id}` - Get assessment details

### Learning (`/api/learning`)
- `GET /paths` - Get all learning paths
- `GET /paths/{path_id}` - Get path with modules and progress
- `POST /modules/{module_id}/start/{student_id}` - Start module
- `PUT /modules/{module_id}/progress/{student_id}` - Update progress
- `POST /modules/{module_id}/complete/{student_id}` - Complete module

### Admin (`/api/admin`) [Admin Only]
- `GET /dashboard` - System statistics
- `GET /users` - List all users
- `GET /students` - List all students
- `GET /errors` - System error logs
- `GET /analytics/summary` - Analytics summary

## 🗄️ Database Models

### Core Models
- **User** - Parent/guardian accounts
- **Student** - Child profiles with learning data
- **LearningPath** - Educational tracks (Game Dev, AI, etc.)
- **LearningModule** - Individual lessons within paths
- **Assessment** - AI-powered skill assessments

### Analytics Models
- **UserAction** - User behavior tracking
- **LearningAnalytics** - Detailed learning metrics
- **ContentEngagement** - Content interaction data
- **SystemMetrics** - Performance monitoring
- **ErrorLog** - System error tracking

## 🔒 Security Features

- **JWT Authentication** with refresh tokens
- **Password Hashing** using bcrypt (12 rounds)
- **Rate Limiting** on all endpoints
- **Input Validation** with Pydantic
- **SQL Injection Protection** via SQLAlchemy
- **CORS Configuration** for production
- **Security Headers** (CSP, XSS protection, etc.)
- **Request Logging** for monitoring

## 📧 Email Service

Integrated AWS SES for:
- Email verification
- Welcome messages
- Assessment completion notifications
- Progress updates
- System notifications

## 📊 Analytics & Monitoring

### User Analytics
- Page views and session tracking
- Feature usage statistics
- User behavior patterns
- Conversion metrics

### Learning Analytics
- Module completion rates
- Time spent learning
- Progress tracking
- Achievement unlocking
- Difficulty ratings

### System Monitoring
- Error logging and tracking
- Performance metrics
- Health checks
- Admin dashboard

## 🚀 Deployment

### Railway Deployment

1. **Create Railway Project**
```bash
railway login
railway init
```

2. **Add PostgreSQL Database**
```bash
railway add postgresql
```

3. **Set Environment Variables**
```bash
railway variables set SECRET_KEY="your-secret-key"
railway variables set AWS_ACCESS_KEY_ID="your-aws-key"
# ... other variables from .env.example
```

4. **Deploy**
```bash
railway up
```

### Environment Variables

Key variables for production:

```env
# Required
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=your-256-bit-secret
APP_URL=https://your-domain.com
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret

# Optional
DEFAULT_ADMIN_EMAIL=admin@yourdomain.com
DEFAULT_ADMIN_PASSWORD=secure-admin-password
ENVIRONMENT=production
```

## 🧪 Testing

### Manual Testing
1. Start the server: `uvicorn main:app --reload`
2. Visit API docs: `http://localhost:8000/docs`
3. Test endpoints using the interactive documentation

### Health Check
```bash
curl http://localhost:8000/health
```

## 📈 Performance

Optimized for 10-15 concurrent users:
- Async database operations
- Connection pooling
- Efficient query patterns
- Rate limiting
- Response caching headers

## 🔧 Configuration

### Database Settings
- **Connection Pool**: 5-20 connections
- **Query Timeout**: 30 seconds
- **Migration Support**: SQLAlchemy migrations

### Security Settings
- **JWT Expiry**: 30 minutes (configurable)
- **Rate Limits**: 60 req/min per user
- **Password Requirements**: 8+ chars, mixed case, numbers
- **Session Timeout**: 60 minutes

### Email Settings
- **Provider**: AWS SES
- **Templates**: HTML + Text versions
- **Delivery**: Async background processing
- **Retry Logic**: Built-in error handling

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check DATABASE_URL format
postgresql+asyncpg://user:password@host:port/database
```

**Email Not Sending**
```bash
# Verify AWS SES configuration
# Check AWS credentials and region
# Ensure SES domain verification
```

**Rate Limiting Too Strict**
```bash
# Adjust rate limits in middleware settings
# Check IP address detection for localhost
```

### Logs
```bash
# Application logs
tail -f logs/app.log

# Error logs
tail -f logs/error.log
```

## 📞 Support

For deployment assistance or customization:
1. Check the API documentation at `/docs`
2. Review error logs in admin dashboard
3. Monitor system health at `/health`

## 📄 License

Private project for CIFIX LEARN educational platform.

---

Built with FastAPI, SQLAlchemy, PostgreSQL, and AWS SES for a secure, scalable educational backend.