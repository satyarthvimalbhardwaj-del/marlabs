"""
Blog CRUD operations with approval workflow.
Implements abstract BaseCRUD with blog-specific functionality.
"""
import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.crud.base_crud import BaseCRUD
from app.models.blog import Blog, BlogStatus
from app.schemas.blog_dto import BlogCreate, BlogUpdate
from app.core.exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


class BlogCRUD(BaseCRUD[Blog, BlogCreate, BlogUpdate]):
    """
    Blog CRUD implementation with approval workflow.
    Extends BaseCRUD with blog-specific operations.
    """

    async def get_by_author(
            self,
            db: AsyncSession,
            author_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[Blog]:
        """
        Get all blogs by specific author.

        Args:
            db: Database session
            author_id: Author user ID
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of blog instances

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.debug(f"Fetching blogs for author_id={author_id}, skip={skip}, limit={limit}")
            query = select(Blog).where(Blog.author_id == author_id).offset(skip).limit(limit).order_by(
                Blog.created_at.desc())
            result = await db.execute(query)
            blogs = result.scalars().all()

            logger.debug(f"Retrieved {len(blogs)} blogs for author_id={author_id}")
            return list(blogs)
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching blogs for author {author_id}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to fetch blogs for author", details={"author_id": author_id, "error": str(e)})

    async def get_approved_blogs(
            self,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100
    ) -> List[Blog]:
        """
        Get all approved (public) blogs.

        Args:
            db: Database session
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of approved blog instances

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.debug(f"Fetching approved blogs: skip={skip}, limit={limit}")
            query = select(Blog).where(
                Blog.status == BlogStatus.APPROVED
            ).offset(skip).limit(limit).order_by(Blog.approved_at.desc())
            result = await db.execute(query)
            blogs = result.scalars().all()

            logger.debug(f"Retrieved {len(blogs)} approved blogs")
            return list(blogs)
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching approved blogs: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to fetch approved blogs", details={"error": str(e)})

    async def get_pending_blogs(
            self,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100
    ) -> List[Blog]:
        """
        Get all pending blogs awaiting approval.

        Args:
            db: Database session
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of pending blog instances

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.debug(f"Fetching pending blogs: skip={skip}, limit={limit}")
            query = select(Blog).where(
                Blog.status == BlogStatus.PENDING
            ).offset(skip).limit(limit).order_by(Blog.created_at.desc())
            result = await db.execute(query)
            blogs = result.scalars().all()

            logger.info(f"Retrieved {len(blogs)} pending blogs")
            return list(blogs)
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching pending blogs: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to fetch pending blogs", details={"error": str(e)})

    async def approve_blog(
            self,
            db: AsyncSession,
            blog_id: int,
            approver_id: int
    ) -> Optional[Blog]:
        """
        Approve a pending blog.

        Args:
            db: Database session
            blog_id: Blog ID to approve
            approver_id: Admin/approver user ID

        Returns:
            Updated blog instance or None

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.info(f"Approving blog id={blog_id} by approver_id={approver_id}")
            blog = await self.get(db, blog_id)

            if not blog:
                logger.warning(f"Blog id={blog_id} not found for approval")
                return None

            blog.status = BlogStatus.APPROVED
            blog.approved_by = approver_id
            blog.approved_at = datetime.utcnow()

            await db.commit()
            await db.refresh(blog)

            logger.info(f"Blog id={blog_id} approved successfully")
            return blog
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error approving blog {blog_id}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to approve blog", details={"blog_id": blog_id, "error": str(e)})

    async def reject_blog(
            self,
            db: AsyncSession,
            blog_id: int
    ) -> Optional[Blog]:
        """
        Reject a pending blog.

        Args:
            db: Database session
            blog_id: Blog ID to reject

        Returns:
            Updated blog instance or None

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.info(f"Rejecting blog id={blog_id}")
            blog = await self.get(db, blog_id)

            if not blog:
                logger.warning(f"Blog id={blog_id} not found for rejection")
                return None

            blog.status = BlogStatus.REJECTED

            await db.commit()
            await db.refresh(blog)

            logger.info(f"Blog id={blog_id} rejected successfully")
            return blog
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error rejecting blog {blog_id}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to reject blog", details={"blog_id": blog_id, "error": str(e)})


# Create singleton instance
blog_crud = BlogCRUD(Blog)
