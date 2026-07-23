"""Deterministic workflow policy used by the engineering team documentation and tests."""

from dataclasses import dataclass
import re
from typing import Any, Mapping


RISK_LEVELS = ("LOW", "MEDIUM", "HIGH")

LOW_RISK_SIGNALS = (
    "documentation", "docs", "internal tooling", "formatting",
    "behavior-preserving refactor", "mechanical refactor", "cleanup",
)

# These signals are deliberately explicit and evaluated in priority order.  A task that
# matches more than one tier receives the highest applicable risk tier.
HIGH_RISK_SIGNALS = (
    "authentication", "authorization", "auth", "payment", "payments", "pii",
    "personal data", "secret", "credential", "production infrastructure",
    "production infra", "data migration", "database migration", "external api",
    "public api", "breaking api", "security", "security audit", "security vulnerability",
    "destructive", "data deletion", "incident",
)
MEDIUM_RISK_SIGNALS = (
    "feature", "schema", "database", "api", "integration", "background job",
    "business logic", "bug fix", "bug", "dependency", "configuration change",
)

HIGH_EFFORT_SIGNALS = (
    "ambiguous", "cross-cutting", "distributed", "concurrency", "migration",
    "architecture", "tradeoff", "multiple services", "unknown behavior",
)
MEDIUM_EFFORT_SIGNALS = (
    "feature", "schema", "api", "integration", "bug", "refactor",
)


@dataclass(frozen=True)
class TaskAssessment:
    """Risk and reasoning effort are intentionally independent dimensions."""

    risk: str
    reasoning_effort: str
    signals: tuple[str, ...] = ()


def _text(task: Any) -> str:
    if isinstance(task, Mapping):
        values = [str(task.get(key, "")) for key in ("title", "objective", "description", "scope")]
        return " ".join(values).lower()
    return str(task).lower()


def _matches(text: str, signals: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(signal for signal in signals if re.search(r"(?<!\w)" + re.escape(signal) + r"(?!\w)", text))


def classify_risk(task: Any) -> str:
    """Return LOW, MEDIUM, or HIGH using an explicit, stable signal table."""
    text = _text(task)
    if _matches(text, HIGH_RISK_SIGNALS):
        return "HIGH"
    if _matches(text, MEDIUM_RISK_SIGNALS):
        return "MEDIUM"
    if _matches(text, LOW_RISK_SIGNALS):
        return "LOW"
    # Unknown scope is not assumed safe; project-manager must bound it.
    return "MEDIUM"


def classify_reasoning_effort(task: Any) -> str:
    """Estimate reasoning effort without changing the impact/risk classification."""
    text = _text(task)
    if _matches(text, HIGH_EFFORT_SIGNALS):
        return "HIGH"
    if _matches(text, MEDIUM_EFFORT_SIGNALS):
        return "MEDIUM"
    return "LOW"


def assess_task(task: Any) -> TaskAssessment:
    text = _text(task)
    return TaskAssessment(
        risk=classify_risk(text),
        reasoning_effort=classify_reasoning_effort(text),
        signals=_matches(text, HIGH_RISK_SIGNALS) + _matches(text, MEDIUM_RISK_SIGNALS),
    )


# Backwards-friendly name for callers that describe the operation as task classification.
classify_task = classify_risk


def delegation_policy(risk: str) -> dict[str, Any]:
    """Return the hard delegation limits and gates for a risk tier."""
    risk = risk.upper()
    if risk not in RISK_LEVELS:
        raise ValueError(f"Unsupported risk tier: {risk}")
    if risk == "LOW":
        return {
            "max_sub_agents": 0,
            "parallel_read_only_checks": False,
            "required_gates": ("GATE-1",),
            "stop_condition": "one focused inspection and one verification pass are complete",
        }
    if risk == "MEDIUM":
        return {
            "max_sub_agents": 1,
            "parallel_read_only_checks": True,
            "required_gates": ("GATE-1", "GATE-2"),
            "stop_condition": "the focused specialist reduces total effort and its checkable output is consumed",
        }
    return {
        "max_sub_agents": None,
        "parallel_read_only_checks": True,
        "required_gates": ("GATE-0", "GATE-1", "GATE-2", "GATE-3"),
        "stop_condition": "all required gates pass and human review is recorded",
    }


HIGH_FLOW = (
    "research",
    "security-analyst (GATE-0 threat model)",
    "architecture-engineer",
    "implementation",
    "tester",
    "QA",
    "security-analyst (GATE-3)",
)


def retry_allowed(attempts: int) -> bool:
    """Allow at most two attempts; a third attempt must be an escalation."""
    return attempts < 2
