import logging
from agents.base import BaseAgent, AgentContext, AgentResult, AgentStatus
from core.llm_clients import FallbackLLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a rigorous academic debater arguing {STANCE} on: {SUB_TOPIC}

Scoring rubric: logic 30%, evidence 30%, engagement with opponent 20%, clarity 10%, originality 10%.

Rules:
- Always engage with your opponent's last argument before making new points
- Cite at least one fact from the provided context if available
- Never repeat arguments you made in previous rounds (history is provided)
- Write 150-250 words
- Never start with "I" or "As an AI"
- Return plain text only, no bullet points, no headers"""


class Debater(BaseAgent):
    def __init__(self, debater_id: str):
        """
        debater_id: "A" or "B"
        """
        super().__init__(name=f"Debater{debater_id}")
        self.debater_id = debater_id
        self.client = FallbackLLMClient()

    async def run(self, context: AgentContext) -> AgentResult:
        stance = context.stance_a if self.debater_id == "A" else context.stance_b
        opponent_arg = context.argument_b if self.debater_id == "A" else context.argument_a

        system = SYSTEM_PROMPT.replace("{STANCE}", stance).replace("{SUB_TOPIC}", context.sub_topic)

        # Build the user prompt with all context
        parts = []

        if context.fact_context:
            parts.append(f"VERIFIED FACTS FROM FACT CHECKER:\n{context.fact_context}")

        if context.memory_context:
            parts.append(f"YOUR PREVIOUS ARGUMENTS (do not repeat these):\n{context.memory_context}")

        if opponent_arg:
            parts.append(f"OPPONENT'S LAST ARGUMENT (you must engage with this):\n{opponent_arg}")

        if context.bias_flags:
            parts.append(f"BIAS WARNING — avoid these flagged patterns: {', '.join(context.bias_flags)}")

        parts.append(f"Round {context.round_number}: Make your argument now.")
        user_prompt = "\n\n".join(parts)

        try:
            text, fallback_used = await self.client.complete(
                system=system,
                user=user_prompt,
                temperature=0.8,
            )

            logger.info(f"[{self.name}] Round {context.round_number} argument generated. Fallback={fallback_used}")
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.OK,
                data={"argument": text, "stance": stance},
                fallback_used=fallback_used,
            )

        except Exception as e:
            logger.error(f"[{self.name}] Failed: {e}")
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                data=None,
                error=str(e),
            )