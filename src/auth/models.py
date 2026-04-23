"""
User model for authentication.

Simple user table with email and hashed password.
Using passlib for secure password hashing.
"""

from datetime import datetime, timezone

from passlib.context import CryptContext
from sqlalchemy import Column, Integer, String, DateTime

from src.database import Base


# Password hashing context - pbkdf2_sha256 has no password length limit
# and is NIST-approved, secure, and works out of the box
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def verify_password(self, plain_password: str) -> bool:
        """Check if provided password matches the hash."""
        return pwd_context.verify(plain_password, self.hashed_password)
    
    @staticmethod
    def hash_password(plain_password: str) -> str:
        """Hash a password for storage."""
        return pwd_context.hash(plain_password)

