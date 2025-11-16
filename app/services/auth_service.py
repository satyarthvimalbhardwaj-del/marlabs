"""
Authentication and authorization service.
Handles user registration, login, and token management.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from app.services.base_service import BaseService
from app.crud.user_crud import user_crud, UserCRUD
from app.schemas.user_dto import UserCreate, UserLogin, TokenResponse, TokenData
from app.core.security import verify_password, get_password_hash
from app.core.exceptions import AuthenticationError, ValidationError
from app.config import settings

logger = logging.getLogger(__name__)


class AuthService(BaseService[UserCRUD]):
    """
    Authentication service handling user registration, login, and token management.
    Implements JWT-based authentication with refresh tokens.
    """

    def __init__(self):
        """Initialize with user CRUD."""
        super().__init__(user_crud)

    async def validate_create(self, db: AsyncSession, obj_in: UserCreate) -> bool:
        """
        Validate user registration data.
        Checks for duplicate email/username.

        Args:
            db: Database session
            obj_in: User creation data

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        logger.debug(f"Validating user creation for email: {obj_in.email}")

        # Check if email exists
        existing_user = await self.crud.get_by_email(db, obj_in.email)
        if existing_user:
            logger.warning(f"Validation failed: Email already registered - {obj_in.email}")
            raise ValidationError("Email already registered")

        # Check if username exists
        existing_user = await self.crud.get_by_username(db, obj_in.username)
        if existing_user:
            logger.warning(f"Validation failed: Username already taken - {obj_in.username}")
            raise ValidationError("Username already taken")

        logger.debug(f"User creation validation passed for: {obj_in.email}")
        return True

    async def validate_update(self, db: AsyncSession, id: int, obj_in: any) -> bool:
        """Validate user update (not implemented in this version)."""
        logger.debug(f"User update validation for id={id}")
        return True

    async def register_user(self, db: AsyncSession, user_in: UserCreate):
        """
        Register a new user.

        Args:
            db: Database session
            user_in: User registration data

        Returns:
            Created user instance

        Raises:
            ValidationError: If validation fails
        """
        logger.info(f"Registering new user: {user_in.email}")

        try:
            await self.validate_create(db, user_in)
            user = await self.crud.create(db, user_in)
            logger.info(f"User registered successfully: id={user.id}, email={user.email}")
            return user
        except ValidationError as e:
            logger.error(f"User registration failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during user registration: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to register user: {str(e)}")

    async def authenticate_user(
            self,
            db: AsyncSession,
            credentials: UserLogin
    ) -> TokenResponse:
        """
        Authenticate user and generate tokens.

        Args:
            db: Database session
            credentials: Login credentials

        Returns:
            TokenResponse with access and refresh tokens

        Raises:
            AuthenticationError: If authentication fails
        """
        logger.info(f"Authenticating user: {credentials.email}")

        try:
            user = await self.crud.authenticate(db, credentials.email, credentials.password)
            if not user:
                logger.warning(f"Authentication failed for: {credentials.email}")
                raise AuthenticationError("Invalid email or password")

            if not await self.crud.is_active(user):
                logger.warning(f"Authentication failed: Inactive user - {credentials.email}")
                raise AuthenticationError("User account is inactive")

            # Generate tokens
            access_token = self._create_access_token(user.id, user.email, user.role.value)
            refresh_token = self._create_refresh_token(user.id)

            logger.info(f"User authenticated successfully: {credentials.email}")
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token
            )
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}", exc_info=True)
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    def _create_access_token(self, user_id: int, email: str, role: str) -> str:
        """
        Create JWT access token.

        Args:
            user_id: User ID
            email: User email
            role: User role

        Returns:
            Encoded JWT token
        """
        logger.debug(f"Creating access token for user_id={user_id}")

        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta

        to_encode = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "exp": expire,
            "type": "access"
        }

        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        logger.debug(f"Access token created for user_id={user_id}")
        return encoded_jwt

    def _create_refresh_token(self, user_id: int) -> str:
        """
        Create JWT refresh token.

        Args:
            user_id: User ID

        Returns:
            Encoded JWT token
        """
        logger.debug(f"Creating refresh token for user_id={user_id}")

        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.utcnow() + expires_delta

        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh"
        }

        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        logger.debug(f"Refresh token created for user_id={user_id}")
        return encoded_jwt


# Create singleton instance
auth_service = AuthService()
