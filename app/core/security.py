"""
Security utilities for password hashing and JWT handling.
Provides cryptographic functions for authentication.
"""
import logging
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if passwords match
    """
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"Password verification result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}", exc_info=True)
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    try:
        hashed = pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}", exc_info=True)
        raise


def decode_token(token: str) -> dict:
    """
    Decode and verify JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        logger.debug("Token decoded successfully")
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {str(e)}", exc_info=True)
        raise JWTError(f"Token decode failed: {str(e)}")
