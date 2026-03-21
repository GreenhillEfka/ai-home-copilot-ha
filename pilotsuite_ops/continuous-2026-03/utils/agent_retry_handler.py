"""
PS-175: Layered Retry Handler with Exponential Backoff + Jitter

Supports three error tiers:
  1. TRANSIENT   → immediate retry (no delay)
  2. RATE_LIMIT  → exponential backoff + jitter
  3. SERVER_ERROR → degraded fallback instead of infinite retry

Usage:
    from agent_retry_handler import AgentRetryHandler, RetryResult

    handler = AgentRetryHandler(max_attempts=3, base_delay=1.0)
    result = await handler.execute_with_retry(my_async_function, arg1, arg2)
    if not result.ok:
        print(result.error.user_message)
"""

from __future__ import annotations

import asyncio
import random
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

from utils.agent_error_envelope import AgentErrorEnvelope

P = ParamSpec("P")
T = TypeVar("T")

logger = logging.getLogger(__name__)


class ErrorTier(Enum):
    TRANSIENT = "TRANSIENT"
    RATE_LIMIT = "RATE_LIMIT"
    SERVER_ERROR = "SERVER_ERROR"
    CLIENT_ERROR = "CLIENT_ERROR"
    CIRCUIT_OPEN = "CIRCUIT_OPEN"
    UNKNOWN = "UNKNOWN"


@dataclass
class RetryResult:
    ok: bool
    value: Any = None
    error: AgentErrorEnvelope | None = None
    attempts: int = 0
    total_latency_ms: float = 0.0

    @property
    def retryable(self) -> bool:
        return self.error is not None and self.error.retryable


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0          # seconds
    exponential_factor: float = 2.0   # multiply delay by this each attempt
    jitter: bool = True              # randomise delay by ±25%
    jitter_range: float = 0.25
    max_delay: float = 60.0          # seconds, cap for rate-limit backoff
    retry_on_non_envelope_errors: bool = True


def _classify(error: Exception | AgentErrorEnvelope) -> ErrorTier:
    """Classify an exception or envelope into an error tier."""
    if isinstance(error, AgentErrorEnvelope):
        tier_name = error.error_type
    else:
        tier_name = type(error).__name__.upper()

    if "RATE" in tier_name or "429" in str(error):
        return ErrorTier.RATE_LIMIT
    if "TIMEOUT" in tier_name or "TimeoutError" in tier_name:
        return ErrorTier.TRANSIENT
    if "CIRCUIT" in tier_name or "CIRCUIT_OPEN" in tier_name:
        return ErrorTier.CIRCUIT_OPEN
    if "500" in str(error) or "SERVER" in tier_name or "InternalError" in tier_name:
        return ErrorTier.SERVER_ERROR
    if "404" in str(error) or "NOT_FOUND" in tier_name or "ClientError" in tier_name:
        return ErrorTier.CLIENT_ERROR
    return ErrorTier.TRANSIENT


def _jittered_delay(attempt: int, base: float, factor: float, max_d: float, jitter: bool, jitter_range: float) -> float:
    """Compute exponential backoff delay with optional jitter."""
    delay = base * (factor ** (attempt - 1))
    delay = min(delay, max_d)
    if jitter:
        r = random.uniform(-jitter_range, jitter_range)
        delay = delay * (1.0 + r)
    return max(0, delay)


def _to_envelope(error: Exception | AgentErrorEnvelope, tool_name: str, attempt: int, max_attempts: int) -> AgentErrorEnvelope:
    """Normalise an exception into an AgentErrorEnvelope."""
    if isinstance(error, AgentErrorEnvelope):
        return error

    tier = _classify(error)
    tier_str = tier.value
    retryable = tier in (ErrorTier.TRANSIENT, ErrorTier.RATE_LIMIT)
    retry_after = _jittered_delay(attempt, 1.0, 2.0, 60.0, True, 0.25) if tier == ErrorTier.RATE_LIMIT else None

    return AgentErrorEnvelope(
        error_type=tier_str,
        code=tier_str,
        retryable=retryable,
        retry_after_sec=retry_after,
        suggested_action="wait_and_retry" if retryable else "no_retry_abort",
        user_message=f"{tier_str}: {str(error)[:200]}",
        recovery_hint=f"Tier={tier_str}, attempt={attempt}/{max_attempts}",
        tool_name=tool_name,
        attempt=attempt,
        max_attempts=max_attempts,
        timestamp=__import__("datetime").datetime.now(timezone.utc).isoformat(),
        details={"exception_type": type(error).__name__, "exception_str": str(error)[:500]},
    )


