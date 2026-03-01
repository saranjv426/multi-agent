"""
Authentication Routes for FastAPI
RESTful endpoints for user authentication operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import logging

from database.connection import get_db
from .service import AuthenticationService
from .security import SecurityManager
from .email_service import EmailService

logger = logging.getLogger(__name__)

# Request/Response models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str

class AuthResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = None

# Security setup
security_scheme = HTTPBearer()

# Router setup
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Initialize services (will be done in main.py with proper config)
auth_service: Optional[AuthenticationService] = None

def get_auth_service() -> AuthenticationService:
    """Get authentication service instance"""
    if auth_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not initialized"
        )
    return auth_service

def init_auth_service(secret_key: str, frontend_url: str) -> AuthenticationService:
    """Initialize authentication service with configuration"""
    global auth_service
    
    if auth_service is None:
        security_manager = SecurityManager(secret_key)
        email_service = EmailService()
        auth_service = AuthenticationService(security_manager, email_service)
        logger.info("Authentication service initialized")
    
    return auth_service

@router.post("/signup", response_model=AuthResponse)
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
    service: AuthenticationService = Depends(get_auth_service)
):
    """
    Register a new user account
    
    Args:
        request: User signup information (email, password)
        
    Returns:
        AuthResponse: User data and access token if successful
    """
    try:
        logger.info(f"📝 Signup attempt for: {request.email}")
        
        result = await service.signup(db, request.email, request.password)
        
        if result["success"]:
            return AuthResponse(
                success=True,
                message="Account created successfully",
                user=result["user"],
                access_token=result["access_token"],
                token_type=result["token_type"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    service: AuthenticationService = Depends(get_auth_service)
):
    """
    Authenticate user login
    
    Args:
        request: User login credentials (email, password)
        
    Returns:
        AuthResponse: User data and access token if successful
    """
    try:
        logger.info(f"🔑 Login attempt for: {request.email}")
        
        result = await service.login(db, request.email, request.password)
        
        if result["success"]:
            return AuthResponse(
                success=True,
                message="Login successful",
                user=result["user"],
                access_token=result["access_token"],
                token_type=result["token_type"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )

@router.post("/forgot-password", response_model=AuthResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    service: AuthenticationService = Depends(get_auth_service)
):
    """
    Deprecated endpoint retained for compatibility.
    
    Args:
        request: Email address
        
    Returns:
        AuthResponse: Generic guidance message
    """
    try:
        logger.info(f"🔄 Password reset request (compat) for: {request.email}")
        await service.forgot_password(db, request.email, "")
        
        return AuthResponse(
            success=True,
            message="Use email and new password in reset password form"
        )
        
    except Exception as e:
        logger.error(f"❌ Forgot password error: {e}")
        return AuthResponse(
            success=True,
            message="Use email and new password in reset password form"
        )

@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
    service: AuthenticationService = Depends(get_auth_service)
):
    """
    Reset password using email + new password
    
    Args:
        request: Email and new password
        
    Returns:
        AuthResponse: Success message if password reset successfully
    """
    try:
        logger.info("🔄 Password reset attempt")
        
        result = await service.reset_password(db, request.email, request.new_password)
        
        if result["success"]:
            return AuthResponse(
                success=True,
                message="Password reset successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed. Please try again."
        )

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
    service: AuthenticationService = Depends(get_auth_service)
):
    """
    Get current user information from token
    
    Returns:
        Dict: Current user information
    """
    try:
        user = await service.get_user_by_token(db, credentials.credentials)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {"user": user}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )
