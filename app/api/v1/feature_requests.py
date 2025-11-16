"""
Feature request API endpoints.
Handles user suggestions and admin management.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas.feature_request_dto import (
    FeatureRequestCreate,
    FeatureRequestUpdate,
    FeatureRequestResponse
)
from app.services.feature_request_service import feature_request_service
from app.api.deps import get_current_active_user, require_admin
from app.models.user import User
from app.models.feature_request import FeatureRequestStatus
from app.core.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feature-requests", tags=["Feature Requests"])


@router.get("/", response_model=List[FeatureRequestResponse])
async def list_feature_requests(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Get all feature requests.

    Authenticated users can view all feature requests.
    Results are ordered by priority (high to low) and creation date.
    """
    logger.info(f"Fetching all feature requests by user_id={current_user.id}")

    try:
        requests = await feature_request_service.get_all(db, skip, limit)
        logger.info(f"Retrieved {len(requests)} feature requests")
        return requests
    except Exception as e:
        logger.error(f"Error fetching feature requests: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feature requests"
        )


@router.post("/", response_model=FeatureRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_feature_request(
        request_in: FeatureRequestCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Create a new feature request.

    - **title**: Feature title (min 5 characters, max 255)
    - **description**: Detailed description (min 10 characters)
    - **priority**: Priority rating 0-10 (default: 0)

    Created requests start in 'pending' status awaiting admin review.
    """
    logger.info(f"Creating feature request by user_id={current_user.id}: {request_in.title}")

    try:
        feature_request = await feature_request_service.create_feature_request(
            db, request_in, current_user.id
        )
        logger.info(f"Feature request created: id={feature_request.id}")
        return feature_request
    except ValidationError as e:
        logger.warning(f"Feature request creation validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating feature request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create feature request"
        )


@router.get("/my-requests", response_model=List[FeatureRequestResponse])
async def get_my_feature_requests(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Get all feature requests created by the authenticated user.
    """
    logger.info(f"Fetching feature requests for user_id={current_user.id}")

    try:
        requests = await feature_request_service.get_by_user(
            db, current_user.id, skip, limit
        )
        logger.info(f"Retrieved {len(requests)} feature requests for user_id={current_user.id}")
        return requests
    except Exception as e:
        logger.error(f"Error fetching user feature requests: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch your feature requests"
        )


@router.patch("/{request_id}", response_model=FeatureRequestResponse)
async def update_feature_request_status(
        request_id: int,
        update_in: FeatureRequestUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """
    Update feature request status (admin only).

    Admins can change status to: pending, accepted, declined
    Can also update priority rating.

    - **status**: New status
    - **priority**: New priority (0-10)
    """
    logger.info(f"Updating feature request id={request_id} by admin user_id={current_user.id}")

    try:
        if update_in.status:
            feature_request = await feature_request_service.update_status(
                db, request_id, update_in.status
            )
        else:
            from app.crud.feature_request_crud import feature_request_crud
            feature_request = await feature_request_crud.update(db, request_id, update_in)

        if not feature_request:
            raise NotFoundError("Feature request not found")

        logger.info(f"Feature request updated: id={request_id}")
        return feature_request
    except NotFoundError as e:
        logger.warning(f"Feature request not found: id={request_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Feature request update validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating feature request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feature request"
        )
