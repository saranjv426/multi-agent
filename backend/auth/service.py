"""
Authentication Service for Railway PostgreSQL
Handles user registration, login, password reset operations
"""

from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from email_validator import validate_email, EmailNotValidError
import logging

from database.models import User
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
                valid_email = validate_email(email, check_deliverability=False)
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
            logger.error(f"❌ Error type: {type(e).__name__}")
            logger.error(f"❌ Error details: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Registration failed: {str(e)}"
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
            logger.error(f"❌ Error type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Login failed: {str(e)}"
            }
    
    async def forgot_password(self, db: Session, email: str, frontend_url: str) -> Dict[str, Any]:
        """Compatibility no-op for deprecated token-email flow."""
        try:
            return {
                "success": True,
                "message": "Deprecated endpoint"
            }
            
        except Exception as e:
            logger.error(f"❌ Error during deprecated forgot-password flow: {e}")
            return {
                "success": False,
                "error": "Forgot password flow failed"
            }
    
    async def reset_password(self, db: Session, email: str, new_password: str) -> Dict[str, Any]:
        """Reset user password with email + new password."""
        try:
            logger.info("🔄 Attempting password reset")
            
            # Validate new password
            if len(new_password) < 8:
                return {
                    "success": False,
                    "error": "Password must be at least 8 characters long"
                }
            
            email = email.lower().strip()

            # Find user by email
            user = db.query(User).filter(User.email == email).first()
            if not user:
                logger.warning(f"Password reset requested for unknown email: {email}")
                return {
                    "success": False,
                    "error": "User not found"
                }

            # Prevent resetting to the existing password
            if self.security.verify_password(new_password, user.password_hash):
                return {
                    "success": False,
                    "error": "New password must be different from current password"
                }
            
            # Update password
            user.password_hash = self.security.hash_password(new_password)
            
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

            try:
                normalized_user_id = UUID(str(user_id))
            except (TypeError, ValueError):
                logger.warning("Token subject is not a valid UUID: %s", user_id)
                return None
            
            # Find user in database
            user = db.query(User).filter(User.id == normalized_user_id).first()
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
