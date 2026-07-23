import logging
import chromadb
from chromadb.config import Settings
from agents.base import BaseAgent, AgentContext, AgentResult, AgentStatus
from config import get_settings
app_settings = get_settings()

logger = logging.getLogger(__name__)

NOVELTY_THRESHOLD = 0.3


def _get_chroma_client():
    return chromadb.PersistentClient(
        path=app_settings.CHROMADB_PATH,
        settings=Settings(anonymized_telemetry=False),
    )


def _collection_name(debate_id: str, debater_id: str) -> str:
    safe = debate_id.replace("-", "")[:36]
    return f"debate_{safe}_{debater_id}"


class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MemoryAgent")

    def _get_or_create_collection(self, client, name: str):
        try:
            return client.get_collection(name)
        except Exception:
            return client.create_collection(name)

    async def store_arguments(self, context: AgentContext) -> None:
        """Store round arguments into ChromaDB."""
        try:
            client = _get_chroma_client()

            if context.argument_a:
                col_a = self._get_or_create_collection(
                    client, _collection_name(context.debate_id, "A")
                )
                col_a.add(
                    documents=[context.argument_a],
                    ids=[f"round_{context.round_number}"],
                )

            if context.argument_b:
                col_b = self._get_or_create_collection(
                    client, _collection_name(context.debate_id, "B")
                )
                col_b.add(
                    documents=[context.argument_b],
                    ids=[f"round_{context.round_number}"],
                )

            logger.info(f"[MemoryAgent] Stored round {context.round_number} arguments.")
        except Exception as e:
            logger.warning(f"[MemoryAgent] Store failed: {e}")

    async def retrieve_history(self, debate_id: str, debater_id: str) -> str:
        """Retrieve all past arguments for a debater as a single string."""
        try:
            client = _get_chroma_client()
            name = _collection_name(debate_id, debater_id)
            col = self._get_or_create_collection(client, name)
            results = col.get()
            docs = results.get("documents", [])
            if not docs:
                return ""
            return "\n\n".join(f"Round {i+1}: {d}" for i, d in enumerate(docs))
        except Exception as e:
            logger.warning(f"[MemoryAgent] Retrieve failed: {e}")
            return ""

    async def novelty_check(self, context: AgentContext) -> float:
        """
        Check how novel the latest arguments are vs all previous ones.
        Returns a score 0.0-1.0. Below NOVELTY_THRESHOLD = repetitive debate.
        """
        try:
            client = _get_chroma_client()
            scores = []

            for debater_id, argument in [("A", context.argument_a), ("B", context.argument_b)]:
                if not argument:
                    continue
                name = _collection_name(context.debate_id, debater_id)
                col = self._get_or_create_collection(client, name)

                # Need at least 2 documents to compare
                existing = col.get()
                if len(existing.get("documents", [])) < 2:
                    scores.append(1.0)
                    continue

                results = col.query(query_texts=[argument], n_results=1)
                distances = results.get("distances", [[]])
                if distances and distances[0]:
                    # Distance 0 = identical, distance 2 = very different
                    # Normalise to 0-1 novelty score
                    novelty = min(distances[0][0] / 2.0, 1.0)
                    scores.append(novelty)

            return sum(scores) / len(scores) if scores else 1.0

        except Exception as e:
            logger.warning(f"[MemoryAgent] Novelty check failed: {e}")
            return 1.0  # Assume novel if check fails

    async def run(self, context: AgentContext) -> AgentResult:
        """Store arguments and return novelty score."""
        novelty = await self.novelty_check(context)
        await self.store_arguments(context)

        is_repetitive = novelty < NOVELTY_THRESHOLD
        if is_repetitive:
            logger.info(f"[MemoryAgent] Repetition detected. Novelty={novelty:.2f}")

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.OK,
            data={
                "novelty_score": novelty,
                "is_repetitive": is_repetitive,
            },
        )