"""
JWT token utilities.

Handles token creation and validation.
Using python-jose for JWT operations.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from src.core.config import get_settings


# JWT Configuration
SECRET_KEY = "your-super-secret-key-change-in-production-12345"  # TODO: Move to .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data (usually {"sub": user_email})
        expires_delta: Optional custom expiry time
        
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT string to decode
        
    Returns:
        Decoded payload dict, or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
