"""Public models for agent results and operational traces."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

class AgentIntent(str, Enum):
    """Supported top-level user intents."""

    POLICY_QUESTION = "policy_question"
    PTO_GUIDANCE = "pto_guidance"
    REMOTE_WORK_ELIGIBILITY = "remote_work_eligibility"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class TraceEvent:
    """One observable orchestration event."""

    step: str
    status: str
    selected_tool: str | None = None
    tool_arguments: dict[str, Any] = field(default_factory=dict)
    tool_output: dict[str, Any] = field(default_factory=dict)
    policy_sources: tuple[dict[str, Any], ...] = ()
    decision_basis: str | None = None
    escalation_decision: str | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the event into JSON-compatible data."""

        return {
            "timestamp": self.timestamp,
            "step": self.step,
            "status": self.status,
            "selected_tool": self.selected_tool,
            "tool_arguments": dict(self.tool_arguments),
            "tool_output": dict(self.tool_output),
            "policy_sources": [
                dict(source) for source in self.policy_sources
            ],
            "decision_basis": self.decision_basis,
            "escalation_decision": self.escalation_decision,
        }

@dataclass(frozen=True)
class AgentResult:
    """Final agent response plus its operational trace."""

    intent: AgentIntent
    answer: str
    trace: tuple[TraceEvent, ...]
    answer_basis: tuple[str, ...] = ()
    requires_confirmation: bool = False
    escalation_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert the complete result into JSON-compatible data."""

        return {
            "intent": self.intent.value,
            "answer": self.answer,
            "answer_basis": list(self.answer_basis),
            "requires_confirmation": self.requires_confirmation,
            "escalation_required": self.escalation_required,
            "trace": [event.to_dict() for event in self.trace],
        }
