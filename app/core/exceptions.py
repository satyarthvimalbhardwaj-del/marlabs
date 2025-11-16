"""
Custom exception classes with detailed error handling.
Provides domain-specific exceptions for better error management.
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class BaseAppException(Exception):
    """Base exception class for application-specific errors."""

    def __init__(
            self,
            message: str,
            status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
            details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(BaseAppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(BaseAppException):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ValidationError(BaseAppException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class NotFoundError(BaseAppException):
    """Raised when requested resource is not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ConflictError(BaseAppException):
    """Raised when resource conflict occurs."""

    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class DatabaseError(BaseAppException):
    """Raised when database operation fails."""

    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ServiceUnavailableError(BaseAppException):
    """Raised when external service is unavailable."""

    def __init__(self, message: str = "Service temporarily unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


def exception_to_http(exception: BaseAppException) -> HTTPException:
    """
    Convert application exception to FastAPI HTTPException.

    Args:
        exception: Application exception

    Returns:
        HTTPException with proper status code and detail
    """
    return HTTPException(
        status_code=exception.status_code,
        detail={
            "message": exception.message,
            "details": exception.details
        }
    )
