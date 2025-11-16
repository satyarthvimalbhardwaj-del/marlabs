"""
Blog management API endpoints.
Handles CRUD operations and approval workflow.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas.blog_dto import (
    BlogCreate, BlogUpdate, BlogResponse,
    BlogListResponse, BlogApprovalRequest
)
from app.services.blog_service import blog_service
from app.services.notification_service import notification_service
from app.api.deps import get_current_active_user, require_approver
from app.models.user import User
from app.core.exceptions import ValidationError, AuthorizationError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/blogs", tags=["Blogs"])


@router.get("/", response_model=List[BlogResponse])
async def list_public_blogs(
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=100, description="Maximum number of records"),
        db: AsyncSession = Depends(get_db)
):
    """
    Get all approved (public) blogs.

    This endpoint is publicly accessible without authentication.
    Only blogs with 'approved' status are returned.

    - **skip**: Pagination offset (default: 0)
    - **limit**: Maximum results per page (default: 100, max: 100)

    Returns list of approved blog posts ordered by approval date (newest first).
    """
    logger.info(f"Fetching public blogs: skip={skip}, limit={limit}")

    try:
        blogs = await blog_service.get_public_blogs(db, skip, limit)
        logger.info(f"Retrieved {len(blogs)} public blogs")
        return blogs
    except Exception as e:
        logger.error(f"Error fetching public blogs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch blogs"
        )


@router.post("/", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
async def create_blog(
        blog_in: BlogCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Create a new blog post (requires authentication).

    - **title**: Blog title (min 5 characters, max 255)
    - **content**: Blog content in markdown format (min 10 characters)
    - **images**: Optional list of image URLs

    Created blogs start in 'pending' status and require admin/approver approval
    before becoming publicly visible. Admins/approvers are notified in real-time.
    """
    logger.info(f"Creating blog by user_id={current_user.id}: {blog_in.title}")

    try:
        blog = await blog_service.create_blog(db, blog_in, current_user.id)

        # Notify admins about new pending blog via SSE
        await notification_service.notify_pending_blog(blog)

        logger.info(f"Blog created successfully: id={blog.id}, title={blog.title}")
        return blog
    except ValidationError as e:
        logger.warning(f"Blog creation validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating blog: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create blog"
        )


@router.get("/{blog_id}", response_model=BlogResponse)
async def get_blog(
        blog_id: int,
        db: AsyncSession = Depends(get_db)
):
    """
    Get a specific blog by ID.

    Only approved blogs are accessible via this public endpoint.
    Pending or rejected blogs cannot be viewed by public users.
    """
    logger.info(f"Fetching blog: id={blog_id}")

    try:
        from app.crud.blog_crud import blog_crud
        from app.models.blog import BlogStatus

        blog = await blog_crud.get(db, blog_id)

        if not blog:
            logger.warning(f"Blog not found: id={blog_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog not found"
            )

        # Only show approved blogs to public
        if blog.status != BlogStatus.APPROVED:
            logger.warning(f"Attempted access to non-approved blog: id={blog_id}, status={blog.status}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog not found"
            )

        logger.info(f"Blog retrieved: id={blog_id}")
        return blog
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching blog: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch blog"
        )


@router.get("/user/my-blogs", response_model=List[BlogResponse])
async def get_my_blogs(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Get all blogs created by the authenticated user.

    Returns all blogs (pending, approved, rejected) authored by the current user.
    """
    logger.info(f"Fetching blogs for user_id={current_user.id}")

    try:
        blogs = await blog_service.get_user_blogs(db, current_user.id, skip, limit)
        logger.info(f"Retrieved {len(blogs)} blogs for user_id={current_user.id}")
        return blogs
    except Exception as e:
        logger.error(f"Error fetching user blogs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch your blogs"
        )


@router.put("/{blog_id}", response_model=BlogResponse)
async def update_blog(
        blog_id: int,
        blog_in: BlogUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Update own blog post (requires authentication).

    Only the blog author can update their blog.
    Only blogs in 'pending' status can be edited.
    Approved or rejected blogs cannot be modified.

    - **title**: Updated title (optional)
    - **content**: Updated content (optional)
    - **images**: Updated image URLs (optional)
    """
    logger.info(f"Updating blog id={blog_id} by user_id={current_user.id}")

    try:
        blog = await blog_service.update_blog(
            db, blog_id, blog_in, current_user.id, current_user.role
        )
        logger.info(f"Blog updated successfully: id={blog_id}")
        return blog
    except NotFoundError as e:
        logger.warning(f"Blog not found for update: id={blog_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except (ValidationError, AuthorizationError) as e:
        logger.warning(f"Blog update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating blog: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update blog"
        )


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(
        blog_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Delete own blog post (requires authentication).

    Only the blog author or admins can delete a blog.
    """
    logger.info(f"Deleting blog id={blog_id} by user_id={current_user.id}")

    try:
        await blog_service.delete_blog(
            db, blog_id, current_user.id, current_user.role
        )
        logger.info(f"Blog deleted successfully: id={blog_id}")
    except NotFoundError as e:
        logger.warning(f"Blog not found for deletion: id={blog_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except (ValidationError, AuthorizationError) as e:
        logger.warning(f"Blog deletion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting blog: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete blog"
        )


@router.post("/{blog_id}/approve", response_model=BlogResponse)
async def approve_blog(
        blog_id: int,
        approval: BlogApprovalRequest,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_approver)
):
    """
    Approve a pending blog (admin/L1 approver only).

    Changes blog status from 'pending' to 'approved', making it publicly visible.
    Records the approver ID and approval timestamp.

    - **reason**: Optional approval reason/notes
    """
    logger.info(f"Approving blog id={blog_id} by user_id={current_user.id}")

    try:
        blog = await blog_service.approve_blog(db, blog_id, current_user.id)

        # Notify about approval
        await notification_service.notify_blog_approved(blog)

        logger.info(f"Blog approved successfully: id={blog_id}")
        return blog
    except NotFoundError as e:
        logger.warning(f"Blog not found for approval: id={blog_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Blog approval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error approving blog: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve blog"
        )


@router.post("/{blog_id}/reject", response_model=BlogResponse)
async def reject_blog(
        blog_id: int,
        rejection: BlogApprovalRequest,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_approver)
):
    """
    Reject a pending blog (admin/L1 approver only).

    Changes blog status from 'pending' to 'rejected'.
    Rejected blogs are not publicly visible.

    - **reason**: Optional rejection reason/feedback for the author
    """
    logger.info(f"Rejecting blog id={blog_id} by user_id={current_user.id}")

    try:
        blog = await blog_service.reject_blog(db, blog_id)
        logger.info(f"Blog rejected successfully: id={blog_id}")
        return blog
    except NotFoundError as e:
        logger.warning(f"Blog not found for rejection: id={blog_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Blog rejection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error rejecting blog: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject blog"
        )


@router.get("/pending/all", response_model=List[BlogResponse])
async def list_pending_blogs(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_approver)
):
    """
    Get all pending blogs for approval (admin/L1 approver only).

    Returns all blogs awaiting approval review, ordered by creation date.
    """
    logger.info(f"Fetching pending blogs by user_id={current_user.id}")

    try:
        blogs = await blog_service.get_pending_blogs(db, skip, limit)
        logger.info(f"Retrieved {len(blogs)} pending blogs")
        return blogs
    except Exception as e:
        logger.error(f"Error fetching pending blogs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pending blogs"
        )
