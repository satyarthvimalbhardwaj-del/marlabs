"""Blog Data Transfer Objects."""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List
from app.models.blog import BlogStatus
import json


class BlogBase(BaseModel):
    """Base blog schema."""
    title: str = Field(..., min_length=5, max_length=255)
    content: str = Field(..., min_length=10)
    images: Optional[List[str]] = None

    @field_validator('images')
    @classmethod
    def validate_images(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate image URLs."""
        if v:
            for url in v:
                if not url.startswith(('http://', 'https://')):
                    raise ValueError(f'Invalid image URL: {url}')
        return v


class BlogCreate(BlogBase):
    """Schema for creating a blog."""
    pass


class BlogUpdate(BaseModel):
    """Schema for updating a blog."""
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    content: Optional[str] = Field(None, min_length=10)
    images: Optional[List[str]] = None


class BlogResponse(BlogBase):
    """Schema for blog response."""
    id: int
    status: BlogStatus
    author_id: int
    approved_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BlogListResponse(BaseModel):
    """Schema for paginated blog list."""
    total: int
    page: int
    page_size: int
    blogs: List[BlogResponse]


class BlogApprovalRequest(BaseModel):
    """Schema for blog approval/rejection."""
    reason: Optional[str] = Field(None, max_length=500)
