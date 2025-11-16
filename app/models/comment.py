"""Comment model for blog discussions."""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Comment(Base):
    """
    Comment model for real-time blog discussions.

    Attributes:
        id: Primary key
        content: Comment text
        blog_id: Foreign key to Blog
        user_id: Foreign key to User
        created_at: Creation timestamp
    """
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    blog_id = Column(Integer, ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    blog = relationship("Blog", back_populates="comments")
    user = relationship("User", back_populates="comments")

    # Indexes
    __table_args__ = (
        Index('idx_comment_blog_created', 'blog_id', 'created_at'),
    )

    def __repr__(self):
        return f"<Comment(id={self.id}, blog_id={self.blog_id}, user_id={self.user_id})>"
