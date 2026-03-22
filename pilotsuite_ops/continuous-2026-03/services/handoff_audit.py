"""
PS-039: Handoff Audit Logger

Structured logging for agent-to-agent handoffs.
Writes to: /config/clawd/pilotsuite_ops/logs/handoff_audit.jsonl
One line per handoff event (JSON, ISO-8601, machine-parseable).

Schema per line:
{
  "handoff_id", "timestamp", "from_agent", "to_agent",
  "context_hash", "decision_rationale", "outcome",
  "duration_ms", "retry_count", "escalation_path"
}

Usage:
    from handoff_audit import HandoffAuditer, audit_handoff

    auditer = HandoffAuditer()

    # Log handoff start
    await auditer.log_start(handoff_id="pilotclaw-designclaw-1742600000000",
                             from_agent="pilotclaw", to_agent="designclaw",
                             context_hash="abc123", context_refs=["MEMORY.md#zone_fix"])

    # Log outcome
    await auditer.log_outcome(handoff_id="...", outcome="completed", duration_ms=4200)

    # Or use the decorator:
    @audit_handoff(auditer)
    async def my_agent_task(...):
        ...
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

LOG_DIR = Path("/config/clawd/pilotsuite_ops/logs")
LOG_FILE = LOG_DIR / "handoff_audit.jsonl"

LOG_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_context_hash(context: dict[str, Any]) -> str:
    """SHA-256 → first 16 hex chars (consistent with handoff_ack.py)."""
    canonical = json.dumps(context, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


class HandoffOutcome:
    """Standard outcome labels for audit entries."""
    RECEIVED = "received"            # Receiver acknowledged
    COMPLETED = "completed"          # Work finished successfully
    DECLINED = "declined"            # Receiver explicitly declined
    TIMED_OUT = "timed_out"          # No ack within timeout
    ESCALATED = "escalated"          # Routed to fallback agent
    FAILED = "failed"                # Work attempted but failed
    ORPHANED = "orphaned"            # Never picked up


class HandoffAuditer:
    """
    Writes structured handoff audit entries to a JSONL file.
    Supports async writes, log rotation by size, and query helpers.
    """

    def __init__(
        self,
        log_file: Path | str | None = None,
        max_file_size_mb: float = 10.0,
        max_backups: int = 5,
    ):
        self.log_file = Path(log_file) if log_file else LOG_FILE
        self.max_file_size = int(max_file_size_mb * 1024 * 1024)
        self.max_backups = max_backups
        self._lock = asyncio.Lock()
        self._write_queue: asyncio.Queue[str] | None = None
        self._writer_task: asyncio.Task[None] | None = None
        self._started = False

    async def start(self) -> None:
        """Start the async background writer (call once at agent startup)."""
        if self._started:
            return
        self._write_queue = asyncio.Queue()
        self._writer_task = asyncio.create_task(self._background_writer())
        self._started = True
        logger.info("[PS-039] HandoffAuditer started → %s", self.log_file)

    async def stop(self) -> None:
        """Flush queue and stop background writer (call at agent shutdown)."""
        if not self._started:
            return
        if self._write_queue:
            await self._write_queue.join()
        if self._writer_task:
            self._writer_task.cancel()
        self._started = False
        logger.info("[PS-039] HandoffAuditer stopped")

    # ── Public log methods ───────────────────────────────────────────────────────

    async def log_start(
        self,
        handoff_id: str,
        from_agent: str,
        to_agent: str,
        context_hash: str | None = None,
        context_refs: list[str] | None = None,
        priority: str = "normal",
        preconditions: dict[str, Any] | None = None,
    ) -> None:
        entry = {
            "event": "handoff_start",
            "handoff_id": handoff_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "context_hash": context_hash,
            "context_refs": context_refs or [],
            "priority": priority,
            "preconditions": preconditions,
            "timestamp": _now_iso(),
            "outcome": HandoffOutcome.RECEIVED,
        }
        await self._enqueue(entry)

    async def log_ack(
        self,
        handoff_id: str,
        to_agent: str,
        capable: bool,
        context_hash: str | None = None,
        decline_reason: str | None = None,
    ) -> None:
        entry = {
            "event": "handoff_ack",
            "handoff_id": handoff_id,
            "to_agent": to_agent,
            "ack_decision": "capable" if capable else "declined",
            "context_hash": context_hash,
            "decline_reason": decline_reason,
            "timestamp": _now_iso(),
        }
        await self._enqueue(entry)

    async def log_outcome(
        self,
        handoff_id: str,
        outcome: str,
        duration_ms: float | None = None,
        retry_count: int = 0,
        escalation_path: list[str] | None = None,
        decision_rationale: str | None = None,
        artifacts: list[str] | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        entry = {
            "event": "handoff_outcome",
            "handoff_id": handoff_id,
            "outcome": outcome,
            "duration_ms": duration_ms,
            "retry_count": retry_count,
            "escalation_path": escalation_path or [],
            "decision_rationale": decision_rationale,
            "artifacts": artifacts or [],
            "error": error,
            "timestamp": _now_iso(),
            **(metadata or {}),
        }
        await self._enqueue(entry)

    async def log_timeout(
        self,
        handoff_id: str,
        to_agent: str,
        wait_seconds: float,
        retry_count: int,
    ) -> None:
        entry = {
            "event": "handoff_timeout",
            "handoff_id": handoff_id,
            "to_agent": to_agent,
            "wait_seconds": wait_seconds,
            "retry_count": retry_count,
            "outcome": HandoffOutcome.TIMED_OUT,
            "timestamp": _now_iso(),
        }
        await self._enqueue(entry)

    # ── Query helpers ──────────────────────────────────────────────────────────

    async def get_handoff_log(self, handoff_id: str) -> list[dict[str, Any]]:
        """Return all log entries for a given handoff_id (read from file)."""
        results: list[dict[str, Any]] = []
        if not self.log_file.exists():
            return results
        async with self._lock:
            with open(self.log_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("handoff_id") == handoff_id:
                            results.append(entry)
                    except json.JSONDecodeError:
                        continue
        return results

    async def recent_outcomes(
        self,
        limit: int = 50,
        outcome_filter: str | None = None,
        from_agent: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return recent handoff outcomes, optionally filtered."""
        results: list[dict[str, Any]] = []
        if not self.log_file.exists():
            return results
        async with self._lock:
            with open(self.log_file) as f:
                lines = f.readlines()
        for line in reversed(lines[-limit:]):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("event") != "handoff_outcome":
                    continue
                if outcome_filter and entry.get("outcome") != outcome_filter:
                    continue
                if from_agent and entry.get("from_agent") != from_agent:
                    continue
                results.append(entry)
            except json.JSONDecodeError:
                continue
        return list(reversed(results))

    # ── Internal ───────────────────────────────────────────────────────────────

    async def _enqueue(self, entry: dict[str, Any]) -> None:
        if not self._started:
            await self.start()
        line = json.dumps(entry, default=str)
        if self._write_queue:
            await self._write_queue.put(line)
        else:
            # Sync fallback
            await self._write_line_sync(line)

    async def _background_writer(self) -> None:
        """Background coroutine that batches writes to the log file."""
        batch: list[str] = []
        while True:
            try:
                line = await asyncio.wait_for(self._write_queue.get(), timeout=0.5)
                batch.append(line)
                self._write_queue.task_done()
            except asyncio.TimeoutError:
                if batch:
                    await self._flush_batch(batch)
                    batch = []
                continue
            except asyncio.CancelledError:
                if batch:
                    await self._flush_batch(batch)
                break

    async def _flush_batch(self, batch: list[str]) -> None:
        async with self._lock:
            try:
                with open(self.log_file, "a") as f:
                    f.write("\n".join(batch) + "\n")
                size = self.log_file.stat().st_size
                if size > self.max_file_size:
                    self._rotate()
            except OSError:
                logger.exception("[PS-039] Failed to write audit log")

    def _rotate(self) -> None:
        """Rotate log file when it exceeds max size."""
        for i in range(self.max_backups - 1, 0, -1):
            src = self.log_file.with_suffix(f".jsonl.bak{i}")
            dst = self.log_file.with_suffix(f".jsonl.bak{i + 1}")
            if src.exists():
                dst.write_bytes(src.read_bytes())
        if self.log_file.exists():
            bk1 = self.log_file.with_suffix(".jsonl.bak1")
            self.log_file.rename(bk1)

    async def _write_line_sync(self, line: str) -> None:
        async with self._lock:
            with open(self.log_file, "a") as f:
                f.write(line + "\n")


