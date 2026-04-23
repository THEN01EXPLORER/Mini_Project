"""
Pydantic schemas for authentication.

Request/response models for the auth endpoints.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Minimum 6 characters")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user info response (no password!)."""
    id: int
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # Enable ORM mode
