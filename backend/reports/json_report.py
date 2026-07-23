from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any


def generate_json_report(report: dict[str, Any]) -> str:
    """
    Takes the assembled report dict from generator.py and
    returns a formatted JSON string ready to write to a file
    or send as a download.
    """

    output = {
        "dialecta_report": {
            "version": "1.0",
            "report_id": report["report_id"],
            "generated_at": report["generated_at"],
            "debate": report["debate"],
            "summary": report["summary"],
            "sub_debates": [],
            "agent_events": report.get("agent_events", []),
        }
    }

    for sub in report.get("sub_debates", []):
        sub_entry = {
            "sub_debate_id": sub.get("sub_debate_id"),
            "sub_topic": sub.get("sub_topic"),
            "stance_a": sub.get("stance_a"),
            "stance_b": sub.get("stance_b"),
            "winner": sub.get("winner"),
            "rounds_run": sub.get("rounds_run"),
            "rounds": [],
        }

        for rnd in sub.get("rounds", []):
            round_entry = {
                "round_number": rnd.get("round_number"),
                "round_winner": rnd.get("round_winner"),
                "scores": {
                    "debater_a": rnd.get("score_a"),
                    "debater_b": rnd.get("score_b"),
                },
                "key_insight": rnd.get("key_insight"),
                "exit_reason": rnd.get("exit_reason"),
                "arguments": [
                    {
                        "speaker": arg.get("speaker"),
                        "content": arg.get("content"),
                        "created_at": arg.get("created_at"),
                    }
                    for arg in rnd.get("arguments", [])
                ],
            }
            sub_entry["rounds"].append(round_entry)

        output["dialecta_report"]["sub_debates"].append(sub_entry)

    return json.dumps(output, indent=2, default=str)