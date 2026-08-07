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

    # ── 2. Sub-debates ──────────────────────────────────────────
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

    # ── 4. Build summary ────────────────────────────────────────
    summary = _build_summary(debate, enriched_subs)

    # ── 5. Build self-improvement log ───────────────────────────
    improvement_log = _build_improvement_log(enriched_subs)

    # ── 6. Assemble final report dict ───────────────────────────
    report = {
        "report_id": str(uuid.uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),

        # Section 1 — Overview
        "overview": {
            "debate_id": debate_id,
            "topic": debate.get("topic"),
            "status": debate.get("status"),
            "winner": debate.get("winner"),
            "overall_score_a": debate.get("overall_score_a"),
            "overall_score_b": debate.get("overall_score_b"),
            "quality_score": debate.get("quality_score"),
            "total_rounds": debate.get("total_rounds"),
            "total_sub_debates": len(enriched_subs),
            "created_at": debate.get("created_at"),
            "completed_at": debate.get("completed_at"),
            "meta_evaluation": debate.get("meta_evaluation", ""),
        },

        # Section 2 — Topic Decomposition
        "topic_decomposition": [
            {
                "index": i + 1,
                "sub_topic": sub.get("sub_topic"),
                "stance_a": sub.get("stance_a"),
                "stance_b": sub.get("stance_b"),
                "rounds_run": sub.get("rounds_run"),
                "winner": sub.get("winner"),
                "final_score_a": sub.get("final_score_a"),
                "final_score_b": sub.get("final_score_b"),
            }
            for i, sub in enumerate(enriched_subs)
        ],

        # Section 3 — Sub-debate Breakdowns
        "sub_debates": [
            {
                "index": i + 1,
                "sub_topic": sub.get("sub_topic"),
                "stance_a": sub.get("stance_a"),
                "stance_b": sub.get("stance_b"),
                "winner": sub.get("winner"),
                "final_score_a": sub.get("final_score_a"),
                "final_score_b": sub.get("final_score_b"),
                "rounds_run": sub.get("rounds_run"),
                "rounds": [
                    {
                        "round_number": r.get("round_number"),
                        "argument_a": r.get("argument_a", ""),
                        "argument_b": r.get("argument_b", ""),
                        "score_a": r.get("score_a"),
                        "score_b": r.get("score_b"),
                        "winner": (r.get("judge_reasoning") or {}).get("winner", ""),
                        "key_insight": (r.get("judge_reasoning") or {}).get("key_insight", ""),
                        "judge_reasoning": r.get("judge_reasoning", {}),
                        "summary": r.get("summary", ""),
                        "audience_reaction": r.get("audience_reaction", ""),
                        "bias_flags": r.get("bias_flags", []),
                        "fact_context": r.get("fact_context", ""),
                        "devils_advocate": r.get("devils_advocate"),
                        "rubric_changes": r.get("rubric_changes"),
                        "novelty_score": r.get("novelty_score", 1.0),
                        "is_repetitive": r.get("is_repetitive", False),
                    }
                    for r in sub.get("rounds", [])
                ],
            }
            for i, sub in enumerate(enriched_subs)
        ],

        # Section 4 — System Self-improvement Log
        "improvement_log": improvement_log,

        # Section 5 — Meta Evaluation
        "meta_evaluation": {
            "evaluation": debate.get("meta_evaluation", ""),
            "quality_score": debate.get("quality_score"),
            "overall_score_a": debate.get("overall_score_a"),
            "overall_score_b": debate.get("overall_score_b"),
        },

        # Section 6 — Final Verdict
        "final_verdict": {
            "winner": debate.get("winner"),
            "overall_score_a": debate.get("overall_score_a"),
            "overall_score_b": debate.get("overall_score_b"),
            "sub_debate_results": [
                {
                    "sub_topic": sub.get("sub_topic"),
                    "winner": sub.get("winner"),
                    "final_score_a": sub.get("final_score_a"),
                    "final_score_b": sub.get("final_score_b"),
                }
                for sub in enriched_subs
            ],
        },

        # Section 7 — Transcript Appendix (verbatim arguments)
        "transcript": [
            {
                "sub_topic": sub.get("sub_topic"),
                "rounds": [
                    {
                        "round_number": r.get("round_number"),
                        "argument_a": r.get("argument_a", ""),
                        "argument_b": r.get("argument_b", ""),
                    }
                    for r in sub.get("rounds", [])
                ],
            }
            for sub in enriched_subs
        ],

        # Legacy summary field
        "summary": summary,
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


def _build_improvement_log(sub_debates: list[dict]) -> list[dict]:
    log = []
    for sub in sub_debates:
        for r in sub.get("rounds", []):
            entry = {}

            if r.get("rubric_changes"):
                entry["type"] = "rubric_update"
                entry["sub_topic"] = sub.get("sub_topic")
                entry["round_number"] = r.get("round_number")
                entry["changes"] = r.get("rubric_changes")
                log.append(entry)

            if r.get("devils_advocate"):
                log.append({
                    "type": "devils_advocate",
                    "sub_topic": sub.get("sub_topic"),
                    "round_number": r.get("round_number"),
                    "advice": r.get("devils_advocate"),
                    "score_a": r.get("score_a"),
                    "score_b": r.get("score_b"),
                })

            if r.get("is_repetitive"):
                log.append({
                    "type": "repetition_detected",
                    "sub_topic": sub.get("sub_topic"),
                    "round_number": r.get("round_number"),
                    "novelty_score": r.get("novelty_score"),
                })

    return log