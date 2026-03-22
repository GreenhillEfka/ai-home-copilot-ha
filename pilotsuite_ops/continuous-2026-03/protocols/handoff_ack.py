"""
PS-038: Handoff Acknowledgment Protocol

Bidirectional ack protocol for agent-to-agent handoffs.
State machine: IDLE → REQUEST_PENDING → ACK_RECEIVED | DECLINED | TIMED_OUT → DONE

Usage:
    from handoff_ack import HandoffAcknowledger, HandoffStatus

    ack = HandoffAcknowledger(handoff_id="pilotclaw-designclaw-1742600000000")
    ack.start(timeout_seconds=30)

    # In receiver agent:
    ack.acknowledge(capable=True, context_hash="abc123")
    # or
    ack.decline(reason="missing_ha_token")

    # In sender agent:
    status = ack.wait_for_ack(timeout=30)
    if status == HandoffStatus.TIMED_OUT:
        ack.escalate(to_agent="hephaistos")
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HandoffStatus(Enum):
    IDLE = "idle"
    REQUEST_PENDING = "request_pending"
    ACK_RECEIVED = "ack_received"
    DECLINED = "declined"
    TIMED_OUT = "timed_out"
    ESCALATED = "escalated"
    DONE = "done"


class AckDecision(Enum):
    CAPABLE = "capable"      # Receiver confirms it can handle the task
    DECLINE = "decline"      # Receiver explicitly declines
    TIMEOUT = "timeout"      # Receiver did not respond in time


# ── In-memory state store (per-process) ───────────────────────────────────────

_HANDOVERS: dict[str, _HandoffState] = {}
_LOCK = asyncio.Lock()


@dataclass
class _HandoffState:
    handoff_id: str
    from_agent: str
    to_agent: str
    status: HandoffStatus = HandoffStatus.IDLE
    decision: AckDecision | None = None
    context_hash: str | None = None
    decline_reason: str | None = None
    timeout_seconds: int = 30
    created_at: float = field(default_factory=time.time)
    ack_received_at: float | None = None
    escalation_target: str | None = None


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_handoff_id(from_agent: str, to_agent: str) -> str:
    """Generate a unique handoff ID: {from}-{to}-{unix_ts_ms}"""
    ts = int(time.time() * 1000)
    return f"{from_agent}-{to_agent}-{ts}"


def compute_context_hash(context: dict[str, Any]) -> str:
    """SHA-256 hash of deterministic JSON for context integrity."""
    import json
    canonical = json.dumps(context, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


class HandoffAcknowledger:
    """
    Manages the acknowledgment lifecycle of a single handoff.

    Protocol flow:
      1. Sender: start() → state = REQUEST_PENDING
      2. Receiver: acknowledge(capable=True) → state = ACK_RECEIVED
                  OR decline(reason="...")     → state = DECLINED
      3. Sender: wait_for_ack(timeout) → HandoffStatus
      4. On TIMED_OUT: sender calls escalate() → state = ESCALATED
      5. On ACK + work done: sender calls complete() → state = DONE
    """

    def __init__(
        self,
        handoff_id: str,
        from_agent: str = "unknown",
        to_agent: str = "unknown",
        timeout_seconds: int = 30,
    ):
        self.handoff_id = handoff_id
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.timeout_seconds = timeout_seconds
        self._state = _HandoffState(
            handoff_id=handoff_id,
            from_agent=from_agent,
            to_agent=to_agent,
            timeout_seconds=timeout_seconds,
        )
        self._event = asyncio.Event()
        self._retries = 0
        self._max_retries = 2

    async def start(self) -> None:
        """Mark handoff as REQUEST_PENDING. Call once by sender."""
        async with _LOCK:
            _HANDOVERS[self.handoff_id] = self._state
        self._state.status = HandoffStatus.REQUEST_PENDING
        logger.info("[PS-038] Handoff %s started: %s → %s", self.handoff_id, self.from_agent, self.to_agent)

    async def acknowledge(self, capable: bool, context_hash: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        """
        Called by the RECEIVER agent.
        Set capable=True if it can handle the task, False + use decline() instead.
        """
        async with _LOCK:
            if self._state.status not in (HandoffStatus.REQUEST_PENDING,):
                logger.warning("[PS-038] Ack for %s ignored — status is %s", self.handoff_id, self._state.status)
                return

            if capable:
                self._state.status = HandoffStatus.ACK_RECEIVED
                self._state.decision = AckDecision.CAPABLE
                self._state.context_hash = context_hash
                logger.info("[PS-038] Handoff %s ACKNOWLEDGED by %s", self.handoff_id, self.to_agent)
            else:
                self._state.status = HandoffStatus.DECLINED
                self._state.decision = AckDecision.DECLINE
                logger.info("[PS-038] Handoff %s DECLINED by %s", self.handoff_id, self.to_agent)

            self._state.ack_received_at = time.time()
            self._event.set()

    async def decline(self, reason: str) -> None:
        """Called by the RECEIVER agent when it cannot handle the task."""
        async with _LOCK:
            self._state.status = HandoffStatus.DECLINED
            self._state.decision = AckDecision.DECLINE
            self._state.decline_reason = reason
            self._state.ack_received_at = time.time()
            self._event.set()
        logger.info("[PS-038] Handoff %s DECLINED: %s", self.handoff_id, reason)

    async def wait_for_ack(self, timeout: float | None = None) -> HandoffStatus:
        """
        Called by the SENDER agent.
        Waits up to `timeout` seconds for an ack. Returns final status.
        On timeout: increments retry counter, re-sends if retries remain.
        """
        timeout = timeout or self.timeout_seconds

        for attempt in range(1, self._max_retries + 1):
            logger.info("[PS-038] Handoff %s waiting for ack (attempt %s/%s)", self.handoff_id, attempt, self._max_retries)

            try:
                await asyncio.wait_for(self._event.wait(), timeout=timeout)
                return self._state.status
            except asyncio.TimeoutError:
                logger.warning("[PS-038] Handoff %s timed out (attempt %s)", self.handoff_id, attempt)
                if attempt < self._max_retries:
                    self._retries += 1
                    self._state.status = HandoffStatus.REQUEST_PENDING
                    self._event.clear()
                    # Re-notify receiver (in production: publish to message bus)
                    logger.info("[PS-038] Retrying handoff %s (%s/%s)", self.handoff_id, attempt, self._max_retries)
                else:
                    self._state.status = HandoffStatus.TIMED_OUT
                    self._state.decision = AckDecision.TIMEOUT
                    return HandoffStatus.TIMED_OUT

        return self._state.status

    async def escalate(self, to_agent: str, reason: str = "ack_timeout") -> None:
        """
        Called by the SENDER when max retries exhausted.
        Re-routes to escalation target.
        """
        self._state.status = HandoffStatus.ESCALATED
        self._state.escalation_target = to_agent
        logger.warning("[PS-038] Handoff %s ESCALATED to %s (reason: %s)", self.handoff_id, to_agent, reason)

    async def complete(self) -> None:
        """Mark handoff as DONE after successful work transfer."""
        self._state.status = HandoffStatus.DONE
        logger.info("[PS-038] Handoff %s COMPLETED", self.handoff_id)

    @property
    def status(self) -> HandoffStatus:
        return self._state.status

    @property
    def decision(self) -> AckDecision | None:
        return self._state.decision

    def to_dict(self) -> dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "status": self.status.value,
            "decision": self.decision.value if self.decision else None,
            "context_hash": self._state.context_hash,
            "decline_reason": self._state.decline_reason,
            "escalation_target": self._state.escalation_target,
            "created_at": datetime.fromtimestamp(self._state.created_at, tz=timezone.utc).isoformat(),
            "ack_received_at": datetime.fromtimestamp(self._state.ack_received_at, tz=timezone.utc).isoformat() if self._state.ack_received_at else None,
        }


# ── Convenience helpers ────────────────────────────────────────────────────────

async def quick_handoff(
    from_agent: str,
    to_agent: str,
    context: dict[str, Any],
    timeout: int = 30,
) -> tuple[HandoffStatus, HandoffAcknowledger]:
    """
    One-liner: initiate handoff, wait for ack, return (status, ack_object).
    Usage:
        status, ack = await quick_handoff("pilotclaw", "designclaw", {"task": "fix bug"})
        if status == HandoffStatus.ACK_RECEIVED:
            # proceed
    """
    handoff_id = generate_handoff_id(from_agent, to_agent)
    ctx_hash = compute_context_hash(context)
    ack = HandoffAcknowledger(handoff_id, from_agent, to_agent, timeout)
    await ack.start()
    status = await ack.wait_for_ack(timeout=timeout)
    return status, ack
