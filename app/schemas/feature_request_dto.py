"""Feature Request Data Transfer Objects."""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.models.feature_request import FeatureRequestStatus


class FeatureRequestBase(BaseModel):
    """Base feature request schema."""
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    priority: int = Field(default=0, ge=0, le=10)


class FeatureRequestCreate(FeatureRequestBase):
    """Schema for creating feature request."""
    pass


class FeatureRequestUpdate(BaseModel):
    """Schema for updating feature request."""
    status: Optional[FeatureRequestStatus] = None
    priority: Optional[int] = Field(None, ge=0, le=10)
    description: Optional[str] = Field(None, min_length=10)


class FeatureRequestResponse(FeatureRequestBase):
    """Schema for feature request response."""
    id: int
    status: FeatureRequestStatus
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FeatureRequestListResponse(BaseModel):
    """Schema for paginated feature request list."""
    total: int
    page: int
    page_size: int
    feature_requests: List[FeatureRequestResponse]
