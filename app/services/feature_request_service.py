"""
Feature request management service.
Handles user suggestions and admin actions.
"""
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.base_service import BaseService
from app.crud.feature_request_crud import feature_request_crud, FeatureRequestCRUD
from app.schemas.feature_request_dto import FeatureRequestCreate, FeatureRequestUpdate
from app.core.exceptions import ValidationError, NotFoundError
from app.models.feature_request import FeatureRequestStatus

logger = logging.getLogger(__name__)


class FeatureRequestService(BaseService[FeatureRequestCRUD]):
    """
    Feature request service handling user suggestions.
    Manages status updates and priority assignments.
    """

    def __init__(self):
        """Initialize with feature request CRUD."""
        super().__init__(feature_request_crud)

    async def validate_create(self, db: AsyncSession, obj_in: FeatureRequestCreate) -> bool:
        """
        Validate feature request creation.

        Args:
            db: Database session
            obj_in: Feature request data

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        logger.debug(f"Validating feature request creation: {obj_in.title}")

        if len(obj_in.title) < 5:
            logger.warning(f"Validation failed: Title too short")
            raise ValidationError("Title must be at least 5 characters")

        if len(obj_in.description) < 10:
            logger.warning(f"Validation failed: Description too short")
            raise ValidationError("Description must be at least 10 characters")

        logger.debug(f"Feature request validation passed: {obj_in.title}")
        return True

    async def validate_update(self, db: AsyncSession, id: int, obj_in: FeatureRequestUpdate) -> bool:
        """
        Validate feature request update.

        Args:
            db: Database session
            id: Feature request ID
            obj_in: Update data

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        logger.debug(f"Validating feature request update for id={id}")

        fr = await self.crud.get(db, id)
        if not fr:
            logger.warning(f"Validation failed: Feature request not found - id={id}")
            raise NotFoundError("Feature request not found")

        logger.debug(f"Feature request update validation passed for id={id}")
        return True

    async def create_feature_request(
            self,
            db: AsyncSession,
            fr_in: FeatureRequestCreate,
            user_id: int
    ):
        """
        Create a new feature request.

        Args:
            db: Database session
            fr_in: Feature request data
            user_id: User ID

        Returns:
            Created feature request

        Raises:
            ValidationError: If validation fails
        """
        logger.info(f"Creating feature request by user_id={user_id}: {fr_in.title}")

        try:
            await self.validate_create(db, fr_in)

            from pydantic import create_model
            FeatureRequestCreateExtended = create_model(
                'FeatureRequestCreateExtended',
                user_id=(int, ...),
                __base__=FeatureRequestCreate
            )

            fr_data = fr_in.model_dump()
            fr_data["user_id"] = user_id
            fr_extended = FeatureRequestCreateExtended(**fr_data)

            feature_request = await self.crud.create(db, fr_extended)
            logger.info(f"Feature request created successfully: id={feature_request.id}")
            return feature_request
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating feature request: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to create feature request: {str(e)}")

    async def update_status(
            self,
            db: AsyncSession,
            fr_id: int,
            status: FeatureRequestStatus
    ):
        """
        Update feature request status (admin only).

        Args:
            db: Database session
            fr_id: Feature request ID
            status: New status

        Returns:
            Updated feature request

        Raises:
            ValidationError: If validation fails
        """
        logger.info(f"Updating feature request id={fr_id} status to {status.value}")

        try:
            update_data = FeatureRequestUpdate(status=status)
            await self.validate_update(db, fr_id, update_data)

            feature_request = await self.crud.update(db, fr_id, update_data)
            logger.info(f"Feature request status updated: id={fr_id}, status={status.value}")
            return feature_request
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error updating feature request status: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to update status: {str(e)}")

    async def get_all(
            self,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100
    ) -> List:
        """
        Get all feature requests.

        Args:
            db: Database session
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of feature requests
        """
        logger.debug(f"Fetching all feature requests: skip={skip}, limit={limit}")

        try:
            requests = await self.crud.get_multi(db, skip, limit)
            logger.debug(f"Retrieved {len(requests)} feature requests")
            return requests
        except Exception as e:
            logger.error(f"Error fetching feature requests: {str(e)}", exc_info=True)
            raise

    async def get_by_user(
            self,
            db: AsyncSession,
            user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List:
        """
        Get feature requests by user.

        Args:
            db: Database session
            user_id: User ID
            skip: Pagination offset
            limit: Maximum results

        Returns:
            List of user's feature requests
        """
        logger.debug(f"Fetching feature requests for user_id={user_id}")

        try:
            requests = await self.crud.get_by_user(db, user_id, skip, limit)
            logger.debug(f"Retrieved {len(requests)} feature requests for user_id={user_id}")
            return requests
        except Exception as e:
            logger.error(f"Error fetching user feature requests: {str(e)}", exc_info=True)
            raise


# Create singleton instance
feature_request_service = FeatureRequestService()
