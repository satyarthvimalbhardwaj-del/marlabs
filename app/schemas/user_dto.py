"""User Data Transfer Objects."""
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username contains only alphanumeric and underscore."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.USER

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    role: UserRole
    is_active: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data."""
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
