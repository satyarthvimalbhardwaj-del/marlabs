"""Comment Data Transfer Objects."""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List


class CommentBase(BaseModel):
    """Base comment schema."""
    content: str = Field(..., min_length=1, max_length=1000)


class CommentCreate(CommentBase):
    """Schema for creating comment."""
    blog_id: int


class CommentResponse(CommentBase):
    """Schema for comment response."""
    id: int
    blog_id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
