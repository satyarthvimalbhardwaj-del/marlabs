"""Feature request model."""
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class FeatureRequestStatus(str, enum.Enum):
    """Feature request status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class FeatureRequest(Base):
    """
    Feature request model for user suggestions.

    Attributes:
        id: Primary key
        title: Request title
        description: Detailed description
        status: Request status
        priority: Priority rating (0-10)
        user_id: Foreign key to User
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "feature_requests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(FeatureRequestStatus), default=FeatureRequestStatus.PENDING, nullable=False, index=True)
    priority = Column(Integer, default=0, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="feature_requests")

    # Indexes
    __table_args__ = (
        Index('idx_feature_request_status_priority', 'status', 'priority'),
    )

    def __repr__(self):
        return f"<FeatureRequest(id={self.id}, title={self.title[:30]}, status={self.status})>"
