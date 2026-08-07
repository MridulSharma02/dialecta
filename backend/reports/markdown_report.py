from __future__ import annotations
from typing import Any


def generate_markdown_report(report: dict[str, Any]) -> str:
    overview = report.get("overview", {})
    summary = report.get("summary", {})
    lines: list[str] = []

    # ── Header ──────────────────────────────────────────────────
    lines.append("# DIALECTA Debate Report")
    lines.append("")
    lines.append(f"**Report ID:** {report['report_id']}")
    lines.append(f"**Generated:** {report['generated_at']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Section 1: Overview ─────────────────────────────────────
    lines.append("## 1. Overview")
    lines.append("")
    lines.append(f"**Topic:** {overview.get('topic', 'N/A')}")
    lines.append(f"**Status:** {overview.get('status', 'N/A')}")
    lines.append(f"**Overall Winner:** {overview.get('winner', 'N/A')}")
    lines.append(f"**Debater A Score:** {overview.get('overall_score_a', 'N/A')}")
    lines.append(f"**Debater B Score:** {overview.get('overall_score_b', 'N/A')}")
    lines.append(f"**Quality Score:** {overview.get('quality_score', 'N/A')}")
    lines.append(f"**Total Sub-Debates:** {overview.get('total_sub_debates', 'N/A')}")
    lines.append(f"**Total Rounds:** {overview.get('total_rounds', 'N/A')}")
    lines.append(f"**Started:** {overview.get('created_at', 'N/A')}")
    lines.append(f"**Completed:** {overview.get('completed_at', 'N/A')}")
    lines.append("")
    if overview.get("meta_evaluation"):
        lines.append(f"**Conclusion:** {overview.get('meta_evaluation')}")
        lines.append("")
    lines.append("---")
    lines.append("")

    # ── Section 2: Topic Decomposition ──────────────────────────
    lines.append("## 2. Topic Decomposition")
    lines.append("")
    lines.append("| # | Sub-Topic | Stance A | Stance B | Rounds | Winner |")
    lines.append("|---|-----------|----------|----------|--------|--------|")
    for sub in report.get("topic_decomposition", []):
        lines.append(
            f"| {sub.get('index')} "
            f"| {sub.get('sub_topic', 'N/A')} "
            f"| {sub.get('stance_a', 'N/A')} "
            f"| {sub.get('stance_b', 'N/A')} "
            f"| {sub.get('rounds_run', 0)} "
            f"| {sub.get('winner', 'N/A')} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Section 3: Sub-debate Breakdowns ────────────────────────
    lines.append("## 3. Sub-Debate Breakdowns")
    lines.append("")
    for sub in report.get("sub_debates", []):
        lines.append(f"### Sub-Debate {sub.get('index')}: {sub.get('sub_topic', 'N/A')}")
        lines.append("")
        lines.append(f"- **Stance A:** {sub.get('stance_a', 'N/A')}")
        lines.append(f"- **Stance B:** {sub.get('stance_b', 'N/A')}")
        lines.append(f"- **Winner:** {sub.get('winner', 'N/A')}")
        lines.append(f"- **Final Score A:** {sub.get('final_score_a', 'N/A')}")
        lines.append(f"- **Final Score B:** {sub.get('final_score_b', 'N/A')}")
        lines.append(f"- **Rounds Run:** {sub.get('rounds_run', 0)}")
        lines.append("")

        for r in sub.get("rounds", []):
            lines.append(f"#### Round {r.get('round_number')}")
            lines.append("")
            lines.append(f"**Scores:** A: {r.get('score_a', 'N/A')} | B: {r.get('score_b', 'N/A')} | Winner: {r.get('winner', 'N/A')}")
            lines.append("")
            if r.get("key_insight"):
                lines.append(f"**Key Insight:** {r.get('key_insight')}")
                lines.append("")
            if r.get("fact_context"):
                lines.append(f"**Fact Context:** {r.get('fact_context')}")
                lines.append("")
            lines.append("**Debater A Argument:**")
            lines.append("")
            lines.append(f"> {r.get('argument_a', '')}")
            lines.append("")
            lines.append("**Debater B Argument:**")
            lines.append("")
            lines.append(f"> {r.get('argument_b', '')}")
            lines.append("")
            if r.get("bias_flags"):
                lines.append(f"**Bias Flags:** {', '.join(r.get('bias_flags', []))}")
                lines.append("")
            if r.get("devils_advocate"):
                lines.append(f"**Devil's Advocate:** {r.get('devils_advocate')}")
                lines.append("")
            if r.get("rubric_changes"):
                lines.append(f"**Rubric Changes:** {r.get('rubric_changes')}")
                lines.append("")
            if r.get("summary"):
                lines.append(f"**Round Summary:** {r.get('summary')}")
                lines.append("")
            if r.get("audience_reaction"):
                lines.append(f"**Audience Reaction:** {r.get('audience_reaction')}")
                lines.append("")
            lines.append(f"**Novelty Score:** {r.get('novelty_score', 1.0):.2f}")
            if r.get("is_repetitive"):
                lines.append("⚠️ *This round was flagged as repetitive.*")
            lines.append("")

    lines.append("---")
    lines.append("")

    # ── Section 4: System Self-improvement Log ───────────────────
    lines.append("## 4. System Self-Improvement Log")
    lines.append("")
    improvement_log = report.get("improvement_log", [])
    if improvement_log:
        for entry in improvement_log:
            etype = entry.get("type")
            if etype == "rubric_update":
                lines.append(f"- **[Round {entry.get('round_number')} — Rubric Update]** {entry.get('sub_topic')} — Changes: {entry.get('changes')}")
            elif etype == "devils_advocate":
                lines.append(f"- **[Round {entry.get('round_number')} — Devil's Advocate]** {entry.get('sub_topic')} — Score gap triggered intervention. Advice: {entry.get('advice')}")
            elif etype == "repetition_detected":
                lines.append(f"- **[Round {entry.get('round_number')} — Repetition]** {entry.get('sub_topic')} — Novelty score: {entry.get('novelty_score', 1.0):.2f}")
    else:
        lines.append("*No system interventions recorded.*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Section 5: Meta Evaluation ───────────────────────────────
    lines.append("## 5. Meta-Evaluation")
    lines.append("")
    meta = report.get("meta_evaluation", {})
    lines.append(f"**Quality Score:** {meta.get('quality_score', 'N/A')}")
    lines.append(f"**Overall Score A:** {meta.get('overall_score_a', 'N/A')}")
    lines.append(f"**Overall Score B:** {meta.get('overall_score_b', 'N/A')}")
    lines.append("")
    if meta.get("evaluation"):
        lines.append(meta.get("evaluation"))
    else:
        lines.append("*No meta-evaluation recorded.*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Section 6: Final Verdict ─────────────────────────────────
    lines.append("## 6. Final Verdict")
    lines.append("")
    verdict = report.get("final_verdict", {})
    lines.append(f"**Overall Winner:** {verdict.get('winner', 'N/A')}")
    lines.append(f"**Score A:** {verdict.get('overall_score_a', 'N/A')}")
    lines.append(f"**Score B:** {verdict.get('overall_score_b', 'N/A')}")
    lines.append("")
    lines.append("| Sub-Topic | Winner | Score A | Score B |")
    lines.append("|-----------|--------|---------|---------|")
    for s in verdict.get("sub_debate_results", []):
        lines.append(
            f"| {s.get('sub_topic', 'N/A')} "
            f"| {s.get('winner', 'N/A')} "
            f"| {s.get('final_score_a', 'N/A')} "
            f"| {s.get('final_score_b', 'N/A')} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Section 7: Transcript Appendix ───────────────────────────
    lines.append("## 7. Transcript Appendix")
    lines.append("")
    for sub in report.get("transcript", []):
        lines.append(f"### {sub.get('sub_topic', 'N/A')}")
        lines.append("")
        for r in sub.get("rounds", []):
            lines.append(f"**Round {r.get('round_number')}**")
            lines.append("")
            lines.append(f"*Debater A:* {r.get('argument_a', '')}")
            lines.append("")
            lines.append(f"*Debater B:* {r.get('argument_b', '')}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by DIALECTA — Multi-Agent AI Debate System*")

    return "\n".join(lines)