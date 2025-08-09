# CIFIX LEARN Security Implementation Guide

## 🔒 CRITICAL SECURITY REQUIREMENTS

### 1. Environment Variables Configuration

**NEVER** hardcode sensitive information. Use environment variables:

```bash
# Generate secure random strings for these:
JWT_SECRET="your-256-bit-secret-key-here"
ENCRYPTION_KEY="your-encryption-key-here"
DB_PASSWORD="your-database-password-here"

# API Keys (keep secret)
OPENAI_API_KEY="sk-proj-your-openai-key-here"
AWS_ACCESS_KEY_ID="your-aws-access-key"
AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
```

### 2. Password Security

**REQUIRED**: Implement proper password hashing

```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt with configurable rounds"""
    rounds = int(os.getenv('BCRYPT_ROUNDS', 12))
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

### 3. Database Security

**IMPLEMENTED**: Security features in database

- ✅ UUID primary keys (prevents enumeration)
- ✅ Password strength validation function
- ✅ Rate limiting system
- ✅ Security audit logging
- ✅ Data encryption functions (placeholders for pgcrypto)

### 4. Authentication & Authorization

**REQUIRED**: JWT-based authentication with proper security

```python
import jwt
from datetime import datetime, timedelta

def create_jwt_token(user_id: str, email: str) -> str:
    """Create secure JWT token"""
    payload = {
        'user_id': user_id,
        'email': email,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=int(os.getenv('SESSION_TIMEOUT', 86400)))
    }
    return jwt.encode(payload, os.getenv('JWT_SECRET'), algorithm='HS256')

def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT token"""
    return jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
```

### 5. Input Validation & Sanitization

**REQUIRED**: Validate all inputs

```python
import re
from typing import Optional

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def sanitize_input(input_str: str) -> str:
    """Basic input sanitization"""
    # Remove null bytes and normalize whitespace
    return ' '.join(input_str.replace('\x00', '').split())

def validate_student_age(age: int) -> bool:
    """Validate student age is within acceptable range"""
    return 5 <= age <= 18
```

### 6. Rate Limiting (Database Level)

**IMPLEMENTED**: Use the database rate limiting functions

```sql
-- Check rate limit before allowing action
SELECT * FROM check_rate_limit(
    user_ip::VARCHAR,     -- IP address or user identifier  
    'login_attempt',      -- Action type
    5,                    -- Max attempts
    15                    -- Window in minutes
);
```

### 7. Security Headers & CORS

**REQUIRED**: Implement security headers

```python
# Example for Flask/FastAPI
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'",
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}
```

### 8. Data Encryption

**RECOMMENDED**: Use pgcrypto extension for sensitive data

```sql
-- Install pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt sensitive data
INSERT INTO users (password_hash) 
VALUES (pgp_sym_encrypt('sensitive_data', 'encryption_key'));

-- Decrypt when needed
SELECT pgp_sym_decrypt(password_hash::bytea, 'encryption_key') 
FROM users WHERE id = 'user_id';
```

### 9. SQL Injection Prevention

**REQUIRED**: Use parameterized queries ONLY

```python
# ✅ CORRECT - Parameterized query
cursor.execute(
    "SELECT * FROM users WHERE email = %s AND password_hash = %s",
    (email, hashed_password)
)

# ❌ WRONG - SQL injection vulnerability
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

### 10. Session Management

**REQUIRED**: Secure session handling

```python
import secrets

def generate_session_token() -> str:
    """Generate cryptographically secure session token"""
    return secrets.token_urlsafe(32)

def invalidate_session(session_token: str):
    """Invalidate session token"""
    # Remove from session store or blacklist
    pass
```

## 🛡️ SECURITY CHECKLIST

### Before Deployment:

- [ ] All environment variables set with strong values
- [ ] No sensitive data hardcoded in source code
- [ ] Password hashing implemented (bcrypt)
- [ ] JWT authentication implemented
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (parameterized queries)
- [ ] Rate limiting enabled
- [ ] CORS configured properly
- [ ] HTTPS enforced in production
- [ ] Security headers implemented
- [ ] Error messages don't leak sensitive information
- [ ] File upload restrictions (if applicable)
- [ ] Database backup encryption
- [ ] Security audit logging enabled
- [ ] Dependency vulnerability scanning

### Database Security:

- [ ] Use `verify_system_settings()` function to check configuration
- [ ] Enable security audit logging
- [ ] Set up rate limiting for critical actions
- [ ] Use password strength validation
- [ ] Enable pgcrypto for sensitive data encryption
- [ ] Regular security audits of logs

### Monitoring & Alerts:

```sql
-- Monitor failed login attempts
SELECT COUNT(*) as failed_attempts, ip_address
FROM security_audit_log 
WHERE event_type = 'LOGIN_FAILED'
AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY ip_address
HAVING COUNT(*) > 5;

-- Monitor rate limit violations  
SELECT * FROM security_audit_log
WHERE event_type = 'RATE_LIMIT_EXCEEDED'
AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

## 🚨 IMMEDIATE ACTIONS REQUIRED

1. **Generate Secure Keys**: Create strong random values for JWT_SECRET and ENCRYPTION_KEY
2. **Set Database Password**: Add secure password to DB_PASSWORD
3. **Configure API Keys**: Add your actual OpenAI and AWS keys
4. **Implement Password Hashing**: Use bcrypt for all password operations
5. **Set Up HTTPS**: Never run in production without SSL/TLS
6. **Enable Security Logging**: Use the security audit functions
7. **Configure Rate Limiting**: Implement rate limiting on critical endpoints

## 📋 SECURITY TESTING

### Password Strength Testing:
```sql
SELECT * FROM validate_password_strength('weakpass');
SELECT * FROM validate_password_strength('StrongP@ssw0rd123!');
```

### Rate Limiting Testing:
```sql
-- Test rate limiting
SELECT * FROM check_rate_limit('192.168.1.100', 'login_attempt', 3, 5);
```

### Settings Verification:
```sql
-- Check all security settings are configured
SELECT * FROM verify_system_settings();
```

## 🔧 PRODUCTION DEPLOYMENT SECURITY

1. **Environment Variables**: Use secure secret management (AWS Secrets Manager, Azure Key Vault, etc.)
2. **Database Access**: Restrict database access to application servers only
3. **Network Security**: Use VPCs and security groups
4. **Monitoring**: Set up security monitoring and alerting
5. **Backup Security**: Encrypt database backups
6. **Regular Updates**: Keep all dependencies updated
7. **Penetration Testing**: Regular security assessments

Remember: Security is not optional - it's essential for protecting student and parent data!