import logging
from agents.base import BaseAgent, AgentContext, AgentResult, AgentStatus
from core.llm_clients import GeminiClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are reacting to a debate round from the perspective of: {PERSONA}. Write 2-3 sentences expressing your genuine reaction — what persuaded or failed to persuade you and why. Be authentic to the persona. Plain text only."""


class AudienceAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="AudienceAgent")
        self.client = GeminiClient()

    async def run(self, context: AgentContext) -> AgentResult:
        persona = context.audience_persona or "a skeptical member of the general public"
        system = SYSTEM_PROMPT.replace("{PERSONA}", persona)

        user_prompt = f"""Sub-topic: {context.sub_topic} — Round {context.round_number}

Debater A argued: {context.argument_a}
Debater B argued: {context.argument_b}

React now as {persona}."""

        try:
            text = await self.client.complete(system, user_prompt, temperature=0.7)
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.OK,
                data={"reaction": text, "persona": persona},
            )
        except Exception as e:
            logger.error(f"[AudienceAgent] Failed: {e}")
            return AgentResult(agent_name=self.name, status=AgentStatus.DEGRADED, data={"reaction": ""}, error=str(e))