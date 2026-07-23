import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    OK = "ok"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class AgentContext:
    debate_id: str
    user_id: str
    topic: str
    sub_topic: str
    round_number: int
    stance_a: str
    stance_b: str
    argument_a: Optional[str] = None
    argument_b: Optional[str] = None
    fact_context: Optional[str] = None
    bias_flags: Optional[list] = field(default_factory=list)
    rubric: Optional[dict] = None
    round_history: Optional[list] = field(default_factory=list)
    memory_context: Optional[str] = None
    score_history: Optional[list] = field(default_factory=list)
    audience_persona: Optional[str] = "general public"


@dataclass
class AgentResult:
    agent_name: str
    status: AgentStatus
    data: Any
    error: Optional[str] = None
    fallback_used: bool = False


class BaseAgent(ABC):
    def __init__(self, name: str, max_retries: int = 3):
        self.name = name
        self.max_retries = max_retries
        self.status = AgentStatus.OK

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        pass

    async def run_with_retry(self, context: AgentContext) -> AgentResult:
        delays = [1, 2, 4]
        last_error = None

        for attempt in range(self.max_retries):
            try:
                result = await self.run(context)
                self.status = AgentStatus.OK
                return result
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[{self.name}] Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(delays[attempt])

        self.status = AgentStatus.DEGRADED
        logger.error(f"[{self.name}] All {self.max_retries} attempts failed.")
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.DEGRADED,
            data=None,
            error=f"Agent degraded after {self.max_retries} attempts: {last_error}"
        )