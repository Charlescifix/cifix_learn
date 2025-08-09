/**
 * Email Service for CIFIX LEARN
 * Handles AWS SES integration for sending verification emails, notifications, etc.
 */

class EmailService {
    constructor() {
        // AWS SES Configuration (to be set from environment variables)
        this.config = {
            region: 'us-east-1', // or your preferred region
            accessKeyId: process.env.AWS_ACCESS_KEY_ID,
            secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
            sourceEmail: 'noreply@cifixlearn.com', // Your verified SES email
            apiVersion: '2010-12-01'
        };
        
        // Email templates
        this.templates = {
            verification: {
                subject: 'Verify Your CIFIX LEARN Account',
                html: this.getVerificationEmailTemplate(),
                text: this.getVerificationEmailText()
            },
            welcome: {
                subject: 'Welcome to CIFIX LEARN!',
                html: this.getWelcomeEmailTemplate(),
                text: this.getWelcomeEmailText()
            },
            passwordReset: {
                subject: 'Reset Your CIFIX LEARN Password',
                html: this.getPasswordResetTemplate(),
                text: this.getPasswordResetText()
            }
        };
    }

    /**
     * Initialize AWS SES client
     * In a real application, this would be done server-side
     */
    initializeAWS() {
        // This is pseudocode - actual implementation would be on the backend
        if (typeof AWS !== 'undefined') {
            AWS.config.update({
                region: this.config.region,
                accessKeyId: this.config.accessKeyId,
                secretAccessKey: this.config.secretAccessKey
            });
            
            this.ses = new AWS.SES({ apiVersion: this.config.apiVersion });
        }
    }

    /**
     * Send verification email with OTP code
     * @param {string} email - Recipient email address
     * @param {string} otpCode - 6-digit verification code
     * @param {string} studentName - Student's name
     * @returns {Promise} - SES send promise
     */
    async sendVerificationEmail(email, otpCode, studentName) {
        const params = {
            Destination: {
                ToAddresses: [email]
            },
            Message: {
                Body: {
                    Html: {
                        Charset: 'UTF-8',
                        Data: this.templates.verification.html
                            .replace('{{studentName}}', studentName)
                            .replace('{{otpCode}}', otpCode)
                            .replace('{{expiryTime}}', '10 minutes')
                    },
                    Text: {
                        Charset: 'UTF-8',
                        Data: this.templates.verification.text
                            .replace('{{studentName}}', studentName)
                            .replace('{{otpCode}}', otpCode)
                            .replace('{{expiryTime}}', '10 minutes')
                    }
                },
                Subject: {
                    Charset: 'UTF-8',
                    Data: this.templates.verification.subject
                }
            },
            Source: this.config.sourceEmail
        };

        try {
            // In frontend demo, we simulate the email sending
            console.log('📧 Simulating email send to:', email);
            console.log('📧 OTP Code:', otpCode);
            console.log('📧 Email content:', params.Message.Text.Data);
            
            // Simulate AWS SES response
            return Promise.resolve({
                MessageId: 'demo-' + Date.now(),
                success: true,
                message: 'Email sent successfully (demo mode)'
            });
            
            // Real implementation would be:
            // return this.ses.sendEmail(params).promise();
        } catch (error) {
            console.error('Email sending failed:', error);
            throw error;
        }
    }

    /**
     * Send welcome email after successful registration
     * @param {string} email - Recipient email address
     * @param {string} studentName - Student's name
     * @param {string} username - Login username
     * @returns {Promise} - SES send promise
     */
    async sendWelcomeEmail(email, studentName, username) {
        const params = {
            Destination: {
                ToAddresses: [email]
            },
            Message: {
                Body: {
                    Html: {
                        Charset: 'UTF-8',
                        Data: this.templates.welcome.html
                            .replace('{{studentName}}', studentName)
                            .replace('{{username}}', username)
                            .replace('{{loginUrl}}', 'https://cifixlearn.com/login')
                    },
                    Text: {
                        Charset: 'UTF-8',
                        Data: this.templates.welcome.text
                            .replace('{{studentName}}', studentName)
                            .replace('{{username}}', username)
                            .replace('{{loginUrl}}', 'https://cifixlearn.com/login')
                    }
                },
                Subject: {
                    Charset: 'UTF-8',
                    Data: this.templates.welcome.subject
                }
            },
            Source: this.config.sourceEmail
        };

        try {
            console.log('📧 Sending welcome email to:', email);
            return Promise.resolve({ MessageId: 'welcome-' + Date.now(), success: true });
        } catch (error) {
            console.error('Welcome email failed:', error);
            throw error;
        }
    }

    /**
     * Generate 6-digit OTP code
     * @returns {string} - 6-digit numeric code
     */
    generateOTP() {
        return Math.floor(100000 + Math.random() * 900000).toString();
    }

    /**
     * Verify OTP code
     * @param {string} enteredCode - Code entered by user
     * @param {string} sentCode - Code that was sent
     * @param {number} timestamp - When code was generated
     * @returns {boolean} - Is code valid
     */
    verifyOTP(enteredCode, sentCode, timestamp) {
        const now = Date.now();
        const expiryTime = 10 * 60 * 1000; // 10 minutes
        
        // Check if code has expired
        if (now - timestamp > expiryTime) {
            return { valid: false, reason: 'expired' };
        }
        
        // Check if code matches
        if (enteredCode === sentCode) {
            return { valid: true };
        }
        
        return { valid: false, reason: 'incorrect' };
    }