# ── Decorator ─────────────────────────────────────────────────────────────────

def audit_handoff(auditer: HandoffAuditer):
    """Decorator to auto-log start + outcome for handoff-tracked functions."""
    def decorator(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
        @wraps(func)
        async def wrapper(*args, handoff_id: str | None = None, from_agent: str = "unknown", to_agent: str = "unknown", **kwargs):
            hid = handoff_id or f"auto-{func.__name__}-{int(time.time()*1000)}"
            start = time.monotonic()
            await auditer.log_start(handoff_id=hid, from_agent=from_agent, to_agent=to_agent)
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.monotonic() - start) * 1000
                await auditer.log_outcome(handoff_id=hid, outcome=HandoffOutcome.COMPLETED, duration_ms=duration_ms)
                return result
            except Exception as exc:
                duration_ms = (time.monotonic() - start) * 1000
                await auditer.log_outcome(handoff_id=hid, outcome=HandoffOutcome.FAILED, duration_ms=duration_ms, error=str(exc)[:200])
                raise
        return wrapper
    return decorator


# ── Global default instance ────────────────────────────────────────────────────

_default_auditer: HandoffAuditer | None = None


async def get_auditer() -> HandoffAuditer:
    global _default_auditer
    if _default_auditer is None:
        _default_auditer = HandoffAuditer()
        await _default_auditer.start()
    return _default_auditer


async def log_handoff_start(**kwargs) -> None:
    auditer = await get_auditer()
    await auditer.log_start(**kwargs)


async def log_handoff_outcome(**kwargs) -> None:
    auditer = await get_auditer()
    await auditer.log_outcome(**kwargs)
