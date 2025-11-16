"""
Role-based access control utilities.
Provides decorators and functions for permission checking.
"""
import logging
from fastapi import HTTPException, status
from app.models.user import UserRole, User

logger = logging.getLogger(__name__)


def require_role(*roles: UserRole):
    """
    Decorator for role-based access control.

    Args:
        roles: Allowed roles

    Returns:
        Decorator function
    """

    def decorator(func):
        async def wrapper(*args, current_user: User, **kwargs):
            logger.debug(f"Checking role permission for user_id={current_user.id}, role={current_user.role}")

            if current_user.role not in roles:
                logger.warning(
                    f"Permission denied for user_id={current_user.id}, required_roles={[r.value for r in roles]}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {[r.value for r in roles]}"
                )

            logger.debug(f"Permission granted for user_id={current_user.id}")
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def is_admin(user: User) -> bool:
    """
    Check if user is admin.

    Args:
        user: User instance

    Returns:
        True if user is admin
    """
    result = user.role == UserRole.ADMIN
    logger.debug(f"Admin check for user_id={user.id}: {result}")
    return result


def is_approver(user: User) -> bool:
    """
    Check if user can approve blogs.

    Args:
        user: User instance

    Returns:
        True if user is admin or L1 approver
    """
    result = user.role in [UserRole.ADMIN, UserRole.L1_APPROVER]
    logger.debug(f"Approver check for user_id={user.id}: {result}")
    return result


def check_ownership(user: User, resource_owner_id: int) -> bool:
    """
    Check if user owns a resource.

    Args:
        user: User instance
        resource_owner_id: Owner ID of the resource

    Returns:
        True if user owns the resource or is admin
    """
    result = user.id == resource_owner_id or is_admin(user)
    logger.debug(f"Ownership check for user_id={user.id}, resource_owner={resource_owner_id}: {result}")
    return result
