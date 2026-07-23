from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BaseEvent:
    type: str
    agent: str
    data: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DebateStartedEvent(BaseEvent):
    type: str = "debate_started"
    agent: str = "orchestrator"


@dataclass
class TopicDecomposedEvent(BaseEvent):
    type: str = "topic_decomposed"
    agent: str = "topic_decomposer"


@dataclass
class SubDebateStartedEvent(BaseEvent):
    type: str = "sub_debate_started"
    agent: str = "orchestrator"


@dataclass
class RoundStartedEvent(BaseEvent):
    type: str = "round_started"
    agent: str = "orchestrator"


@dataclass
class RoundCompleteEvent(BaseEvent):
    type: str = "round_complete"
    agent: str = "orchestrator"


@dataclass
class SubDebateCompleteEvent(BaseEvent):
    type: str = "sub_debate_complete"
    agent: str = "orchestrator"


@dataclass
class DebateCompleteEvent(BaseEvent):
    type: str = "debate_complete"
    agent: str = "orchestrator"


@dataclass
class FactCheckCompleteEvent(BaseEvent):
    type: str = "fact_check_complete"
    agent: str = "fact_checker"


@dataclass
class ArgumentSubmittedEvent(BaseEvent):
    type: str = "argument_submitted"
    agent: str = "debater_a"


@dataclass
class BiasFlagsRaisedEvent(BaseEvent):
    type: str = "bias_flags_raised"
    agent: str = "bias_detector"


@dataclass
class ArgumentRevisedEvent(BaseEvent):
    type: str = "argument_revised"
    agent: str = "debater_a"


@dataclass
class JudgeScoresEvent(BaseEvent):
    type: str = "judge_scores"
    agent: str = "judge"


@dataclass
class CriticUpdatedRubricEvent(BaseEvent):
    type: str = "critic_updated_rubric"
    agent: str = "critic"


@dataclass
class DevilsAdvocateFiredEvent(BaseEvent):
    type: str = "devils_advocate_fired"
    agent: str = "devils_advocate"


@dataclass
class MemoryStoredEvent(BaseEvent):
    type: str = "memory_stored"
    agent: str = "memory_agent"


@dataclass
class NoveltyScoreEvent(BaseEvent):
    type: str = "novelty_score"
    agent: str = "memory_agent"


@dataclass
class RoundSummaryEvent(BaseEvent):
    type: str = "round_summary"
    agent: str = "summariser"


@dataclass
class AudienceReactedEvent(BaseEvent):
    type: str = "audience_reacted"
    agent: str = "audience_agent"


@dataclass
class ReportGeneratingEvent(BaseEvent):
    type: str = "report_generating"
    agent: str = "orchestrator"


@dataclass
class ReportReadyEvent(BaseEvent):
    type: str = "report_ready"
    agent: str = "orchestrator"


@dataclass
class AgentDegradedEvent(BaseEvent):
    type: str = "agent_degraded"
    agent: str = "orchestrator"


@dataclass
class FallbackUsedEvent(BaseEvent):
    type: str = "fallback_used"
    agent: str = "orchestrator"


@dataclass
class CheckpointSavedEvent(BaseEvent):
    type: str = "checkpoint_saved"
    agent: str = "orchestrator"


@dataclass
class DebateResumedEvent(BaseEvent):
    type: str = "debate_resumed"
    agent: str = "orchestrator"


@dataclass
class RateLimitWarningEvent(BaseEvent):
    type: str = "rate_limit_warning"
    agent: str = "orchestrator"


@dataclass
class ErrorEvent(BaseEvent):
    type: str = "error"
    agent: str = "orchestrator"


def make_event(event_type: str, agent: str, **data_kwargs) -> dict:
    return BaseEvent(type=event_type, agent=agent, data=data_kwargs).to_dict()