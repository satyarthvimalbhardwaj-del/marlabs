"""
Authentication API endpoints.
Handles user registration and login.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user_dto import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import auth_service
from app.core.exceptions import AuthenticationError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
        user_in: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.

    - **email**: Valid email address (unique)
    - **username**: Unique username (3-50 characters, alphanumeric)
    - **password**: Strong password (min 8 chars, must include uppercase, lowercase, and digit)
    - **role**: User role (default: user)

    Returns the created user object without password.
    """
    logger.info(f"Registration attempt for email: {user_in.email}")

    try:
        user = await auth_service.register_user(db, user_in)
        logger.info(f"User registered successfully: user_id={user.id}, email={user.email}")
        return user
    except ValidationError as e:
        logger.warning(f"Registration validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later."
        )


@router.post("/login", response_model=TokenResponse)
async def login(
        credentials: UserLogin,
        db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.

    - **email**: User email
    - **password**: User password

    Returns:
    - **access_token**: Short-lived token for API access (30 minutes)
    - **refresh_token**: Long-lived token for token refresh (7 days)
    - **token_type**: Bearer

    Use the access_token in the Authorization header as: `Bearer <access_token>`
    """
    logger.info(f"Login attempt for email: {credentials.email}")

    try:
        tokens = await auth_service.authenticate_user(db, credentials)
        logger.info(f"User logged in successfully: {credentials.email}")
        return tokens
    except AuthenticationError as e:
        logger.warning(f"Login failed for {credentials.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later."
        )
