"""Blog model with approval workflow."""
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class BlogStatus(str, enum.Enum):
    """Blog approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Blog(Base):
    """
    Blog article model with markdown content and approval workflow.

    Attributes:
        id: Primary key
        title: Blog title
        content: Markdown content
        images: JSON array of image URLs
        status: Approval status
        author_id: Foreign key to User
        approved_by: Foreign key to approver User
        created_at: Creation timestamp
        updated_at: Last update timestamp
        approved_at: Approval timestamp
    """
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    images = Column(Text, nullable=True)  # JSON string
    status = Column(SQLEnum(BlogStatus), default=BlogStatus.PENDING, nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    author = relationship("User", back_populates="blogs", foreign_keys=[author_id])
    approver = relationship("User", foreign_keys=[approved_by])
    comments = relationship("Comment", back_populates="blog", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_blog_status_created', 'status', 'created_at'),
        Index('idx_blog_author_status', 'author_id', 'status'),
    )

    def __repr__(self):
        return f"<Blog(id={self.id}, title={self.title[:30]}, status={self.status})>"
