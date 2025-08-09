-- SECURE SETTINGS SETUP
-- Run this script to populate system settings from environment variables
-- This script should be executed after the main seed data script
-- NEVER commit this file with actual values - use environment variables only

-- Create a function to securely update system settings from environment variables
CREATE OR REPLACE FUNCTION update_system_settings_from_env()
RETURNS VOID AS $$
BEGIN
    -- This function would be called from your application code
    -- with values from environment variables, not from SQL
    
    RAISE NOTICE 'System settings should be updated from application code using environment variables';
    RAISE NOTICE 'Example usage in your application:';
    RAISE NOTICE 'UPDATE system_settings SET setting_value = ENV_VAR WHERE setting_key = ''openai_api_key''';
    
    -- Template for updating settings (DO NOT PUT REAL VALUES HERE)
    -- UPDATE system_settings SET setting_value = $ENV{OPENAI_API_KEY} WHERE setting_key = 'openai_api_key';
    -- UPDATE system_settings SET setting_value = $ENV{AWS_ACCESS_KEY_ID} WHERE setting_key = 'aws_access_key_id';
    -- UPDATE system_settings SET setting_value = $ENV{AWS_SECRET_ACCESS_KEY} WHERE setting_key = 'aws_secret_access_key';
    -- UPDATE system_settings SET setting_value = $ENV{AWS_REGION} WHERE setting_key = 'aws_region';
    -- UPDATE system_settings SET setting_value = $ENV{SES_SOURCE_EMAIL} WHERE setting_key = 'ses_source_email';
    -- UPDATE system_settings SET setting_value = $ENV{SES_REPLY_TO_EMAIL} WHERE setting_key = 'ses_reply_to_email';
    -- UPDATE system_settings SET setting_value = $ENV{SES_CONFIGURATION_SET} WHERE setting_key = 'ses_configuration_set';
    -- UPDATE system_settings SET setting_value = $ENV{JWT_SECRET_KEY} WHERE setting_key = 'jwt_secret_key';
    -- UPDATE system_settings SET setting_value = $ENV{ENCRYPTION_KEY} WHERE setting_key = 'encryption_key';
    
END;
$$ LANGUAGE plpgsql;

