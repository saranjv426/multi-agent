"""
Email Service for Password Reset
Handles sending password reset emails using Resend
"""

import os
from typing import Optional
import logging
import asyncio
from datetime import datetime

# Import resend with fallback for development
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logging.warning("Resend not available - email functionality will be mocked")

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for authentication-related emails"""
    
    def __init__(self, api_key: Optional[str] = None, from_email: Optional[str] = None):
        """Initialize email service"""
        self.api_key = api_key or os.getenv("RESEND_API_KEY")
        self.from_email = from_email or os.getenv("FROM_EMAIL", "noreply@yourdomain.com")
        
        if RESEND_AVAILABLE and self.api_key:
            resend.api_key = self.api_key
            self.enabled = True
            logger.info("Email service initialized with Resend")
        else:
            self.enabled = False
            logger.warning("Email service disabled - no API key or Resend not available")
    
    async def send_password_reset_email(self, to_email: str, reset_url: str) -> bool:
        """Send password reset email"""
        try:
            if not self.enabled:
                # Mock email sending for development
                logger.info(f"📧 [MOCK] Password reset email would be sent to: {to_email}")
                logger.info(f"📧 [MOCK] Reset URL: {reset_url}")
                return True
            
            # Email template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Password Reset</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; }}
                    .content {{ padding: 20px; }}
                    .button {{ display: inline-block; background: #007bff; color: white; padding: 12px 24px; 
                             text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                    .footer {{ font-size: 12px; color: #666; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Reset Your Password</h1>
                    </div>
                    <div class="content">
                        <p>Hello,</p>
                        <p>You requested a password reset for your Roof Design Validation account.</p>
                        <p>Click the button below to reset your password:</p>
                        <a href="{reset_url}" class="button">Reset Password</a>
                        <p>If the button doesn't work, copy and paste this link into your browser:</p>
                        <p><a href="{reset_url}">{reset_url}</a></p>
                        <p>This link will expire in 30 minutes for security reasons.</p>
                        <p>If you didn't request this reset, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>Roof Design Validation System<br>
                        This is an automated email, please do not reply.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Text version
            text_content = f"""
            Reset Your Password
            
            Hello,
            
            You requested a password reset for your Roof Design Validation account.
            
            Click this link to reset your password:
            {reset_url}
            
            This link will expire in 30 minutes for security reasons.
            
            If you didn't request this reset, please ignore this email.
            
            Roof Design Validation System
            """
            
            # Send email using Resend
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": "Reset Your Password - Roof Design Validation",
                "html": html_content,
                "text": text_content,
            }
            
            email = resend.Emails.send(params)
            
            logger.info(f"📧 Password reset email sent successfully to: {to_email}")
            logger.info(f"📧 Email ID: {email.get('id', 'unknown')}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send password reset email to {to_email}: {e}")
            return False
    
    async def send_welcome_email(self, to_email: str) -> bool:
        """Send welcome email to new users (optional)"""
        try:
            if not self.enabled:
                logger.info(f"📧 [MOCK] Welcome email would be sent to: {to_email}")
                return True
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Welcome to Roof Design Validation</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #28a745; color: white; padding: 20px; text-align: center; border-radius: 8px; }}
                    .content {{ padding: 20px; }}
                    .footer {{ font-size: 12px; color: #666; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome!</h1>
                    </div>
                    <div class="content">
                        <p>Hello,</p>
                        <p>Welcome to the Roof Design Validation System!</p>
                        <p>Your account has been created successfully. You can now start validating roof designs with our AI-powered system.</p>
                        <p>If you have any questions, feel free to reach out to our support team.</p>
                        <p>Happy validating!</p>
                    </div>
                    <div class="footer">
                        <p>Roof Design Validation System<br>
                        This is an automated email, please do not reply.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": "Welcome to Roof Design Validation",
                "html": html_content,
            }
            
            email = resend.Emails.send(params)
            
            logger.info(f"📧 Welcome email sent successfully to: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send welcome email to {to_email}: {e}")
            return False
