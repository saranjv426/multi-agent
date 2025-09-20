"""
Authentication Service for Railway PostgreSQL
Handles user registration, login, password reset operations
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from email_validator import validate_email, EmailNotValidError
import logging

from database.models import User, PasswordResetToken
from .security import SecurityManager
from .email_service import EmailService

logger = logging.getLogger(__name__)

class AuthenticationService:
    """Main authentication service"""
    
    def __init__(self, security_manager: SecurityManager, email_service: EmailService):
        """Initialize authentication service"""
        self.security = security_manager
        self.email = email_service
    
    async def signup(self, db: Session, email: str, password: str) -> Dict[str, Any]:
        """Register a new user"""
        try:
            logger.info(f"🔐 Attempting user signup for: {email}")
            
            # Validate email format
            try:
                valid_email = validate_email(email)
                email = valid_email.email.lower()
            except EmailNotValidError as e:
                logger.warning(f"Invalid email format: {email}")
                return {
                    "success": False,
                    "error": "Invalid email format"
                }
            
            # Validate password strength
            if len(password) < 8:
                return {
                    "success": False,
                    "error": "Password must be at least 8 characters long"
                }
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                logger.warning(f"User already exists: {email}")
                return {
                    "success": False,
                    "error": "User with this email already exists"
                }
            
            # Hash password and create user
            password_hash = self.security.hash_password(password)
            
            new_user = User(
                email=email,
                password_hash=password_hash,
                is_active=True
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Generate access token
            token_data = {"sub": str(new_user.id), "email": new_user.email}
            access_token = self.security.create_access_token(token_data)
            
            logger.info(f"✅ User created successfully: {email}")
            
            return {
                "success": True,
                "user": {
                    "id": str(new_user.id),
                    "email": new_user.email,
                    "created_at": new_user.created_at.isoformat()
                },
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except IntegrityError:
            db.rollback()
            logger.warning(f"Integrity error during signup (duplicate email): {email}")
            return {
                "success": False,
                "error": "User with this email already exists"
            }
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Unexpected error during signup: {e}")
            return {
                "success": False,
                "error": "Registration failed. Please try again."
            }
    
    async def login(self, db: Session, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user login"""
        try:
            logger.info(f"🔑 Attempting user login for: {email}")
            
            # Normalize email
            email = email.lower().strip()
            
            # Find user by email
            user = db.query(User).filter(User.email == email).first()
            if not user:
                logger.warning(f"User not found: {email}")
                return {
                    "success": False,
                    "error": "Invalid email or password"
                }
            
            # Verify password
            if not self.security.verify_password(password, user.password_hash):
                logger.warning(f"Invalid password for user: {email}")
                return {
                    "success": False,
                    "error": "Invalid email or password"
                }
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Inactive user attempted login: {email}")
                return {
                    "success": False,
                    "error": "Account is deactivated"
                }
            
            # Generate access token
            token_data = {"sub": str(user.id), "email": user.email}
            access_token = self.security.create_access_token(token_data)
            
            logger.info(f"✅ User logged in successfully: {email}")
            
            return {
                "success": True,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "created_at": user.created_at.isoformat()
                },
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"❌ Error during login: {e}")
            return {
                "success": False,
                "error": "Login failed. Please try again."
            }
    
    async def forgot_password(self, db: Session, email: str, frontend_url: str) -> Dict[str, Any]:
        """Send password reset email"""
        try:
            logger.info(f"🔄 Password reset requested for: {email}")
            
            # Normalize email
            email = email.lower().strip()
            
            # Find user by email
            user = db.query(User).filter(User.email == email).first()
            if not user:
                # Don't reveal if email exists or not for security
                logger.warning(f"Password reset requested for non-existent user: {email}")
                return {
                    "success": True,
                    "message": "If this email exists, you will receive a reset link"
                }
            
            # Generate reset token
            reset_token = self.security.generate_reset_token()
            expires_at = datetime.utcnow() + timedelta(minutes=30)  # 30 minutes
            
            # Store reset token in database
            db_token = PasswordResetToken(
                user_id=user.id,
                token=reset_token,
                expires_at=expires_at,
                used=False
            )
            
            db.add(db_token)
            db.commit()
            
            # Send reset email
            reset_url = f"{frontend_url}/reset-password?token={reset_token}"
            await self.email.send_password_reset_email(user.email, reset_url)
            
            logger.info(f"✅ Password reset email sent to: {email}")
            
            return {
                "success": True,
                "message": "Password reset email sent"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error during password reset request: {e}")
            return {
                "success": False,
                "error": "Failed to send reset email. Please try again."
            }
    
    async def reset_password(self, db: Session, token: str, new_password: str) -> Dict[str, Any]:
        """Reset user password with token"""
        try:
            logger.info("🔄 Attempting password reset")
            
            # Validate new password
            if len(new_password) < 8:
                return {
                    "success": False,
                    "error": "Password must be at least 8 characters long"
                }
            
            # Find and validate reset token
            db_token = db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token,
                PasswordResetToken.used == False,
                PasswordResetToken.expires_at > datetime.utcnow()
            ).first()
            
            if not db_token:
                logger.warning("Invalid or expired reset token used")
                return {
                    "success": False,
                    "error": "Invalid or expired reset token"
                }
            
            # Find user
            user = db.query(User).filter(User.id == db_token.user_id).first()
            if not user:
                logger.error(f"User not found for reset token: {db_token.user_id}")
                return {
                    "success": False,
                    "error": "Invalid reset token"
                }
            
            # Update password
            user.password_hash = self.security.hash_password(new_password)
            
            # Mark token as used
            db_token.used = True
            
            db.commit()
            
            logger.info(f"✅ Password reset successfully for user: {user.email}")
            
            return {
                "success": True,
                "message": "Password reset successfully"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error during password reset: {e}")
            return {
                "success": False,
                "error": "Password reset failed. Please try again."
            }
    
    async def get_user_by_token(self, db: Session, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from JWT token"""
        try:
            # Verify token
            payload = self.security.verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # Find user in database
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                return None
            
            return {
                "id": str(user.id),
                "email": user.email,
                "created_at": user.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user by token: {e}")
            return None
