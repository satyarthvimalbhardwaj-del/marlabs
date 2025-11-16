"""User model with role-based access control."""
import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    USER = "user"
    ADMIN = "admin"
    L1_APPROVER = "l1_approver"


class User(Base):
    """
    User model with authentication and authorization.

    Attributes:
        id: Primary key
        email: Unique email address
        username: Unique username
        hashed_password: Bcrypt hashed password
        role: User role for RBAC
        is_active: Account status (1=active, 0=inactive)
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    blogs = relationship("Blog", back_populates="author", foreign_keys="Blog.author_id", cascade="all, delete-orphan")
    approved_blogs = relationship("Blog", foreign_keys="Blog.approved_by")
    feature_requests = relationship("FeatureRequest", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
