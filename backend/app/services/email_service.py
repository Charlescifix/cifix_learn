"""
Email service for CIFIX LEARN using AWS SES
Simple, secure email notifications
"""
import boto3
from botocore.exceptions import ClientError
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails via AWS SES"""
    
    def __init__(self):
        self.ses_client = boto3.client(
            'ses',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
    
    async def send_verification_email(
        self, 
        to_email: str, 
        verification_token: str, 
        user_name: str
    ) -> bool:
        """Send email verification email"""
        
        verification_url = f"{settings.APP_URL}/verify-email/{verification_token}"
        
        html_content = self._get_verification_email_template(
            user_name, 
            verification_url
        )
        
        text_content = f"""
        Welcome to CIFIX LEARN, {user_name}!
        
        Please verify your email address by clicking the link below:
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account with CIFIX LEARN, please ignore this email.
        
        Best regards,
        The CIFIX LEARN Team
        """
        
        return await self._send_email(
            to_email=to_email,
            subject="Welcome to CIFIX LEARN - Please verify your email",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_welcome_email(
        self, 
        to_email: str, 
        user_name: str, 
        student_name: str
    ) -> bool:
        """Send welcome email after verification"""
        
        html_content = self._get_welcome_email_template(user_name, student_name)
        
        text_content = f"""
        Welcome to CIFIX LEARN, {user_name}!
        
        Your account has been successfully verified. {student_name} is now ready to start their AI learning journey!
        
        What's Next:
        1. Complete the AI Pathway Assessment to find the perfect learning path
        2. Explore personalized learning modules
        3. Track progress and earn achievements
        4. Build amazing projects
        
        Get started at: {settings.APP_URL}
        
        If you need help, contact us at {settings.SES_REPLY_TO_EMAIL}
        
        Best regards,
        The CIFIX LEARN Team
        """
        
        return await self._send_email(
            to_email=to_email,
            subject=f"Welcome to CIFIX LEARN - {student_name} is ready to start!",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_assessment_complete_email(
        self, 
        to_email: str, 
        user_name: str, 
        student_name: str, 
        recommended_path: str
    ) -> bool:
        """Send email when assessment is completed"""
        
        html_content = self._get_assessment_complete_template(
            user_name, 
            student_name, 
            recommended_path
        )
        
        text_content = f"""
        Great news, {user_name}!
        
        {student_name} has completed their AI Pathway Assessment and we've found the perfect learning path!
        
        Recommended Learning Path: {recommended_path}
        
        This path has been carefully selected based on {student_name}'s interests, learning style, and goals. They can now start their personalized learning journey with modules designed specifically for their success.
        
        View Progress: {settings.APP_URL}/dashboard
        
        Best regards,
        The CIFIX LEARN Team
        """
        
        return await self._send_email(
            to_email=to_email,
            subject=f"🎯 {student_name}'s Perfect Learning Path: {recommended_path}",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_progress_update_email(
        self, 
        to_email: str, 
        user_name: str, 
        student_name: str, 
        module_completed: str,
        total_progress: int
    ) -> bool:
        """Send progress update email"""
        
        html_content = self._get_progress_update_template(
            user_name, 
            student_name, 
            module_completed,
            total_progress
        )
        
        text_content = f"""
        Congratulations, {user_name}!
        
        {student_name} just completed "{module_completed}" and is making excellent progress!
        
        Learning Path Progress: {total_progress}%
        
        Keep up the great work! Each completed module brings {student_name} closer to mastering their chosen field.
        
        View Full Progress: {settings.APP_URL}/dashboard
        
        Best regards,
        The CIFIX LEARN Team
        """
        
        return await self._send_email(
            to_email=to_email,
            subject=f"🏆 {student_name} completed {module_completed}!",
            html_content=html_content,
            text_content=text_content
        )
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        configuration_set: Optional[str] = None
    ) -> bool:
        """Send email via AWS SES"""
        
        try:
            # Prepare email parameters
            email_params = {
                'Source': settings.SES_SOURCE_EMAIL,
                'Destination': {
                    'ToAddresses': [to_email]
                },
                'Message': {
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': text_content,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': html_content,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            }
            
            # Add reply-to if configured
            if settings.SES_REPLY_TO_EMAIL:
                email_params['ReplyToAddresses'] = [settings.SES_REPLY_TO_EMAIL]
            
            # Add configuration set if provided
            if configuration_set or settings.SES_CONFIGURATION_SET:
                email_params['ConfigurationSetName'] = configuration_set or settings.SES_CONFIGURATION_SET
            
            # Send email
            response = self.ses_client.send_email(**email_params)
            
            logger.info(f"Email sent successfully to {to_email}. MessageId: {response['MessageId']}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to send email to {to_email}. Error: {error_code} - {error_message}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {str(e)}")
            return False
    
    def _get_verification_email_template(self, user_name: str, verification_url: str) -> str:
        """Get HTML template for verification email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your CIFIX LEARN Account</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #5B47B0, #00D9C0); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">Welcome to CIFIX LEARN! 🚀</h1>
                <p style="margin: 10px 0 0; font-size: 16px;">AI-Powered Learning for Young Minds</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
                <h2 style="color: #5B47B0; margin-top: 0;">Hi {user_name}! 👋</h2>
                
                <p>Thank you for joining CIFIX LEARN! We're excited to help your child discover their perfect programming path through AI-powered assessments.</p>
                
                <p>To get started, please verify your email address by clicking the button below:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" style="background: linear-gradient(135deg, #5B47B0, #00D9C0); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                        ✅ Verify Email Address
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    If the button doesn't work, copy and paste this link into your browser:<br>
                    <a href="{verification_url}" style="color: #5B47B0; word-break: break-all;">{verification_url}</a>
                </p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #5B47B0; margin-top: 0;">What's Next? 🎯</h3>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>Complete the 3-minute AI Pathway Assessment</li>
                        <li>Get personalized learning path recommendations</li>
                        <li>Start learning with interactive modules</li>
                        <li>Track progress and earn achievements</li>
                    </ul>
                </div>
                
                <p style="font-size: 14px; color: #666; border-top: 1px solid #eee; padding-top: 20px; margin-top: 30px;">
                    This verification link expires in 24 hours. If you didn't create a CIFIX LEARN account, please ignore this email.
                </p>
                
                <p style="color: #5B47B0; font-weight: bold;">
                    Happy Learning!<br>
                    The CIFIX LEARN Team
                </p>
            </div>
        </body>
        </html>
        """
    
    def _get_welcome_email_template(self, user_name: str, student_name: str) -> str:
        """Get HTML template for welcome email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to CIFIX LEARN</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #5B47B0, #00D9C0); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">Account Verified! 🎉</h1>
                <p style="margin: 10px 0 0; font-size: 16px;">{student_name} is ready to start learning!</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
                <h2 style="color: #5B47B0; margin-top: 0;">Welcome aboard, {user_name}! 🚀</h2>
                
                <p>Your email has been verified and {student_name}'s learning journey with CIFIX LEARN can now begin!</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #5B47B0; margin-top: 0;">Next Steps for {student_name} 📚</h3>
                    <ol style="margin: 0; padding-left: 20px;">
                        <li><strong>Take the AI Assessment</strong> - 3-minute quiz to find the perfect learning path</li>
                        <li><strong>Explore Learning Modules</strong> - Interactive lessons tailored to their interests</li>
                        <li><strong>Build Projects</strong> - Hands-on coding projects to apply new skills</li>
                        <li><strong>Earn Achievements</strong> - Unlock badges and track progress</li>
                    </ol>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.APP_URL}/dashboard" style="background: linear-gradient(135deg, #5B47B0, #00D9C0); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                        🎯 Start Learning Journey
                    </a>
                </div>
                
                <div style="background: linear-gradient(135deg, #FFD93D, #FF8C42); color: #333; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">🔥 Summer Classes Available!</h3>
                    <p style="margin: 0;">Join our intensive summer coding bootcamp designed specifically for young learners aged 5-18!</p>
                </div>
                
                <p style="color: #5B47B0; font-weight: bold;">
                    We're here to help {student_name} succeed!<br>
                    The CIFIX LEARN Team
                </p>
                
                <p style="font-size: 14px; color: #666; border-top: 1px solid #eee; padding-top: 20px; margin-top: 30px;">
                    Questions? Reply to this email or visit our help center at {settings.APP_URL}/help
                </p>
            </div>
        </body>
        </html>
        """
    
    def _get_assessment_complete_template(
        self, 
        user_name: str, 
        student_name: str, 
        recommended_path: str
    ) -> str:
        """Get HTML template for assessment completion"""
        
        path_emojis = {
            "Game Development": "🎮",
            "AI & Machine Learning": "🤖", 
            "Web Development": "🌐",
            "Robotics": "🤖",
            "Data Science": "📊",
            "Mobile App Development": "📱",
            "General Programming": "💻"
        }
        
        emoji = path_emojis.get(recommended_path, "💻")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Assessment Complete - Perfect Learning Path Found!</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #00D9C0, #10B981); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">Perfect Match Found! 🎯</h1>
                <p style="margin: 10px 0 0; font-size: 16px;">AI Assessment Complete</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
                <h2 style="color: #5B47B0; margin-top: 0;">Great news, {user_name}! 🎉</h2>
                
                <p>{student_name} has completed the AI Pathway Assessment and we've found their perfect learning path!</p>
                
                <div style="background: linear-gradient(135deg, #5B47B0, #00D9C0); color: white; padding: 25px; border-radius: 15px; text-align: center; margin: 25px 0;">
                    <h2 style="margin: 0; font-size: 24px;">{emoji} {recommended_path}</h2>
                    <p style="margin: 10px 0 0; opacity: 0.9;">Recommended Learning Path for {student_name}</p>
                </div>
                
                <p>This path has been carefully selected based on {student_name}'s:</p>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Learning style and preferences</li>
                    <li>Interests and passions</li>
                    <li>Problem-solving approach</li>
                    <li>Creative thinking patterns</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.APP_URL}/learning-modules" style="background: linear-gradient(135deg, #5B47B0, #00D9C0); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                        🚀 Start Learning Modules
                    </a>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #5B47B0; margin-top: 0;">What's Included in {recommended_path}? 📚</h3>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>6 interactive learning modules</li>
                        <li>Hands-on coding projects</li>
                        <li>Progressive skill building</li>
                        <li>Achievement badges and rewards</li>
                        <li>Real-time progress tracking</li>
                    </ul>
                </div>
                
                <p style="color: #5B47B0; font-weight: bold;">
                    Let's build something amazing!<br>
                    The CIFIX LEARN Team
                </p>
            </div>
        </body>
        </html>
        """
    
    def _get_progress_update_template(
        self, 
        user_name: str, 
        student_name: str, 
        module_completed: str,
        total_progress: int
    ) -> str:
        """Get HTML template for progress updates"""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Module Completed - Great Progress!</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #10B981, #00D9C0); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">Module Completed! 🏆</h1>
                <p style="margin: 10px 0 0; font-size: 16px;">Excellent Progress by {student_name}</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
                <h2 style="color: #5B47B0; margin-top: 0;">Congratulations, {user_name}! 🎉</h2>
                
                <p>{student_name} just completed <strong>"{module_completed}"</strong> and is making excellent progress in their learning journey!</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 25px 0;">
                    <h3 style="color: #5B47B0; margin-top: 0; text-align: center;">Learning Path Progress</h3>
                    
                    <div style="background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden;">
                        <div style="background: linear-gradient(135deg, #5B47B0, #00D9C0); height: 100%; width: {total_progress}%; transition: width 0.3s ease;"></div>
                    </div>
                    
                    <p style="text-align: center; margin: 10px 0 0; font-size: 18px; font-weight: bold; color: #5B47B0;">{total_progress}% Complete</p>
                </div>
                
                <p>Each completed module brings {student_name} closer to mastering their chosen field. Keep up the fantastic work!</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.APP_URL}/dashboard" style="background: linear-gradient(135deg, #5B47B0, #00D9C0); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                        📊 View Full Progress
                    </a>
                </div>
                
                <div style="background: linear-gradient(135deg, #FFD93D, #FF8C42); color: #333; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">🔥 Keep the momentum going!</h3>
                    <p style="margin: 0;">The next module is ready and waiting. Continue the learning adventure!</p>
                </div>
                
                <p style="color: #5B47B0; font-weight: bold;">
                    Proud of {student_name}'s progress!<br>
                    The CIFIX LEARN Team
                </p>
            </div>
        </body>
        </html>
        """