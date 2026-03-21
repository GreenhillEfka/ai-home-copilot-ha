"""
PS-177: AgentErrorEnvelope — Structured error schema for agent tool calls.
JSON Schema: pilotsuite_ops/schemas/agent_error_envelope.schema.json
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ErrorType(Enum):
    TRANSIENT = "TRANSIENT"
    RATE_LIMIT = "RATE_LIMIT"
    SERVER_ERROR = "SERVER_ERROR"
    CLIENT_ERROR = "CLIENT_ERROR"
    AUTH_ERROR = "AUTH_ERROR"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CIRCUIT_OPEN = "CIRCUIT_OPEN"
    UNKNOWN = "UNKNOWN"


class SuggestedAction(Enum):
    WAIT_AND_RETRY = "wait_and_retry"
    FALLBACK_MODEL = "fallback_model"
    FALLBACK_TOOL = "fallback_tool"
    DEGRADE_GRACEFULLY = "degrade_gracefully"
    ALERT_AND_ABORT = "alert_and_abort"
    CIRCUIT_OPEN_SKIP = "circuit_open_skip"
    NO_RETRY_ABORT = "no_retry_abort"


@dataclass
class AgentErrorEnvelope:
    """
    Structured error envelope for PilotSuite agent tool calls.
    Enables automated recovery without human intervention.
    """
    error_type: str
    code: str
    retryable: bool
    user_message: str
    suggested_action: str = "no_retry_abort"
    retry_after_sec: float | None = None
    recovery_hint: str | None = None
    tool_name: str | None = None
    attempt: int | None = None
    max_attempts: int | None = None
    latency_ms: float | None = None
    timestamp: str | None = None
    details: dict[str, Any] | None = None
    error_id: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.error_id is None:
            self.error_id = str(uuid.uuid4())[:8]

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_id": self.error_id,
            "error_type": self.error_type,
            "code": self.code,
            "retryable": self.retryable,
            "retry_after_sec": self.retry_after_sec,
            "suggested_action": self.suggested_action,
            "user_message": self.user_message,
            "recovery_hint": self.recovery_hint,
            "tool_name": self.tool_name,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentErrorEnvelope:
        return cls(
            error_type=data["error_type"],
            code=data["code"],
            retryable=data["retryable"],
            user_message=data["user_message"],
            **{k: v for k, v in data.items() if k in cls.__dataclass_fields__},
        )

    def with_retry_context(self, attempt: int, max_attempts: int) -> AgentErrorEnvelope:
        return AgentErrorEnvelope(
            error_type=self.error_type,
            code=self.code,
            retryable=self.retryable,
            user_message=self.user_message,
            suggested_action=self.suggested_action,
            retry_after_sec=self.retry_after_sec,
            recovery_hint=self.recovery_hint,
            tool_name=self.tool_name,
            attempt=attempt,
            max_attempts=max_attempts,
            timestamp=self.timestamp,
            details=self.details,
        )

    @classmethod
    def circuit_open(cls, tool_name: str, consecutive_failures: int = 0, recovery_hint: str = "") -> AgentErrorEnvelope:
        return cls(
            error_type="CIRCUIT_OPEN",
            code="CIRCUIT_OPEN",
            retryable=False,
            suggested_action="circuit_open_skip",
            user_message=f"Circuit breaker OPEN for tool '{tool_name}'. Do not retry.",
            recovery_hint=recovery_hint or f"Circuit consecutive_failures={consecutive_failures}. Wait 30s or reset.",
            tool_name=tool_name,
        )

    @classmethod
    def rate_limited(cls, tool_name: str, retry_after_sec: float, attempt: int, max_attempts: int) -> AgentErrorEnvelope:
        return cls(
            error_type="RATE_LIMIT",
            code="RATE_LIMIT",
            retryable=True,
            retry_after_sec=retry_after_sec,
            suggested_action="wait_and_retry",
            user_message=f"Rate limited on {tool_name}. Retry after {retry_after_sec:.0f}s.",
            tool_name=tool_name,
            attempt=attempt,
            max_attempts=max_attempts,
        )

    @classmethod
    def timeout(cls, tool_name: str, latency_ms: float, attempt: int, max_attempts: int) -> AgentErrorEnvelope:
        return cls(
            error_type="TIMEOUT",
            code="TIMEOUT",
            retryable=True,
            suggested_action="wait_and_retry",
            user_message=f"Timeout ({latency_ms:.0f}ms) calling {tool_name}.",
            tool_name=tool_name,
            attempt=attempt,
            max_attempts=max_attempts,
            latency_ms=latency_ms,
        )

    @classmethod
    def unknown(cls, tool_name: str, exception: Exception, attempt: int, max_attempts: int) -> AgentErrorEnvelope:
        return cls(
            error_type="UNKNOWN",
            code="UNKNOWN",
            retryable=False,
            suggested_action="no_retry_abort",
            user_message=f"Unexpected error calling {tool_name}: {str(exception)[:100]}",
            recovery_hint=f"Exception type: {type(exception).__name__}",
            tool_name=tool_name,
            attempt=attempt,
            max_attempts=max_attempts,
            details={"exception_type": type(exception).__name__, "exception_str": str(exception)[:500]},
        )