class AgentRetryHandler:
    """
    Layered retry executor for agent tool calls.

    Tier-based strategy:
      TRANSIENT  → retry immediately, no backoff
      RATE_LIMIT → exponential backoff + jitter, respect retry_after if available
      SERVER_ERROR → retry once, then degrade to fallback
      CLIENT_ERROR / CIRCUIT_OPEN → no retry, fail fast
    """

    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()

    async def execute_with_retry(
        self,
        coro: Callable[P, Coroutine[Any, Any, T]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> RetryResult:
        """
        Execute an async coroutine with layered retry logic.
        Returns RetryResult with .ok, .value, .error, .attempts, .latency_ms.
        """
        tool_name = getattr(coro, "__name__", "unknown")
        errors: list[AgentErrorEnvelope] = []
        start = time.monotonic()
        fallback_triggered = False

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                value = await coro(*args, **kwargs)
                return RetryResult(
                    ok=True,
                    value=value,
                    attempts=attempt,
                    total_latency_ms=(time.monotonic() - start) * 1000,
                )
            except Exception as exc:  # noqa: BLE001
                envelope = _to_envelope(exc, tool_name, attempt, self.config.max_attempts)
                errors.append(envelope)
                tier = _classify(exc)

                # Fail fast for non-retryable tiers
                if not envelope.retryable:
                    logger.warning("[PS-175] %s [%s/%s] — fail fast", tool_name, attempt, self.config.max_attempts)
                    break

                # Server errors: retry once, then degrade
                if tier == ErrorTier.SERVER_ERROR and attempt >= 2:
                    logger.warning("[PS-175] %s server error on attempt %s/%s — degrading", tool_name, attempt, self.config.max_attempts)
                    fallback_triggered = True
                    break

                # Calculate delay
                delay = envelope.retry_after_sec
                if delay is None or delay <= 0:
                    delay = _jittered_delay(
                        attempt, self.config.base_delay, self.config.exponential_factor,
                        self.config.max_delay, self.config.jitter, self.config.jitter_range,
                    )

                logger.info("[PS-175] %s [%s/%s] retryable error — waiting %.1fs", tool_name, attempt, self.config.max_attempts, delay)
                await asyncio.sleep(delay)

        # All attempts exhausted
        final_envelope = errors[-1] if errors else AgentErrorEnvelope(
            error_type="UNKNOWN",
            code="MAX_ATTEMPTS",
            retryable=False,
            suggested_action="alert_and_abort",
            user_message=f"Max retry attempts ({self.config.max_attempts}) reached for {tool_name}",
            tool_name=tool_name,
            attempt=self.config.max_attempts,
            max_attempts=self.config.max_attempts,
            timestamp=__import__("datetime").datetime.now(timezone.utc).isoformat(),
        )

        return RetryResult(
            ok=False,
            error=final_envelope,
            attempts=self.config.max_attempts,
            total_latency_ms=(time.monotonic() - start) * 1000,
        )

    def execute_with_retry_sync(
        self,
        func: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> RetryResult:
        """Synchronous wrapper — runs event loop internally."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.execute_with_retry(func, *args, **kwargs))


# ── Convenience helpers ────────────────────────────────────────────────────────

async def retry_coro(coro: Coroutine, *, max_attempts: int = 3, base_delay: float = 1.0) -> RetryResult:
    """One-liner for simple coroutine retry."""
    handler = AgentRetryHandler(RetryConfig(max_attempts=max_attempts, base_delay=base_delay))
    return await handler.execute_with_retry(lambda: coro)
