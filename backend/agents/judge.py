import json
import logging
from agents.base import BaseAgent, AgentContext, AgentResult, AgentStatus
from core.llm_clients import FallbackLLMClient

logger = logging.getLogger(__name__)

WEIGHTS = {"logic": 0.30, "evidence": 0.30, "engagement": 0.20, "clarity": 0.10, "originality": 0.10}

SYSTEM_PROMPT = """You are an impartial debate judge. Score each argument 0.0-10.0 per criterion.
Be consistent with previous rounds. 

Return only valid JSON with no extra text, no markdown, no code fences:
{"scores": {"debater_a": {"logic": 0.0, "evidence": 0.0, "engagement": 0.0, "clarity": 0.0, "originality": 0.0}, "debater_b": {"logic": 0.0, "evidence": 0.0, "engagement": 0.0, "clarity": 0.0, "originality": 0.0}}, "reasoning": {"debater_a": "one sentence", "debater_b": "one sentence"}, "round_winner": "debater_a|debater_b|tie", "key_insight": "one sentence"}"""


def _calculate_total(scores: dict, bias_flags: list, fact_penalty: float) -> float:
    total = sum(scores.get(k, 0) * w for k, w in WEIGHTS.items())
    total -= 0.5 * len(bias_flags)
    total -= fact_penalty
    return round(max(0.0, min(10.0, total)), 2)


class Judge(BaseAgent):
    def __init__(self):
        super().__init__(name="Judge")
        self.client = FallbackLLMClient()

    async def run(self, context: AgentContext) -> AgentResult:
        rubric_note = ""
        if context.rubric:
            criteria = context.rubric.get("criteria", [])
            rubric_note = "Updated rubric from Critic:\n" + "\n".join(
                f"- {c['name']} ({c['weight']*100:.0f}%): {c['description']}"
                for c in criteria
            )

        history_note = ""
        if context.score_history:
            history_note = "Previous round scores:\n" + "\n".join(
                f"  Round {i+1}: A={r.get('total_a', '?')} B={r.get('total_b', '?')}"
                for i, r in enumerate(context.score_history)
            )

        user_prompt = f"""Sub-topic: {context.sub_topic}
Round: {context.round_number}

DEBATER A argument (stance: {context.stance_a}):
{context.argument_a}

DEBATER B argument (stance: {context.stance_b}):
{context.argument_b}

{rubric_note}
{history_note}

Score both arguments now."""

        try:
            raw, fallback_used = await self.client.complete(
                system=SYSTEM_PROMPT,
                user=user_prompt,
                temperature=0.3,
            )

            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            parsed = json.loads(clean)
            scores_a = parsed["scores"]["debater_a"]
            scores_b = parsed["scores"]["debater_b"]

            # Python recalculates totals — never trust model math
            total_a = _calculate_total(scores_a, context.bias_flags or [], 0.0)
            total_b = _calculate_total(scores_b, [], 0.0)

            # Determine winner from recalculated totals
            if total_a > total_b:
                winner = "debater_a"
            elif total_b > total_a:
                winner = "debater_b"
            else:
                winner = "tie"

            result_data = {
                "scores_a": scores_a,
                "scores_b": scores_b,
                "total_a": total_a,
                "total_b": total_b,
                "winner": winner,
                "reasoning": parsed.get("reasoning", {}),
                "key_insight": parsed.get("key_insight", ""),
                "fallback_used": fallback_used,
            }

            logger.info(f"[Judge] Round {context.round_number} scored. A={total_a} B={total_b} Winner={winner}")
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.OK,
                data=result_data,
                fallback_used=fallback_used,
            )

        except Exception as e:
            logger.error(f"[Judge] Failed: {e}")
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                data=None,
                error=str(e),
            )