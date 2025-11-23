"""WebSocket endpoints."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.websocket.manager import manager
from app.core.security import verify_token
from loguru import logger
import json

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/connect/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket connection endpoint.

    Args:
        websocket: WebSocket connection
        token: JWT authentication token
    """
    try:
        # Verify token
        payload = verify_token(token)
        user_id = str(payload.get("sub"))

        # Connect
        await manager.connect(websocket, user_id)

        try:
            while True:
                # Receive messages from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "subscribe":
                    # Subscribe to specific job updates
                    job_id = message.get("job_id")
                    await websocket.send_json({
                        "type": "subscribed",
                        "job_id": job_id
                    })

        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
            logger.info(f"WebSocket disconnected: user {user_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()
