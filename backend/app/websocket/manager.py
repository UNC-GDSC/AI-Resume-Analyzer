"""WebSocket support for real-time updates."""

from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
import json
import asyncio


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket client.

        Args:
            websocket: WebSocket connection
            user_id: User identifier
        """
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user: {user_id}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket client.

        Args:
            websocket: WebSocket connection
            user_id: User identifier
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user: {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user's connections.

        Args:
            message: Message to send
            user_id: User identifier
        """
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {str(e)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connections.

        Args:
            message: Message to broadcast
        """
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)

    async def send_ranking_update(
        self, user_id: str, job_id: int, resume_id: int, status: str, data: dict = None
    ):
        """Send ranking update notification.

        Args:
            user_id: User identifier
            job_id: Job ID
            resume_id: Resume ID
            status: Status update (processing, completed, failed)
            data: Additional data
        """
        message = {
            "type": "ranking_update",
            "job_id": job_id,
            "resume_id": resume_id,
            "status": status,
            "data": data or {},
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_personal_message(message, user_id)

    async def send_batch_progress(
        self, user_id: str, job_id: int, total: int, processed: int, failed: int
    ):
        """Send batch processing progress update.

        Args:
            user_id: User identifier
            job_id: Job ID
            total: Total files
            processed: Successfully processed
            failed: Failed count
        """
        message = {
            "type": "batch_progress",
            "job_id": job_id,
            "total": total,
            "processed": processed,
            "failed": failed,
            "percentage": (processed + failed) / total * 100 if total > 0 else 0,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_personal_message(message, user_id)

    async def send_notification(
        self, user_id: str, title: str, message: str, notification_type: str = "info"
    ):
        """Send general notification.

        Args:
            user_id: User identifier
            title: Notification title
            message: Notification message
            notification_type: Type (info, success, warning, error)
        """
        notification = {
            "type": "notification",
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_personal_message(notification, user_id)


# Global connection manager instance
manager = ConnectionManager()
