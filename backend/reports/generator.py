from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

from db.supabase_client import supabase_admin


async def assemble_report(debate_id: str, user_id: str) -> dict[str, Any]:
    # ── 1. Debate header ────────────────────────────────────────
    debate_row = (
        supabase_admin
        .from_("debates")
        .select("*")
        .eq("debate_id", debate_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not debate_row.data:
        raise ValueError(f"Debate {debate_id} not found or access denied.")
    debate = debate_row.data

    # ── 2. Sub-debates (no created_at column) ──────────────────
    sub_rows = (
        supabase_admin
        .from_("sub_debates")
        .select("*")
        .eq("debate_id", debate_id)
        .execute()
    )
    sub_debates = sub_rows.data or []

    # ── 3. Rounds for every sub-debate ──────────────────────────
    enriched_subs = []
    for sub in sub_debates:
        sid = sub["sub_debate_id"]
        round_rows = (
            supabase_admin
            .from_("rounds")
            .select("*")
            .eq("sub_debate_id", sid)
            .order("round_number")
            .execute()
        )
        sub["rounds"] = round_rows.data or []
        enriched_subs.append(sub)

    # ── 4. Assemble final report dict ───────────────────────────
    report = {
        "report_id": str(uuid.uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "debate": {
            "debate_id": debate_id,
            "topic": debate.get("topic"),
            "status": debate.get("status"),
            "winner": debate.get("winner"),
            "quality_score": debate.get("quality_score"),
            "total_rounds": debate.get("total_rounds"),
            "created_at": debate.get("created_at"),
            "completed_at": debate.get("completed_at"),
        },
        "sub_debates": enriched_subs,
        "summary": _build_summary(debate, enriched_subs),
    }

    return report


def _build_summary(debate: dict, sub_debates: list[dict]) -> dict[str, Any]:
    total_rounds = sum(len(s.get("rounds", [])) for s in sub_debates)
    winners = [s.get("winner") for s in sub_debates if s.get("winner")]
    debater_a_wins = winners.count("debater_a")
    debater_b_wins = winners.count("debater_b")
    ties = winners.count("tie")

    return {
        "total_sub_debates": len(sub_debates),
        "total_rounds": total_rounds,
        "debater_a_wins": debater_a_wins,
        "debater_b_wins": debater_b_wins,
        "ties": ties,
        "overall_winner": debate.get("winner", "unknown"),
        "quality_score": debate.get("quality_score"),
    }