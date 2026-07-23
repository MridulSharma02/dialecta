import json
import logging
from agents.base import BaseAgent, AgentContext, AgentResult, AgentStatus
from core.llm_clients import GeminiClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a debate architect. Break this topic into 2-4 distinct independently debatable sub-topics covering the full complexity of the question.
Return only valid JSON with no extra text, no markdown, no code fences:
{"sub_topics": [{"id": 1, "title": "short title", "question": "full question", "why_included": "one sentence", "suggested_stance_a": "FOR position", "suggested_stance_b": "AGAINST position", "complexity": "philosophical|empirical|legal|ethical|practical"}]}"""


class TopicDecomposer(BaseAgent):
    def __init__(self):
        super().__init__(name="TopicDecomposer")
        self.client = GeminiClient()

    async def run(self, context: AgentContext) -> AgentResult:
        try:
            user_prompt = f"Topic to decompose: {context.topic}"
            raw = await self.client.complete(SYSTEM_PROMPT, user_prompt, temperature=0.5)

            # Strip any accidental markdown fences
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()

            parsed = json.loads(clean)
            sub_topics = parsed.get("sub_topics", [])

            if not sub_topics:
                raise ValueError("No sub_topics returned by model")

            logger.info(f"[TopicDecomposer] Decomposed into {len(sub_topics)} sub-topics")
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.OK,
                data=sub_topics,
            )

        except json.JSONDecodeError as e:
            logger.error(f"[TopicDecomposer] JSON parse error: {e}")
            # Fallback: single sub-topic mirroring the original topic
            fallback = [{
                "id": 1,
                "title": context.topic[:60],
                "question": context.topic,
                "why_included": "Original topic used as fallback",
                "suggested_stance_a": "In favour of the proposition",
                "suggested_stance_b": "Against the proposition",
                "complexity": "philosophical",
            }]
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.DEGRADED,
                data=fallback,
                error=str(e),
            )