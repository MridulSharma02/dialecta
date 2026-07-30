import logging
from agents.base import BaseAgent, AgentContext, AgentResult, AgentStatus
from core.llm_clients import FallbackLLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a debate summariser. Write a concise 3-4 sentence digest of this debate round. Cover the key arguments made by each side and the round outcome. Plain text only."""


class Summariser(BaseAgent):
    def __init__(self):
        super().__init__(name="Summariser")
        self.client = FallbackLLMClient()

    async def run(self, context: AgentContext) -> AgentResult:
        user_prompt = f"""Sub-topic: {context.sub_topic} — Round {context.round_number}

Debater A ({context.stance_a}):
{context.argument_a}

Debater B ({context.stance_b}):
{context.argument_b}

Write a round digest now."""

        try:
            text, _ = await self.client.complete(SYSTEM_PROMPT, user_prompt, temperature=0.5, prefer_gemini=True)
            return AgentResult(agent_name=self.name, status=AgentStatus.OK, data={"summary": text})
        except Exception as e:
            logger.error(f"[Summariser] Failed: {e}")
            return AgentResult(agent_name=self.name, status=AgentStatus.DEGRADED, data={"summary": ""}, error=str(e))