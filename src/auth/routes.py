"""
Authentication routes.

Endpoints for user registration, login, and profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.auth.models import User
from src.auth.schemas import UserCreate, UserLogin, Token, UserResponse
from src.auth.jwt import create_access_token
from src.auth.dependencies import get_current_user


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - **email**: Valid email address (must be unique)
    - **password**: Minimum 6 characters
    """
    try:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = User.hash_password(user_data.password)
        new_user = User(email=user_data.email, hashed_password=hashed_password)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Registration error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login and get JWT token.
    
    Returns access token that must be included in Authorization header
    for protected endpoints.
    """
    # Find user
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not user.verify_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token
    access_token = create_access_token(data={"sub": user.email})
    
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user info.
    
    Requires valid JWT token in Authorization header.
    """
    return current_user
