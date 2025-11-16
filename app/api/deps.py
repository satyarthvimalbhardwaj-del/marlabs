"""
API dependencies for authentication and authorization.
Provides reusable dependencies for FastAPI endpoints.
"""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.security import decode_token
from app.crud.user_crud import user_crud
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization header
        db: Database session

    Returns:
        Current user instance

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        logger.debug("Decoding authentication token")
        payload = decode_token(token)
        user_id: int = int(payload.get("sub"))

        if user_id is None:
            logger.warning("Token payload missing user_id")
            raise credentials_exception

        logger.debug(f"Token decoded successfully for user_id={user_id}")
    except JWTError as e:
        logger.warning(f"JWT error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {str(e)}", exc_info=True)
        raise credentials_exception

    user = await user_crud.get(db, user_id)
    if user is None:
        logger.warning(f"User not found: user_id={user_id}")
        raise credentials_exception

    logger.info(f"User authenticated: user_id={user.id}, email={user.email}")
    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure current user is active.

    Args:
        current_user: Current user from token

    Returns:
        Active user instance

    Raises:
        HTTPException: If user is inactive
    """
    if not await user_crud.is_active(current_user):
        logger.warning(f"Inactive user attempted access: user_id={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    logger.debug(f"Active user check passed: user_id={current_user.id}")
    return current_user


async def require_admin(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require admin role.

    Args:
        current_user: Current active user

    Returns:
        Admin user instance

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user attempted admin access: user_id={current_user.id}, role={current_user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    logger.debug(f"Admin check passed: user_id={current_user.id}")
    return current_user


async def require_approver(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require approver role (admin or L1 approver).

    Args:
        current_user: Current active user

    Returns:
        Approver user instance

    Raises:
        HTTPException: If user cannot approve
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.L1_APPROVER]:
        logger.warning(f"Non-approver attempted approver access: user_id={current_user.id}, role={current_user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approver access required. Must be admin or L1 approver."
        )

    logger.debug(f"Approver check passed: user_id={current_user.id}")
    return current_user
