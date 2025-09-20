"""
JWT Authentication Middleware
FastAPI dependency for protecting routes with JWT authentication
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from database.connection import get_db
from .service import AuthenticationService

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security_scheme = HTTPBearer()

# Global auth service reference (will be set in main.py)
_auth_service: Optional[AuthenticationService] = None

def set_auth_service(service: AuthenticationService):
    """Set the authentication service instance"""
    global _auth_service
    _auth_service = service

def get_auth_service() -> AuthenticationService:
    """Get the authentication service instance"""
    if _auth_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not initialized"
        )
    return _auth_service

async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    FastAPI dependency that requires valid JWT authentication
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session
        
    Returns:
        Dict: User information if authentication successful
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Get authentication service
        auth_service = get_auth_service()
        
        # Extract token from credentials
        token = credentials.credentials
        
        # Validate token and get user
        user = await auth_service.get_user_by_token(db, token)
        
        if not user:
            logger.warning("Invalid or expired token used")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"Authenticated user: {user['email']}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Authentication middleware error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency for optional authentication
    Returns user info if valid token provided, None otherwise
    
    Args:
        credentials: Optional HTTP Bearer token
        db: Database session
        
    Returns:
        Optional[Dict]: User information if authenticated, None if not
    """
    if not credentials:
        return None
    
    try:
        auth_service = get_auth_service()
        user = await auth_service.get_user_by_token(db, credentials.credentials)
        return user
    except Exception as e:
        logger.debug(f"Optional auth failed: {e}")
        return None
