"""
Comment CRUD operations.
Implements abstract BaseCRUD with comment-specific functionality.
"""
import logging
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.crud.base_crud import BaseCRUD
from app.models.comment import Comment
from app.schemas.comment_dto import CommentCreate, CommentBase
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class CommentCRUD(BaseCRUD[Comment, CommentCreate, CommentBase]):
    """
    Comment CRUD implementation.
    Extends BaseCRUD with comment-specific operations.
    """

    async def get_by_blog(
            self,
            db: AsyncSession,
            blog_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[Comment]:
        """
        Get all comments for a specific blog.

        Args:
            db: Database session
            blog_id: Blog ID
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of comment instances

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.debug(f"Fetching comments for blog_id={blog_id}")
            query = select(Comment).where(
                Comment.blog_id == blog_id
            ).offset(skip).limit(limit).order_by(Comment.created_at.asc())
            result = await db.execute(query)
            comments = result.scalars().all()

            logger.debug(f"Retrieved {len(comments)} comments for blog_id={blog_id}")
            return list(comments)
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching comments for blog {blog_id}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to fetch comments", details={"blog_id": blog_id, "error": str(e)})


# Create singleton instance
comment_crud = CommentCRUD(Comment)
