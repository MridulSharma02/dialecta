import logging
from agents.base import BaseAgent, AgentContext, AgentResult, AgentStatus
from core.llm_clients import FallbackLLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a debate coach helping the losing debater. Provide 3 sharp, specific arguments or angles they have not yet used. Be direct and tactical. Return plain text only."""


class DevilsAdvocate(BaseAgent):
    def __init__(self):
        super().__init__(name="DevilsAdvocate")
        self.client = FallbackLLMClient()

    async def run(self, context: AgentContext) -> AgentResult:
        # Figure out who is losing
        if not context.score_history:
            return AgentResult(agent_name=self.name, status=AgentStatus.OK, data={"advice": None})

        last = context.score_history[-1]
        total_a = last.get("total_a", 5)
        total_b = last.get("total_b", 5)
        losing_stance = context.stance_a if total_a < total_b else context.stance_b
        losing_debater = "A" if total_a < total_b else "B"

        user_prompt = f"""Sub-topic: {context.sub_topic}
Losing debater is arguing: {losing_stance}
Their last argument: {context.argument_a if losing_debater == 'A' else context.argument_b}
Give them 3 new angles to use in the next round."""

        try:
            text, fallback_used = await self.client.complete(SYSTEM_PROMPT, user_prompt, temperature=0.9)
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.OK,
                data={"advice": text, "for_debater": losing_debater},
                fallback_used=fallback_used,
            )
        except Exception as e:
            logger.error(f"[DevilsAdvocate] Failed: {e}")
            return AgentResult(agent_name=self.name, status=AgentStatus.DEGRADED, data={"advice": None}, error=str(e))