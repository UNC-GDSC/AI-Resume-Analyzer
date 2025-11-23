"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.models.user import User
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from loguru import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user

    Raises:
        HTTPException: If username or email already exists
    """
    # Check if user exists
    existing_user = (
        db.query(User)
        .filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"Registered new user: {user.username}")
    return user


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT tokens.

    Args:
        user_data: Login credentials
        db: Database session

    Returns:
        JWT access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user
    user = db.query(User).filter(User.username == user_data.username).first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    logger.info(f"User logged in: {user.username}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user information.

    Args:
        current_user: Current authenticated user data
        db: Database session

    Returns:
        User information

    Raises:
        HTTPException: If user not found
    """
    user_id = int(current_user["sub"])
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user
