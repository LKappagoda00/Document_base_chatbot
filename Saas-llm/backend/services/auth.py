"""
Authentication service for JWT token management and user authentication.
Multi-tenant ready for SaaS architecture.
"""

import warnings
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from models.database import User
from config.settings import settings

# Suppress bcrypt version warnings
warnings.filterwarnings("ignore", message=".*bcrypt.*version.*")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management and JWT tokens."""
    
    def __init__(self):
        self.user_model = User()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            print(f"Password verification error: {e}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Get password hash."""
        try:
            # Bcrypt has a 72-byte limit, truncate if necessary
            if len(password.encode('utf-8')) > 72:
                password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
            return pwd_context.hash(password)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Password hashing failed: {str(e)}"
            )
    
    def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user with email and password."""
        user = self.user_model.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user["password_hash"]):
            return None
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.jwt_secret_key, 
            algorithm=settings.jwt_algorithm
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(
                token, 
                settings.jwt_secret_key, 
                algorithms=[settings.jwt_algorithm]
            )
            user_id: int = payload.get("sub")
            if user_id is None:
                return None
            return payload
        except JWTError:
            return None
    
    def get_current_user(self, token: str) -> dict:
        """Get current user from JWT token."""
        payload = self.verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        user = self.user_model.get_user_by_id(int(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    def register_user(self, email: str, password: str, full_name: str = None) -> dict:
        """Register a new user."""
        # Validate password length (bcrypt limit is 72 bytes)
        if len(password.encode('utf-8')) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is too long. Maximum length is 72 bytes."
            )
        
        # Check if user already exists
        existing_user = self.user_model.get_user_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = self.get_password_hash(password)
        user_id = self.user_model.create_user(email, hashed_password, full_name)
        
        # Get created user
        user = self.user_model.get_user_by_id(user_id)
        return user


# Global auth service instance
auth_service = AuthService()