-- Function to verify all required settings are configured
CREATE OR REPLACE FUNCTION verify_system_settings()
RETURNS TABLE (
    setting_key VARCHAR(100),
    is_configured BOOLEAN,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ss.setting_key,
        CASE 
            WHEN ss.setting_value IS NULL OR ss.setting_value = '' THEN FALSE
            ELSE TRUE
        END as is_configured,
        CASE 
            WHEN ss.setting_value IS NULL OR ss.setting_value = '' THEN 'NOT CONFIGURED - SECURITY RISK'
            WHEN ss.is_public = FALSE AND LENGTH(ss.setting_value) < 10 THEN 'WEAK VALUE - SECURITY RISK'
            ELSE 'OK'
        END as status
    FROM system_settings ss
    WHERE ss.setting_key IN (
        'openai_api_key',
        'aws_access_key_id', 
        'aws_secret_access_key',
        'aws_region',
        'ses_source_email',
        'ses_reply_to_email',
        'jwt_secret_key',
        'encryption_key'
    )
    ORDER BY ss.setting_key;
END;
$$ LANGUAGE plpgsql;

-- Function to encrypt sensitive data
CREATE OR REPLACE FUNCTION encrypt_sensitive_field(plaintext TEXT, encryption_key TEXT)
RETURNS TEXT AS $$
BEGIN
    -- In production, use proper encryption like pgcrypto
    -- This is a placeholder - implement proper encryption
    IF plaintext IS NULL OR plaintext = '' THEN
        RETURN NULL;
    END IF;
    
    -- This would use proper encryption in production
    -- RETURN pgp_sym_encrypt(plaintext, encryption_key);
    
    -- For now, just indicate data should be encrypted
    RETURN 'ENCRYPTED:' || LENGTH(plaintext) || ':chars';
END;
$$ LANGUAGE plpgsql;

-- Function to decrypt sensitive data
CREATE OR REPLACE FUNCTION decrypt_sensitive_field(encrypted_text TEXT, encryption_key TEXT)
RETURNS TEXT AS $$
BEGIN
    -- In production, use proper decryption like pgcrypto
    -- This is a placeholder - implement proper decryption
    IF encrypted_text IS NULL OR encrypted_text = '' THEN
        RETURN NULL;
    END IF;
    
    -- This would use proper decryption in production
    -- RETURN pgp_sym_decrypt(encrypted_text::bytea, encryption_key);
    
    -- For now, just return placeholder
    RETURN 'DECRYPTED_DATA';
END;
$$ LANGUAGE plpgsql;

-- Create audit table for security events
CREATE TABLE IF NOT EXISTS security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    event_details JSONB,
    risk_level VARCHAR(20) DEFAULT 'LOW', -- LOW, MEDIUM, HIGH, CRITICAL
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for security audit log
CREATE INDEX IF NOT EXISTS idx_security_audit_log_event_type ON security_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_user_id ON security_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_created_at ON security_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_risk_level ON security_audit_log(risk_level);

-- Function to log security events
CREATE OR REPLACE FUNCTION log_security_event(
    p_event_type VARCHAR(50),
    p_user_id UUID DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_event_details JSONB DEFAULT NULL,
    p_risk_level VARCHAR(20) DEFAULT 'LOW'
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO security_audit_log (
        event_type,
        user_id,
        ip_address,
        user_agent,
        event_details,
        risk_level
    ) VALUES (
        p_event_type,
        p_user_id,
        p_ip_address,
        p_user_agent,
        p_event_details,
        p_risk_level
    );
END;
$$ LANGUAGE plpgsql;

-- Create function to validate password strength
CREATE OR REPLACE FUNCTION validate_password_strength(password TEXT)
RETURNS TABLE (
    is_valid BOOLEAN,
    strength_score INTEGER,
    feedback TEXT[]
) AS $$
DECLARE
    score INTEGER := 0;
    feedback_array TEXT[] := ARRAY[]::TEXT[];
BEGIN
    -- Length check
    IF LENGTH(password) >= 8 THEN
        score := score + 2;
    ELSE
        feedback_array := array_append(feedback_array, 'Password must be at least 8 characters long');
    END IF;
    
    -- Uppercase check
    IF password ~ '[A-Z]' THEN
        score := score + 1;
    ELSE
        feedback_array := array_append(feedback_array, 'Password must contain at least one uppercase letter');
    END IF;
    
    -- Lowercase check
    IF password ~ '[a-z]' THEN
        score := score + 1;
    ELSE
        feedback_array := array_append(feedback_array, 'Password must contain at least one lowercase letter');
    END IF;
    
    -- Number check
    IF password ~ '[0-9]' THEN
        score := score + 1;
    ELSE
        feedback_array := array_append(feedback_array, 'Password must contain at least one number');
    END IF;
    
    -- Special character check
    IF password ~ '[!@#$%^&*()_+\-=\[\]{};'':"\\|,.<>\?]' THEN
        score := score + 2;
    ELSE
        feedback_array := array_append(feedback_array, 'Password must contain at least one special character');
    END IF;
    
    -- Common password check (simplified)
    IF LOWER(password) IN ('password', '123456', 'password123', 'admin', 'letmein', 'welcome', 'monkey', '1234567890') THEN
        score := 0;
        feedback_array := array_append(feedback_array, 'Password is too common and easily guessed');
    END IF;
    
    RETURN QUERY SELECT 
        score >= 5 as is_valid,
        score as strength_score,
        feedback_array as feedback;
END;
$$ LANGUAGE plpgsql;

-- Create rate limiting table
CREATE TABLE IF NOT EXISTS rate_limiting (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier VARCHAR(255) NOT NULL, -- IP address, user ID, etc.
    action_type VARCHAR(50) NOT NULL, -- login_attempt, api_call, etc.
    attempt_count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    blocked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(identifier, action_type)
);

CREATE INDEX IF NOT EXISTS idx_rate_limiting_identifier_action ON rate_limiting(identifier, action_type);
CREATE INDEX IF NOT EXISTS idx_rate_limiting_blocked_until ON rate_limiting(blocked_until);

-- Function to check and update rate limits
CREATE OR REPLACE FUNCTION check_rate_limit(
    p_identifier VARCHAR(255),
    p_action_type VARCHAR(50),
    p_max_attempts INTEGER DEFAULT 5,
    p_window_minutes INTEGER DEFAULT 15
)
RETURNS TABLE (
    is_allowed BOOLEAN,
    attempts_remaining INTEGER,
    blocked_until_result TIMESTAMP WITH TIME ZONE,
    reset_time TIMESTAMP WITH TIME ZONE
) AS $$
DECLARE
    current_record RECORD;
    window_start_time TIMESTAMP WITH TIME ZONE;
    is_blocked BOOLEAN := FALSE;
BEGIN
    window_start_time := CURRENT_TIMESTAMP - INTERVAL '1 minute' * p_window_minutes;
    
    -- Get current rate limiting record
    SELECT * INTO current_record 
    FROM rate_limiting 
    WHERE identifier = p_identifier AND action_type = p_action_type;
    
    -- Check if currently blocked
    IF current_record.blocked_until IS NOT NULL AND current_record.blocked_until > CURRENT_TIMESTAMP THEN
        is_blocked := TRUE;
    END IF;
    
    -- If blocked, return blocked status
    IF is_blocked THEN
        RETURN QUERY SELECT 
            FALSE as is_allowed,
            0 as attempts_remaining,
            current_record.blocked_until as blocked_until_result,
            current_record.blocked_until as reset_time;
        RETURN;
    END IF;
    
    -- Reset counter if window has passed
    IF current_record.window_start IS NULL OR current_record.window_start < window_start_time THEN
        INSERT INTO rate_limiting (identifier, action_type, attempt_count, window_start)
        VALUES (p_identifier, p_action_type, 1, CURRENT_TIMESTAMP)
        ON CONFLICT (identifier, action_type) 
        DO UPDATE SET 
            attempt_count = 1,
            window_start = CURRENT_TIMESTAMP,
            blocked_until = NULL,
            updated_at = CURRENT_TIMESTAMP;
            
        RETURN QUERY SELECT 
            TRUE as is_allowed,
            p_max_attempts - 1 as attempts_remaining,
            NULL::TIMESTAMP WITH TIME ZONE as blocked_until_result,
            CURRENT_TIMESTAMP + INTERVAL '1 minute' * p_window_minutes as reset_time;
        RETURN;
    END IF;
    
    -- Increment attempt count
    UPDATE rate_limiting 
    SET attempt_count = attempt_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE identifier = p_identifier AND action_type = p_action_type;
    
    -- Check if limit exceeded
    IF current_record.attempt_count + 1 > p_max_attempts THEN
        -- Block the identifier
        UPDATE rate_limiting 
        SET blocked_until = CURRENT_TIMESTAMP + INTERVAL '1 minute' * p_window_minutes * 2,
            updated_at = CURRENT_TIMESTAMP
        WHERE identifier = p_identifier AND action_type = p_action_type;
        
        -- Log security event
        PERFORM log_security_event(
            'RATE_LIMIT_EXCEEDED',
            NULL,
            p_identifier::INET,
            NULL,
            jsonb_build_object(
                'action_type', p_action_type,
                'attempts', current_record.attempt_count + 1,
                'max_attempts', p_max_attempts
            ),
            'HIGH'
        );
        
        RETURN QUERY SELECT 
            FALSE as is_allowed,
            0 as attempts_remaining,
            CURRENT_TIMESTAMP + INTERVAL '1 minute' * p_window_minutes * 2 as blocked_until_result,
            CURRENT_TIMESTAMP + INTERVAL '1 minute' * p_window_minutes * 2 as reset_time;
        RETURN;
    END IF;
    
    -- Allow the request
    RETURN QUERY SELECT 
        TRUE as is_allowed,
        p_max_attempts - (current_record.attempt_count + 1) as attempts_remaining,
        NULL::TIMESTAMP WITH TIME ZONE as blocked_until_result,
        current_record.window_start + INTERVAL '1 minute' * p_window_minutes as reset_time;
END;
$$ LANGUAGE plpgsql;

-- Comments
COMMENT ON FUNCTION update_system_settings_from_env IS 'Template function for updating system settings from environment variables';
COMMENT ON FUNCTION verify_system_settings IS 'Checks if all required system settings are properly configured';
COMMENT ON FUNCTION validate_password_strength IS 'Validates password strength and provides feedback';
COMMENT ON FUNCTION check_rate_limit IS 'Implements rate limiting with configurable windows and attempt limits';
COMMENT ON TABLE security_audit_log IS 'Logs all security-related events for monitoring and analysis';
COMMENT ON TABLE rate_limiting IS 'Implements rate limiting for various actions to prevent abuse';