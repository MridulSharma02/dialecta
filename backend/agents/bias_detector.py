import logging
from agents.base import BaseAgent, AgentContext, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

# These are the fallacy types we check for
FALLACY_LABELS = [
    "ad hominem attack",
    "false dichotomy",
    "emotional manipulation",
    "slippery slope fallacy",
    "straw man argument",
    "appeal to authority without evidence",
]

# Threshold — if confidence is above this, we flag it
FLAG_THRESHOLD = 0.6


def _load_classifier():
    """Load the HuggingFace classifier lazily so startup is fast."""
    import os
    if os.getenv("ENVIRONMENT") == "production":
        logger.warning("[BiasDetector] Skipping model load in production (memory constraint).")
        return None
    try:
        from transformers import pipeline
        classifier = pipeline(
            "zero-shot-classification",
            model="cross-encoder/nli-MiniLM2-L6-H768",
            device=-1,  # CPU only
        )
        logger.info("[BiasDetector] Model loaded successfully.")
        return classifier
    except Exception as e:
        logger.error(f"[BiasDetector] Failed to load model: {e}")
        return None


# Module-level classifier — loaded once, reused forever
_classifier = None


def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = _load_classifier()
    return _classifier


def _check_argument(text: str) -> list[str]:
    """Run zero-shot classification and return flagged fallacy labels."""
    clf = get_classifier()
    if clf is None:
        return []

    try:
        result = clf(text, candidate_labels=FALLACY_LABELS, multi_label=True)
        flags = [
            label
            for label, score in zip(result["labels"], result["scores"])
            if score >= FLAG_THRESHOLD
        ]
        return flags
    except Exception as e:
        logger.warning(f"[BiasDetector] Classification error: {e}")
        return []


class BiasDetector(BaseAgent):
    def __init__(self):
        super().__init__(name="BiasDetector")

    async def run(self, context: AgentContext) -> AgentResult:
        flags_a = []
        flags_b = []

        if context.argument_a:
            flags_a = _check_argument(context.argument_a)
            if flags_a:
                logger.info(f"[BiasDetector] Debater A flagged: {flags_a}")

        if context.argument_b:
            flags_b = _check_argument(context.argument_b)
            if flags_b:
                logger.info(f"[BiasDetector] Debater B flagged: {flags_b}")

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.OK,
            data={
                "flags_a": flags_a,
                "flags_b": flags_b,
                "any_flags": bool(flags_a or flags_b),
            },
        )