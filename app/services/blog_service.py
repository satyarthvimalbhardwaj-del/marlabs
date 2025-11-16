"""
Blog management service with approval workflow.
Handles blog lifecycle and permissions.
"""
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base_service import BaseService
from app.crud.blog_crud import blog_crud, BlogCRUD
from app.schemas.blog_dto import BlogCreate, BlogUpdate, BlogResponse
from app.core.exceptions import ValidationError, AuthorizationError, NotFoundError
from app.models.blog import BlogStatus
from app.models.user import UserRole

logger = logging.getLogger(__name__)


class BlogService(BaseService[BlogCRUD]):
    """
    Blog service handling article lifecycle and approval workflow.
    Manages permissions for creation, editing, and approval.
    """

    def __init__(self):
        """Initialize with blog CRUD."""
        super().__init__(blog_crud)

    async def validate_create(self, db: AsyncSession, obj_in: BlogCreate) -> bool:
        """
        Validate blog creation.
        Checks content requirements.

        Args:
            db: Database session
            obj_in: Blog creation data

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        logger.debug(f"Validating blog creation: {obj_in.title}")

        if len(obj_in.title) < 5:
            logger.warning(f"Validation failed: Title too short - {obj_in.title}")
            raise ValidationError("Title must be at least 5 characters")

        if len(obj_in.content) < 10:
            logger.warning(f"Validation failed: Content too short")
            raise ValidationError("Content must be at least 10 characters")

        logger.debug(f"Blog creation validation passed: {obj_in.title}")
        return True

    async def validate_update(self, db: AsyncSession, id: int, obj_in: BlogUpdate) -> bool:
        """
        Validate blog update.
        Checks if blog exists and is editable.

        Args:
            db: Database session
            id: Blog ID
            obj_in: Update data

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        logger.debug(f"Validating blog update for id={id}")

        blog = await self.crud.get(db, id)
        if not blog:
            logger.warning(f"Validation failed: Blog not found - id={id}")
            raise NotFoundError("Blog not found")

        # Only pending blogs can be edited
        if blog.status != BlogStatus.PENDING:
            logger.warning(f"Validation failed: Blog not in pending status - id={id}, status={blog.status}")
            raise ValidationError("Only pending blogs can be edited")

        logger.debug(f"Blog update validation passed for id={id}")
        return True

    async def create_blog(
        self,
        db: AsyncSession,
        blog_in: BlogCreate,
        author_id: int
    ):
        """
        Create a new blog post in pending status.

        Args:
            db: Database session
            blog_in: Blog creation data
            author_id: Author user ID

        Returns:
            Created blog instance

        Raises:
            ValidationError: If validation fails
        """
        logger.info(f"Creating blog by author_id={author_id}: {blog_in.title}")

        try:
            await self.validate_create(db, blog_in)

            # Create blog data with author_id
            from pydantic import create_model
            BlogCreateExtended = create_model(
                'BlogCreateExtended',
                author_id=(int, ...),
                status=(BlogStatus, BlogStatus.PENDING),
                __base__=BlogCreate
            )

            blog_data = blog_in.model_dump()
            blog_data["author_id"] = author_id
            blog_data["status"] = BlogStatus.PENDING

            blog_extended = BlogCreateExtended(**blog_data)
            blog = await self.crud.create(db, blog_extended)

            logger.info(f"Blog created successfully: id={blog.id}, title={blog.title}")
            return blog
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating blog: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to create blog: {str(e)}")

    async def get_public_blogs(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """
        Get all approved (public) blogs.

        Args:
            db: Database session
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of approved blogs
        """
        logger.debug(f"Fetching public blogs: skip={skip}, limit={limit}")

        try:
            blogs = await self.crud.get_approved_blogs(db, skip, limit)
            logger.debug(f"Retrieved {len(blogs)} public blogs")
            return blogs
        except Exception as e:
            logger.error(f"Error fetching public blogs: {str(e)}", exc_info=True)
            raise

    async def get_user_blogs(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """
        Get all blogs by a specific user.

        Args:
            db: Database session
            user_id: User ID
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of user's blogs
        """
        logger.debug(f"Fetching blogs for user_id={user_id}")

        try:
            blogs = await self.crud.get_by_author(db, user_id, skip, limit)
            logger.debug(f"Retrieved {len(blogs)} blogs for user_id={user_id}")
            return blogs
        except Exception as e:
            logger.error(f"Error fetching user blogs: {str(e)}", exc_info=True)
            raise

    async def update_blog(
        self,
        db: AsyncSession,
        blog_id: int,
        blog_in: BlogUpdate,
        user_id: int,
        user_role: UserRole
    ):
        """
        Update a blog post.
        Only author can update their own pending blogs.

        Args:
            db: Database session
            blog_id: Blog ID
            blog_in: Update data
            user_id: Current user ID
            user_role: Current user role

        Returns:
            Updated blog instance

        Raises:
            AuthorizationError: If user lacks permission
        """
        logger.info(f"Updating blog id={blog_id} by user_id={user_id}")

        try:
            blog = await self.crud.get(db, blog_id)
            if not blog:
                logger.warning(f"Blog not found: id={blog_id}")
                raise NotFoundError("Blog not found")

            # Check ownership
            if blog.author_id != user_id:
                logger.warning(f"Authorization failed: user_id={user_id} attempted to edit blog id={blog_id}")
                raise AuthorizationError("You can only edit your own blogs")

            await self.validate_update(db, blog_id, blog_in)
            updated_blog = await self.crud.update(db, blog_id, blog_in)

            logger.info(f"Blog updated successfully: id={blog_id}")
            return updated_blog
        except (ValidationError, AuthorizationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error updating blog: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to update blog: {str(e)}")

    async def delete_blog(
        self,
        db: AsyncSession,
        blog_id: int,
        user_id: int,
        user_role: UserRole
    ) -> bool:
        """
        Delete a blog post.
        Only author or admin can delete.

        Args:
            db: Database session
            blog_id: Blog ID
            user_id: Current user ID
            user_role: Current user role

        Returns:
            True if deleted

        Raises:
            AuthorizationError: If user lacks permission
        """
        logger.info(f"Deleting blog id={blog_id} by user_id={user_id}")

        try:
            blog = await self.crud.get(db, blog_id)
            if not blog:
                logger.warning(f"Blog not found: id={blog_id}")
                raise NotFoundError("Blog not found")

            # Check ownership or admin
            if blog.author_id != user_id and user_role != UserRole.ADMIN:
                logger.warning(f"Authorization failed: user_id={user_id} attempted to delete blog id={blog_id}")
                raise AuthorizationError("You can only delete your own blogs")

            result = await self.crud.delete(db, blog_id)
            logger.info(f"Blog deleted successfully: id={blog_id}")
            return result
        except (AuthorizationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error deleting blog: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to delete blog: {str(e)}")

    async def approve_blog(
        self,
        db: AsyncSession,
        blog_id: int,
        approver_id: int
    ):
        """
        Approve a pending blog (admin/approver only).

        Args:
            db: Database session
            blog_id: Blog ID
            approver_id: Approver user ID

        Returns:
            Approved blog instance
        """
        logger.info(f"Approving blog id={blog_id} by approver_id={approver_id}")

        try:
            blog = await self.crud.approve_blog(db, blog_id, approver_id)
            if not blog:
                logger.warning(f"Blog not found for approval: id={blog_id}")
                raise NotFoundError("Blog not found")

            logger.info(f"Blog approved successfully: id={blog_id}")
            return blog
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error approving blog: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to approve blog: {str(e)}")

    async def reject_blog(
        self,
        db: AsyncSession,
        blog_id: int
    ):
        """
        Reject a pending blog (admin/approver only).

        Args:
            db: Database session
            blog_id: Blog ID

        Returns:
            Rejected blog instance
        """
        logger.info(f"Rejecting blog id={blog_id}")

        try:
            blog = await self.crud.reject_blog(db, blog_id)
            if not blog:
                logger.warning(f"Blog not found for rejection: id={blog_id}")
                raise NotFoundError("Blog not found")

            logger.info(f"Blog rejected successfully: id={blog_id}")
            return blog
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error rejecting blog: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to reject blog: {str(e)}")

    async def get_pending_blogs(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """
        Get all pending blogs for approval.

        Args:
            db: Database session
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of pending blogs
        """
        logger.debug(f"Fetching pending blogs: skip={skip}, limit={limit}")

        try:
            blogs = await self.crud.get_pending_blogs(db, skip, limit)
            logger.debug(f"Retrieved {len(blogs)} pending blogs")
            return blogs
        except Exception as e:
            logger.error(f"Error fetching pending blogs: {str(e)}", exc_info=True)
            raise


# Create singleton instance
blog_service = BlogService()
