import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect, status
from core.security import decode_token
from config import get_settings

settings = get_settings()
logger = logging.getLogger("dialecta.ws")

# Registry of active connections: debate_id -> list of WebSockets
_connections: dict[str, list[WebSocket]] = {}


async def authenticate_websocket(websocket: WebSocket) -> dict:
    """
    Wait for first message containing JWT token.
    Close with 4001 if invalid, 4002 if timeout.
    Returns decoded token payload on success.
    """
    try:
        # Wait for auth message with timeout
        auth_message = await asyncio.wait_for(
            websocket.receive_json(),
            timeout=settings.WS_AUTH_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        await websocket.close(code=4002, reason="Authentication timeout")
        raise WebSocketDisconnect(code=4002)
    except Exception:
        await websocket.close(code=4001, reason="Authentication failed")
        raise WebSocketDisconnect(code=4001)

    token = auth_message.get("token")
    if not token:
        await websocket.close(code=4001, reason="No token provided")
        raise WebSocketDisconnect(code=4001)

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Wrong token type")
        logger.info("WebSocket authenticated for user %s", payload.get("sub"))
        return payload
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        raise WebSocketDisconnect(code=4001)


def register_connection(debate_id: str, websocket: WebSocket) -> None:
    if debate_id not in _connections:
        _connections[debate_id] = []
    _connections[debate_id].append(websocket)
    logger.info("WebSocket registered for debate %s (%d total)",
                debate_id, len(_connections[debate_id]))


def unregister_connection(debate_id: str, websocket: WebSocket) -> None:
    if debate_id in _connections:
        _connections[debate_id] = [
            ws for ws in _connections[debate_id] if ws != websocket
        ]
        if not _connections[debate_id]:
            del _connections[debate_id]
    logger.info("WebSocket unregistered for debate %s", debate_id)


async def broadcast(debate_id: str, event: dict) -> None:
    """Send event to all WebSockets connected to a debate."""
    if debate_id not in _connections:
        return
    dead = []
    for ws in _connections[debate_id]:
        try:
            await ws.send_json(event)
        except Exception:
            dead.append(ws)
    for ws in dead:
        unregister_connection(debate_id, ws)


def get_active_connections() -> dict[str, int]:
    """Return debate_id -> connection count. Used by admin endpoints."""
    return {debate_id: len(conns) for debate_id, conns in _connections.items()}