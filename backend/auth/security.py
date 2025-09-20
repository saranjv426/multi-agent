"""
Security utilities for JWT and password handling
Handles token generation, validation, and password hashing
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
import secrets
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    """Handles JWT tokens and password security"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """Initialize security manager"""
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Token expiration times
        self.access_token_expire_minutes = 30 * 24 * 60  # 30 days
        self.reset_token_expire_minutes = 30  # 30 minutes
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Access token created for user: {data.get('sub', 'unknown')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            return None
    
    def generate_reset_token(self) -> str:
        """Generate a secure random token for password reset"""
        return secrets.token_urlsafe(32)
    
    def create_reset_token_data(self, user_id: str) -> Dict[str, Any]:
        """Create data structure for password reset token"""
        return {
            "user_id": user_id,
            "type": "password_reset",
            "issued_at": datetime.utcnow().isoformat()
        }
