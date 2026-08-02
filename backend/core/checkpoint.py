import logging
from datetime import datetime, timezone
from db.supabase_client import supabase_admin

logger = logging.getLogger("dialecta.checkpoint")


async def save_checkpoint(
    debate_id: str,
    sub_debate_id: str,
    round_number: int,
    state: dict,
) -> bool:
    """
    Save debate state after every round.
    Returns True on success, False on failure.
    Debate continues even if checkpoint fails.
    """
    try:
        supabase_admin.table("checkpoints").upsert({
            "debate_id": debate_id,
            "round_number": round_number,
            "state_json": state,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        logger.info("Checkpoint saved: debate=%s round=%d", debate_id, round_number)
        return True
    except Exception as e:
        logger.error("Checkpoint save failed: %s", e)
        return False


async def load_checkpoint(debate_id: str) -> dict | None:
    """
    Load the latest checkpoint for a debate.
    Returns state dict or None if no checkpoint exists.
    """
    try:
        result = (
            supabase_admin.table("checkpoints")
            .select("*")
            .eq("debate_id", debate_id)
            .order("round_number", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            logger.info("Checkpoint loaded: debate=%s round=%d",
                        debate_id, result.data[0]["round_number"])
            return result.data[0]
        return None
    except Exception as e:
        logger.error("Checkpoint load failed: %s", e)
        return None


async def delete_checkpoints(debate_id: str) -> None:
    """Clean up checkpoints after debate completes successfully."""
    try:
        supabase_admin.table("checkpoints").delete().eq("debate_id", debate_id).execute()
        logger.info("Checkpoints deleted for debate %s", debate_id)
    except Exception as e:
        logger.error("Checkpoint delete failed: %s", e)