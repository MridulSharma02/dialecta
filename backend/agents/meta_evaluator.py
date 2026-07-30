import logging
from agents.base import BaseAgent, AgentContext, AgentResult, AgentStatus
from core.llm_clients import FallbackLLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a meta-evaluator assessing the overall quality of a completed debate. Evaluate: argument depth, evidence quality, engagement between debaters, logical coherence, and intellectual progress made. Write 4-5 sentences. End with an overall quality score 1-10. Plain text only."""


class MetaEvaluator(BaseAgent):
    def __init__(self):
        super().__init__(name="MetaEvaluator")
        self.client = FallbackLLMClient()

    async def run(self, context: AgentContext) -> AgentResult:
        score_summary = "\n".join(
            f"Round {i+1}: A={r.get('total_a')} B={r.get('total_b')} Winner={r.get('winner')}"
            for i, r in enumerate(context.score_history or [])
        )

        user_prompt = f"""Topic: {context.topic}
Sub-topic: {context.sub_topic}
Total rounds: {context.round_number}

Score history:
{score_summary}

Provide your overall quality assessment now."""

        try:
            text, _ = await self.client.complete(SYSTEM_PROMPT, user_prompt, temperature=0.5, prefer_gemini=True)

            # Extract numeric quality score from last sentence
            quality_score = 7.0  # default
            for word in text.split():
                try:
                    val = float(word.strip(".,/10"))
                    if 1.0 <= val <= 10.0:
                        quality_score = val
                except ValueError:
                    continue

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.OK,
                data={"evaluation": text, "quality_score": quality_score},
            )
        except Exception as e:
            logger.error(f"[MetaEvaluator] Failed: {e}")
            return AgentResult(agent_name=self.name, status=AgentStatus.DEGRADED, data={"evaluation": "", "quality_score": 0.0}, error=str(e))