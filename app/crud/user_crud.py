"""
User CRUD operations with authentication methods.
Implements abstract BaseCRUD with user-specific functionality.
"""
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.crud.base_crud import BaseCRUD
from app.models.user import User
from app.schemas.user_dto import UserCreate, UserBase
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


class UserCRUD(BaseCRUD[User, UserCreate, UserBase]):
    """
    User CRUD implementation with authentication methods.
    Extends BaseCRUD with user-specific operations.
    """

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            db: Database session
            email: User email

        Returns:
            User instance or None

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.debug(f"Fetching user by email: {email}")
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if user:
                logger.debug(f"User found with email: {email}")
            else:
                logger.debug(f"No user found with email: {email}")

            return user
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching user by email {email}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to fetch user by email", details={"email": email, "error": str(e)})

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            db: Database session
            username: Username

        Returns:
            User instance or None

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.debug(f"Fetching user by username: {username}")
            result = await db.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()

            if user:
                logger.debug(f"User found with username: {username}")
            else:
                logger.debug(f"No user found with username: {username}")

            return user
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching user by username {username}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to fetch user by username", details={"username": username, "error": str(e)})

    async def create(self, db: AsyncSession, obj_in: UserCreate) -> User:
        """
        Create new user with hashed password.

        Args:
            db: Database session
            obj_in: User creation schema

        Returns:
            Created user instance

        Raises:
            ValidationError: If email or username already exists
            DatabaseError: If database operation fails
        """
        try:
            logger.info(f"Creating new user with email: {obj_in.email}")

            # Check if email already exists
            existing_user = await self.get_by_email(db, obj_in.email)
            if existing_user:
                logger.warning(f"Attempt to create user with existing email: {obj_in.email}")
                raise ValidationError("Email already registered")

            # Check if username already exists
            existing_user = await self.get_by_username(db, obj_in.username)
            if existing_user:
                logger.warning(f"Attempt to create user with existing username: {obj_in.username}")
                raise ValidationError("Username already taken")

            # Create user with hashed password
            obj_data = obj_in.model_dump()
            obj_data["hashed_password"] = get_password_hash(obj_data.pop("password"))

            db_obj = User(**obj_data)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)

            logger.info(f"User created successfully: id={db_obj.id}, email={db_obj.email}")
            return db_obj
        except ValidationError:
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error creating user: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to create user", details={"error": str(e)})

    async def authenticate(
            self,
            db: AsyncSession,
            email: str,
            password: str
    ) -> Optional[User]:
        """
        Authenticate user with email and password.

        Args:
            db: Database session
            email: User email
            password: Plain text password

        Returns:
            User instance if authenticated, None otherwise
        """
        try:
            logger.info(f"Authenticating user: {email}")
            user = await self.get_by_email(db, email)

            if not user:
                logger.warning(f"Authentication failed: user not found - {email}")
                return None

            if not verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: invalid password for {email}")
                return None

            logger.info(f"User authenticated successfully: {email}")
            return user
        except Exception as e:
            logger.error(f"Error during authentication for {email}: {str(e)}", exc_info=True)
            return None

    async def is_active(self, user: User) -> bool:
        """
        Check if user is active.

        Args:
            user: User instance

        Returns:
            True if user is active
        """
        is_active = user.is_active == 1
        logger.debug(f"User {user.id} active status: {is_active}")
        return is_active


# Create singleton instance
user_crud = UserCRUD(User)
