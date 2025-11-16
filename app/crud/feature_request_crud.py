"""
Feature Request CRUD operations.
Implements abstract BaseCRUD with feature request-specific functionality.
"""
import logging
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.crud.base_crud import BaseCRUD
from app.models.feature_request import FeatureRequest, FeatureRequestStatus
from app.schemas.feature_request_dto import FeatureRequestCreate, FeatureRequestUpdate
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class FeatureRequestCRUD(BaseCRUD[FeatureRequest, FeatureRequestCreate, FeatureRequestUpdate]):
    """
    Feature Request CRUD implementation.
    Extends BaseCRUD with feature request-specific operations.
    """

    async def get_by_user(
            self,
            db: AsyncSession,
            user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[FeatureRequest]:
        """
        Get all feature requests by specific user.

        Args:
            db: Database session
            user_id: User ID
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of feature request instances

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.debug(f"Fetching feature requests for user_id={user_id}")
            query = select(FeatureRequest).where(
                FeatureRequest.user_id == user_id
            ).offset(skip).limit(limit).order_by(FeatureRequest.created_at.desc())
            result = await db.execute(query)
            requests = result.scalars().all()

            logger.debug(f"Retrieved {len(requests)} feature requests for user_id={user_id}")
            return list(requests)
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching feature requests for user {user_id}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to fetch feature requests", details={"user_id": user_id, "error": str(e)})

    async def get_by_status(
            self,
            db: AsyncSession,
            status: FeatureRequestStatus,
            skip: int = 0,
            limit: int = 100
    ) -> List[FeatureRequest]:
        """
        Get feature requests by status.

        Args:
            db: Database session
            status: Feature request status
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of feature request instances

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            logger.debug(f"Fetching feature requests with status={status.value}")
            query = select(FeatureRequest).where(
                FeatureRequest.status == status
            ).offset(skip).limit(limit).order_by(FeatureRequest.priority.desc(), FeatureRequest.created_at.desc())
            result = await db.execute(query)
            requests = result.scalars().all()

            logger.debug(f"Retrieved {len(requests)} feature requests with status={status.value}")
            return list(requests)
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching feature requests by status {status}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to fetch feature requests by status",
                                details={"status": status.value, "error": str(e)})


# Create singleton instance
feature_request_crud = FeatureRequestCRUD(FeatureRequest)
