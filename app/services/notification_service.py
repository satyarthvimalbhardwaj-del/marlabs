"""
Notification service for Server-Sent Events (SSE).
Manages real-time notifications for admins and approvers.
"""
import logging
import asyncio
from typing import Set
from app.models.blog import Blog

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Notification service for Server-Sent Events (SSE).
    Manages real-time notifications for pending blog approvals.
    """

    def __init__(self):
        """Initialize notification queues and subscribers."""
        self._subscribers: Set[asyncio.Queue] = set()
        logger.info("NotificationService initialized")

    async def subscribe(self) -> asyncio.Queue:
        """
        Subscribe to notifications.

        Returns:
            Queue for receiving notifications
        """
        queue = asyncio.Queue()
        self._subscribers.add(queue)
        logger.info(f"New subscriber added. Total subscribers: {len(self._subscribers)}")
        return queue

    async def unsubscribe(self, queue: asyncio.Queue):
        """
        Unsubscribe from notifications.

        Args:
            queue: Queue to remove
        """
        self._subscribers.discard(queue)
        logger.info(f"Subscriber removed. Total subscribers: {len(self._subscribers)}")

    async def notify_pending_blog(self, blog: Blog):
        """
        Notify all subscribers about a new pending blog.

        Args:
            blog: Newly created pending blog
        """
        logger.info(f"Broadcasting notification for pending blog id={blog.id}")

        message = {
            "event": "new_pending_blog",
            "data": {
                "id": blog.id,
                "title": blog.title,
                "author_id": blog.author_id,
                "created_at": str(blog.created_at)
            }
        }

        # Send to all subscribers
        dead_queues = []
        for queue in self._subscribers:
            try:
                await queue.put(message)
                logger.debug(f"Notification sent to subscriber")
            except Exception as e:
                logger.error(f"Error sending notification to subscriber: {str(e)}")
                dead_queues.append(queue)

        # Remove dead queues
        for queue in dead_queues:
            self._subscribers.discard(queue)

        logger.info(f"Notification broadcast complete. Active subscribers: {len(self._subscribers)}")

    async def notify_blog_approved(self, blog: Blog):
        """
        Notify about blog approval.

        Args:
            blog: Approved blog
        """
        logger.info(f"Broadcasting notification for approved blog id={blog.id}")

        message = {
            "event": "blog_approved",
            "data": {
                "id": blog.id,
                "title": blog.title,
                "approved_at": str(blog.approved_at)
            }
        }

        for queue in self._subscribers:
            try:
                await queue.put(message)
            except Exception as e:
                logger.error(f"Error sending approval notification: {str(e)}")


# Create singleton instance
notification_service = NotificationService()
