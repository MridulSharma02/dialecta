import json
import logging
from agents.base import BaseAgent, AgentContext, AgentResult, AgentStatus
from core.llm_clients import FallbackLLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a meta-evaluator of debate judging rubrics. Review the judge's scoring history. Identify bias patterns. Rewrite the rubric to correct them.
Return only valid JSON with no extra text:
{"updated_rubric": {"criteria": [{"name": "logic", "weight": 0.30, "description": "...", "scoring_guide": "..."}]}, "changes_made": ["change 1"], "reasoning": "paragraph"}"""


class Critic(BaseAgent):
    def __init__(self):
        super().__init__(name="Critic")
        self.client = FallbackLLMClient()

    async def run(self, context: AgentContext) -> AgentResult:
        history_str = "\n".join(
            f"Round {i+1}: A={r.get('total_a')} B={r.get('total_b')} Winner={r.get('winner')}"
            for i, r in enumerate(context.score_history or [])
        )
        user_prompt = f"Sub-topic: {context.sub_topic}\nScore history:\n{history_str}\n\nReview and rewrite the rubric."

        try:
            raw, fallback_used = await self.client.complete(SYSTEM_PROMPT, user_prompt, temperature=0.3)
            clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            parsed = json.loads(clean)
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.OK,
                data=parsed,
                fallback_used=fallback_used,
            )
        except Exception as e:
            logger.error(f"[Critic] Failed: {e}")
            return AgentResult(agent_name=self.name, status=AgentStatus.DEGRADED, data=None, error=str(e))