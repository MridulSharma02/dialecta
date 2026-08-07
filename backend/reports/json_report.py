from __future__ import annotations
import json
from typing import Any


def generate_json_report(report: dict[str, Any]) -> str:
    output = {
        "dialecta_report": {
            "version": "2.0",
            "report_id": report["report_id"],
            "generated_at": report["generated_at"],

            "overview": report.get("overview", {}),
            "topic_decomposition": report.get("topic_decomposition", []),

            "sub_debates": [
                {
                    "index": sub.get("index"),
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
                            "scores": {
                                "debater_a": r.get("score_a"),
                                "debater_b": r.get("score_b"),
                            },
                            "winner": r.get("winner"),
                            "key_insight": r.get("key_insight"),
                            "judge_reasoning": r.get("judge_reasoning", {}),
                            "argument_a": r.get("argument_a", ""),
                            "argument_b": r.get("argument_b", ""),
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
                for sub in report.get("sub_debates", [])
            ],

            "improvement_log": report.get("improvement_log", []),
            "meta_evaluation": report.get("meta_evaluation", {}),
            "final_verdict": report.get("final_verdict", {}),
            "transcript": report.get("transcript", []),
        }
    }

    return json.dumps(output, indent=2, default=str)