"""Core utilities package."""
from app.core.security import verify_password, get_password_hash, decode_token
from app.core.permissions import require_role, is_admin, is_approver, check_ownership
from app.core.exceptions import (
    BaseAppException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    ConflictError,
    DatabaseError,
    ServiceUnavailableError
)

__all__ = [
    "verify_password",
    "get_password_hash",
    "decode_token",
    "require_role",
    "is_admin",
    "is_approver",
    "check_ownership",
    "BaseAppException",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "DatabaseError",
    "ServiceUnavailableError"
]