    // Email Templates

    getVerificationEmailTemplate() {
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #5B47B0, #00D9C0); padding: 20px; border-radius: 10px 10px 0 0; }
                .logo { color: white; font-size: 24px; font-weight: bold; text-align: center; }
                .content { background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .otp-code { background: #f0f9ff; border: 2px dashed #00D9C0; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; color: #5B47B0; margin: 20px 0; border-radius: 10px; }
                .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">CIFIX LEARN</div>
                </div>
                <div class="content">
                    <h2>Verify Your Email Address</h2>
                    <p>Hi {{studentName}},</p>
                    <p>Welcome to CIFIX LEARN! Please use the verification code below to complete your account setup:</p>
                    <div class="otp-code">{{otpCode}}</div>
                    <p><strong>This code will expire in {{expiryTime}}.</strong></p>
                    <p>If you didn't create an account with us, please ignore this email.</p>
                    <p>Happy coding!<br>The CIFIX LEARN Team</p>
                </div>
                <div class="footer">
                    <p>CIFIX LEARN - AI Coding Education for Kids | support@cifixlearn.com</p>
                </div>
            </div>
        </body>
        </html>`;
    }

    getVerificationEmailText() {
        return `
        CIFIX LEARN - Email Verification
        
        Hi {{studentName}},
        
        Welcome to CIFIX LEARN! Please use this verification code to complete your account setup:
        
        Verification Code: {{otpCode}}
        
        This code will expire in {{expiryTime}}.
        
        If you didn't create an account with us, please ignore this email.
        
        Happy coding!
        The CIFIX LEARN Team
        
        ---
        CIFIX LEARN - AI Coding Education for Kids
        support@cifixlearn.com
        `;
    }

    getWelcomeEmailTemplate() {
        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #5B47B0, #00D9C0); padding: 20px; border-radius: 10px 10px 0 0; }
                .logo { color: white; font-size: 24px; font-weight: bold; text-align: center; }
                .content { background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .cta-button { background: linear-gradient(135deg, #5B47B0, #00D9C0); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; display: inline-block; font-weight: bold; margin: 20px 0; }
                .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">CIFIX LEARN</div>
                </div>
                <div class="content">
                    <h2>🎉 Welcome to CIFIX LEARN!</h2>
                    <p>Hi {{studentName}},</p>
                    <p>Congratulations! Your account has been successfully created and you're now ready to start your AI coding journey with us.</p>
                    
                    <h3>Your Login Details:</h3>
                    <ul>
                        <li><strong>Username:</strong> {{username}}</li>
                        <li><strong>Login URL:</strong> <a href="{{loginUrl}}">{{loginUrl}}</a></li>
                    </ul>
                    
                    <h3>What's Next?</h3>
                    <ol>
                        <li>Log in to your student dashboard</li>
                        <li>Complete your learning profile</li>
                        <li>Start with our beginner-friendly AI fundamentals course</li>
                        <li>Join our community of young coders!</li>
                    </ol>
                    
                    <a href="{{loginUrl}}" class="cta-button">Start Learning Now!</a>
                    
                    <p>If you have any questions, our support team is here to help at support@cifixlearn.com</p>
                    
                    <p>Happy coding!<br>The CIFIX LEARN Team</p>
                </div>
                <div class="footer">
                    <p>CIFIX LEARN - AI Coding Education for Kids | support@cifixlearn.com</p>
                </div>
            </div>
        </body>
        </html>`;
    }

    getWelcomeEmailText() {
        return `
        CIFIX LEARN - Welcome!
        
        Hi {{studentName}},
        
        Congratulations! Your account has been successfully created and you're now ready to start your AI coding journey with us.
        
        Your Login Details:
        Username: {{username}}
        Login URL: {{loginUrl}}
        
        What's Next?
        1. Log in to your student dashboard
        2. Complete your learning profile
        3. Start with our beginner-friendly AI fundamentals course
        4. Join our community of young coders!
        
        Visit {{loginUrl}} to start learning now!
        
        If you have any questions, our support team is here to help at support@cifixlearn.com
        
        Happy coding!
        The CIFIX LEARN Team
        
        ---
        CIFIX LEARN - AI Coding Education for Kids
        support@cifixlearn.com
        `;
    }

    getPasswordResetTemplate() {
        // Password reset template implementation
        return '<!-- Password reset template would go here -->';
    }

    getPasswordResetText() {
        return 'Password reset text would go here';
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EmailService;
} else {
    window.EmailService = EmailService;
}

// Usage example:
/*
const emailService = new EmailService();

// Send verification email
emailService.sendVerificationEmail('student@example.com', '123456', 'John Doe')
    .then(result => console.log('Email sent:', result))
    .catch(error => console.error('Email failed:', error));

// Generate OTP
const otpCode = emailService.generateOTP();

// Verify OTP
const isValid = emailService.verifyOTP('123456', otpCode, Date.now());
*/