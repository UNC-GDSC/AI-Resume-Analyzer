"""User schemas."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """User login schema."""

    username: str
    password: str


class UserResponse(UserBase):
    """User response schema."""

    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""

    username: Optional[str] = None
