"""
Server-Sent Events (SSE) API for real-time notifications.
"""
import logging
import asyncio
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.api.deps import require_approver
from app.models.user import User
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/sse")
async def notification_stream(
        current_user: User = Depends(require_approver)
):
    """
    Server-Sent Events stream for real-time notifications (admin/approver only).

    Admins and approvers receive real-time notifications when:
    - New blogs are submitted for approval
    - Blogs are approved or rejected

    Keep this connection open to receive live updates.

    Example usage with JavaScript:
    ```
    const eventSource = new EventSource('/api/v1/notifications/sse', {
        headers: { 'Authorization': 'Bearer ' + token }
    });

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Notification:', data);
    };
    ```
    """
    logger.info(f"SSE stream opened by user_id={current_user.id}")

    async def event_generator():
        queue = await notification_service.subscribe()

        try:
            # Send initial connection message
            yield f"data: {json.dumps({'event': 'connected', 'message': 'Notification stream established'})}\n\n"

            while True:
                # Wait for notification
                message = await queue.get()

                # Format as SSE
                event_data = json.dumps(message)
                yield f"data: {event_data}\n\n"

                logger.debug(f"SSE notification sent to user_id={current_user.id}: {message['event']}")
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for user_id={current_user.id}")
        except Exception as e:
            logger.error(f"SSE stream error for user_id={current_user.id}: {str(e)}", exc_info=True)
        finally:
            await notification_service.unsubscribe(queue)
            logger.info(f"SSE stream closed for user_id={current_user.id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
