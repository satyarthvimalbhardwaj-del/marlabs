"""
WebSocket endpoints for real-time comments.
"""
import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Set
from app.database import get_db
from app.crud.comment_crud import comment_crud
from app.schemas.comment_dto import CommentCreate
from app.core.security import decode_token
from jose import JWTError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSockets"])


class ConnectionManager:
    """Manages WebSocket connections for blog comments."""

    def __init__(self):
        # blog_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        logger.info("ConnectionManager initialized")

    async def connect(self, websocket: WebSocket, blog_id: int):
        """Accept and register WebSocket connection."""
        await websocket.accept()

        if blog_id not in self.active_connections:
            self.active_connections[blog_id] = set()

        self.active_connections[blog_id].add(websocket)
        logger.info(
            f"WebSocket connected for blog_id={blog_id}. Total connections: {len(self.active_connections[blog_id])}")

    def disconnect(self, websocket: WebSocket, blog_id: int):
        """Remove WebSocket connection."""
        if blog_id in self.active_connections:
            self.active_connections[blog_id].discard(websocket)

            # Clean up empty sets
            if not self.active_connections[blog_id]:
                del self.active_connections[blog_id]

        logger.info(f"WebSocket disconnected for blog_id={blog_id}")

    async def broadcast(self, message: dict, blog_id: int):
        """Broadcast message to all connections for a blog."""
        if blog_id not in self.active_connections:
            return

        dead_connections = set()
        for connection in self.active_connections[blog_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {str(e)}")
                dead_connections.add(connection)

        # Remove dead connections
        for connection in dead_connections:
            self.disconnect(connection, blog_id)

        logger.debug(f"Broadcast message to {len(self.active_connections[blog_id])} connections for blog_id={blog_id}")


manager = ConnectionManager()


@router.websocket("/ws/blogs/{blog_id}/comments")
async def websocket_blog_comments(
        websocket: WebSocket,
        blog_id: int,
        token: str = Query(..., description="JWT access token"),
        db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time blog comments.

    Connect to this endpoint to send and receive comments in real-time.

    Connection URL: `/api/v1/ws/blogs/{blog_id}/comments?token=<your_jwt_token>`

    Message format for sending comments:
    ```
    {
        "content": "Your comment text here"
    }
    ```

    Received message format:
    ```
    {
        "type": "comment",
        "data": {
            "id": 1,
            "content": "Comment text",
            "user_id": 123,
            "created_at": "2025-11-16T12:00:00"
        }
    }
    ```
    """
    # Authenticate user via token
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))

        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        return

    # Connect WebSocket
    await manager.connect(websocket, blog_id)
    logger.info(f"User user_id={user_id} connected to blog_id={blog_id} comments")

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            # Create comment
            comment_create = CommentCreate(
                content=data.get("content", ""),
                blog_id=blog_id
            )

            # Save to database
            from pydantic import create_model
            CommentCreateExtended = create_model(
                'CommentCreateExtended',
                user_id=(int, ...),
                __base__=CommentCreate
            )

            comment_data = comment_create.model_dump()
            comment_data["user_id"] = user_id
            comment_extended = CommentCreateExtended(**comment_data)

            comment = await comment_crud.create(db, comment_extended)
            logger.info(f"Comment created: id={comment.id}, blog_id={blog_id}, user_id={user_id}")

            # Broadcast to all connected clients
            message = {
                "type": "comment",
                "data": {
                    "id": comment.id,
                    "content": comment.content,
                    "user_id": comment.user_id,
                    "created_at": str(comment.created_at)
                }
            }

            await manager.broadcast(message, blog_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, blog_id)
        logger.info(f"User user_id={user_id} disconnected from blog_id={blog_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user_id={user_id}, blog_id={blog_id}: {str(e)}", exc_info=True)
        manager.disconnect(websocket, blog_id)
