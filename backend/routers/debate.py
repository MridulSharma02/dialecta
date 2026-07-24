import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.websocket_auth import authenticate_websocket
from core.events import DebateStartedEvent
from agents.orchestrator import Orchestrator
from db.supabase_client import supabase_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/debate")
async def debate_websocket(websocket: WebSocket):
    await websocket.accept()

    # Step 1 — Authenticate the WebSocket connection
    user = await authenticate_websocket(websocket)
    if not user:
        return  # authenticate_websocket already closed the connection

    user_id = user["sub"]
    debate_id = str(uuid.uuid4())

    try:
        # Step 2 — Receive debate config from client
        config = await websocket.receive_json()
        topic = config.get("topic", "").strip()
        audience_persona = config.get("audience_persona", "general public")

        if not topic:
            await websocket.send_json({"event": "error", "data": {"message": "Topic is required"}})
            await websocket.close()
            return

        # Step 3 — Create debate record in Supabase
        supabase_service.table("debates").insert({
            "debate_id": debate_id,
            "user_id": user_id,
            "topic": topic,
            "status": "running",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        logger.info(f"[DebateWS] Debate {debate_id} started by user {user_id}")

        # Step 4 — Build the emit function that sends events over WebSocket
        async def emit(event_type: str, data: dict):
            try:
                await websocket.send_json({"event": event_type, "data": data})
            except Exception as e:
                logger.warning(f"[DebateWS] Could not emit {event_type}: {e}")

        # Step 5 — Run the full debate via Orchestrator
        orchestrator = Orchestrator(emit=emit)
        await orchestrator.run_debate(
            debate_id=debate_id,
            user_id=user_id,
            topic=topic,
            audience_persona=audience_persona,
        )

    except WebSocketDisconnect:
        logger.info(f"[DebateWS] Client disconnected. Debate {debate_id}")
        # Mark debate as disconnected in Supabase
        try:
            supabase_service.table("debates").update({
                "status": "disconnected"
            }).eq("debate_id", debate_id).execute()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"[DebateWS] Unexpected error in debate {debate_id}: {e}")
        try:
            await websocket.send_json({
                "event": "error",
                "data": {"message": "An internal error occurred. Please try again."}
            })
            supabase_service.table("debates").update({
                "status": "failed"
            }).eq("debate_id", debate_id).execute()
        except Exception:
            pass
        finally:
            await websocket.close()