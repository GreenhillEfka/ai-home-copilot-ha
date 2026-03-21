"""
PS-176: Circuit Breaker Wrapper for OpenClaw Tool Calls

States:
  CLOSED      → normal operation, all requests pass through
  OPEN        → fail fast after threshold (5 consecutive failures or 50% in 60s)
  HALF_OPEN   → after 30s timeout, single probe request to test recovery

Usage:
    cb = ToolCircuitBreaker(tool_name="web_search")
    if cb.can_execute():
        result = cb.execute(my_tool_call, *args)
    else:
        logger.warning("Circuit OPEN for %s — skipping", tool_name)
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, ParamSpec, TypeVar

from utils.agent_error_envelope import AgentErrorEnvelope

P = ParamSpec("P")
T = TypeVar("T")

logger = logging.getLogger(__name__)

LOG_PATH = Path("/config/clawd/pilotsuite_ops/logs/circuit_breaker.jsonl")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitMetrics:
    total_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0
    last_failure_ts: float = 0.0
    last_success_ts: float = 0.0
    state: CircuitState = CircuitState.CLOSED
    half_open_probe_sent: bool = False
    state_since: float = field(default_factory=time.time)

    @property
    def failure_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls

    def is_healthy(self) -> bool:
        return self.state == CircuitState.CLOSED

    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def is_half_open(self) -> bool:
        return self.state == CircuitState.HALF_OPEN

    def to_dict(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "failed_calls": self.failed_calls,
            "consecutive_failures": self.consecutive_failures,
            "failure_rate": round(self.failure_rate, 4),
            "state": self.state.value,
            "state_since": self.state_since,
            "last_failure_ts": self.last_failure_ts,
            "last_success_ts": self.last_success_ts,
        }


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5           # consecutive failures to trip OPEN
    failure_rate_threshold: float = 0.50   # 50% failure rate in window to trip OPEN
    window_seconds: float = 60.0           # rolling window for rate calculation
    half_open_timeout: float = 30.0        # seconds before probing HALF_OPEN
    half_open_max_probes: int = 1          # probes allowed in HALF_OPEN before deciding
    log_transitions: bool = True
    log_path: Path | None = LOG_PATH


def _log_transition(tool_name: str, old: CircuitState, new: CircuitState, metrics: CircuitMetrics, reason: str = "") -> None:
    entry = {
        "ts": time.time(),
        "tool": tool_name,
        "event": "state_change",
        "from": old.value,
        "to": new.value,
        "reason": reason,
        "metrics": metrics.to_dict(),
    }
    if LOG_PATH:
        with open(LOG_PATH, "a") as f:
            f.write(__import__("json").dumps(entry) + "\n")
    logger.info("[PS-176] %s: %s → %s %s", tool_name, old.value, new.value, f"({reason})" if reason else "")


class ToolCircuitBreaker:
    """
    Per-tool circuit breaker for OpenClaw tool calls.

    Thread-safe. Tracks failure rate and consecutive failures.
    Transitions: CLOSED → OPEN (threshold hit) → HALF_OPEN (timeout) → CLOSED|OPEN (probe result)
    """

    def __init__(
        self,
        tool_name: str,
        config: CircuitBreakerConfig | None = None,
    ):
        self.tool_name = tool_name
        self.config = config or CircuitBreakerConfig()
        self._metrics = CircuitMetrics()
        self._lock = threading.RLock()
        self._window: list[tuple[float, bool]] = []  # (ts, success)

    def _check_window(self) -> list[tuple[float, bool]]:
        """Return only entries within the rolling window."""
        cutoff = time.time() - self.config.window_seconds
        self._window = [(ts, ok) for ts, ok in self._window if ts > cutoff]
        return self._window

    def _should_trip_open(self) -> bool:
        """Return True if circuit should transition to OPEN."""
        # Consecutive failures threshold
        if self._metrics.consecutive_failures >= self.config.failure_threshold:
            return True
        # Rolling failure rate threshold
        window = self._check_window()
        if len(window) >= 5:
            rate = sum(1 for _, ok in window if not ok) / len(window)
            if rate >= self.config.failure_rate_threshold:
                return True
        return False

    def can_execute(self) -> bool:
        """True if a request should be allowed through."""
        with self._lock:
            if self._metrics.state == CircuitState.CLOSED:
                return True

            if self._metrics.state == CircuitState.OPEN:
                # Check if half-open timeout has elapsed
                elapsed = time.time() - self._metrics.state_since
                if elapsed >= self.config.half_open_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                    self._metrics.half_open_probe_sent = False
                    return True
                return False

            if self._metrics.state == CircuitState.HALF_OPEN:
                # Allow one probe through
                if not self._metrics.half_open_probe_sent:
                    self._metrics.half_open_probe_sent = True
                    return True
                return False

        return False

    def _transition_to(self, new_state: CircuitState, reason: str = "") -> None:
        old = self._metrics.state
        if old == new_state:
            return
        self._metrics.state = new_state
        self._metrics.state_since = time.time()
        self._metrics.half_open_probe_sent = False
        if self.config.log_transitions:
            _log_transition(self.tool_name, old, new_state, self._metrics, reason)

    def record_success(self) -> None:
        with self._lock:
            self._metrics.total_calls += 1
            self._metrics.consecutive_failures = 0
            self._metrics.last_success_ts = time.time()
            self._window.append((time.time(), True))

            if self._metrics.state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.CLOSED, "probe succeeded")
            elif self._metrics.state == CircuitState.OPEN:
                # Shouldn't happen but safety net
                self._transition_to(CircuitState.CLOSED, "success after open")

    def record_failure(self, error: Exception | AgentErrorEnvelope | None = None) -> None:
        with self._lock:
            self._metrics.total_calls += 1
            self._metrics.consecutive_failures += 1
            self._metrics.last_failure_ts = time.time()
            self._window.append((time.time(), False))

            if self._metrics.state == CircuitState.HALF_OPEN:
                # Probe failed → go back to OPEN
                self._transition_to(CircuitState.OPEN, f"probe failed: {error}")
            elif self._metrics.state == CircuitState.CLOSED:
                if self._should_trip_open():
                    self._transition_to(CircuitState.OPEN, "failure threshold reached")

    def execute(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        """
        Execute a synchronous function through the circuit breaker.
        Raises CircuitOpenError if the circuit is OPEN and should not be probed.
        """
        if not self.can_execute():
            raise CircuitOpenError(f"Circuit OPEN for tool '{self.tool_name}' — fail fast, do not retry")

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as exc:  # noqa: BLE001
            self.record_failure(exc)
            raise

    async def execute_async(self, coro, *args, **kwargs):
        """Async wrapper — record_failure / record_success still use the lock."""
        if not self.can_execute():
            raise CircuitOpenError(f"Circuit OPEN for tool '{self.tool_name}' — fail fast")

        try:
            result = await coro(*args, **kwargs)
            self.record_success()
            return result
        except Exception as exc:  # noqa: BLE001
            self.record_failure(exc)
            raise

    @property
    def state(self) -> CircuitState:
        return self._metrics.state

    @property
    def metrics(self) -> CircuitMetrics:
        return self._metrics

    def get_error_envelope(self, tool_name: str) -> AgentErrorEnvelope:
        """Build a CIRCUIT_OPEN error envelope for this tool."""
        return AgentErrorEnvelope(
            error_type="CIRCUIT_OPEN",
            code="CIRCUIT_OPEN",
            retryable=False,
            suggested_action="circuit_open_skip",
            user_message=f"Circuit breaker OPEN for tool '{tool_name}'. Do not retry — fail fast.",
            recovery_hint=f"Circuit state={self._metrics.state.value}, consecutive_failures={self._metrics.consecutive_failures}",
            tool_name=tool_name,
            timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        )

    def reset(self) -> None:
        """Manually reset circuit to CLOSED (e.g., after manual intervention)."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED, "manual_reset")
            self._metrics.consecutive_failures = 0
            self._window.clear()


class CircuitOpenError(Exception):
    """Raised when a circuit is OPEN and we want to fail fast instead of retry."""
    pass


# ── Global registry for per-tool circuit breakers ──────────────────────────────

_CB_REGISTRY: dict[str, ToolCircuitBreaker] = {}
_REGISTRY_LOCK = threading.Lock()


def get_circuit_breaker(tool_name: str, config: CircuitBreakerConfig | None = None) -> ToolCircuitBreaker:
    """Get or create a circuit breaker for a named tool (singleton per tool_name)."""
    with _REGISTRY_LOCK:
        if tool_name not in _CB_REGISTRY:
            _CB_REGISTRY[tool_name] = ToolCircuitBreaker(tool_name, config)
        return _CB_REGISTRY[tool_name]


def reset_all_circuits() -> None:
    """Reset all circuit breakers in the registry (e.g., after system recovery)."""
    with _REGISTRY_LOCK:
        for cb in _CB_REGISTRY.values():
            cb.reset()


def all_circuit_states() -> dict[str, dict]:
    """Return the state of all registered circuit breakers."""
    with _REGISTRY_LOCK:
        return {name: cb.metrics.to_dict() for name, cb in _CB_REGISTRY.items()}
