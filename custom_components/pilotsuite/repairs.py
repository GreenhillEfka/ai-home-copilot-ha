from __future__ import annotations

import asyncio
import logging
import re
import traceback
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

import voluptuous as vol

from homeassistant import data_entry_flow
from homeassistant.components import persistent_notification
from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_track_time_interval

from .api import CopilotApiClient, CopilotApiError
from .const import DOMAIN
from .log_fixer import async_analyze_logs, async_disable_custom_integration_for_manifest_error
from .log_store import FindingType
from .log_store import async_get_log_fixer_state
from .storage import CandidateState, async_defer_candidate, async_set_candidate_state

_LOGGER = logging.getLogger(__name__)

# --- Decision Sync Queue ---------------------------------------------------

_SYNC_QUEUE_MAX_SIZE = 200
_SYNC_QUEUE_MAX_RETRIES = 5
_SYNC_QUEUE_RETRY_INTERVAL = 60  # seconds


@dataclass
class _PendingDecision:
    """A decision that failed to sync and needs retry."""
    entry_id: str
    candidate_id: str
    state: str
    retry_after_days: int | None = None
    attempts: int = 0
    created: float = field(default_factory=lambda: datetime.now().timestamp())


class DecisionSyncQueue:
    """Queue for decisions that failed to sync to Core.

    Stores failed decision syncs and retries them periodically.
    Thread-safe via asyncio.Lock.
    """

    def __init__(self) -> None:
        self._queue: deque[_PendingDecision] = deque(maxlen=_SYNC_QUEUE_MAX_SIZE)
        self._lock = asyncio.Lock()
        self._cancel_timer = None

    @property
    def pending_count(self) -> int:
        return len(self._queue)

    async def enqueue(self, decision: _PendingDecision) -> None:
        async with self._lock:
            self._queue.append(decision)
        _LOGGER.debug(
            "Decision sync queued: %s → %s (queue size: %d)",
            decision.candidate_id, decision.state, len(self._queue),
        )

    async def process(self, hass: HomeAssistant) -> int:
        """Process all pending decisions. Returns count of successfully synced."""
        async with self._lock:
            if not self._queue:
                return 0
            batch = list(self._queue)
            self._queue.clear()

        synced = 0
        requeue: list[_PendingDecision] = []

        for decision in batch:
            api = _get_core_api(hass, decision.entry_id)
            if api is None:
                decision.attempts += 1
                if decision.attempts < _SYNC_QUEUE_MAX_RETRIES:
                    requeue.append(decision)
                else:
                    _LOGGER.warning(
                        "Decision sync dropped after %d attempts: %s → %s",
                        decision.attempts, decision.candidate_id, decision.state,
                    )
                continue

            core_id = decision.candidate_id
            if core_id.startswith("core_"):
                core_id = core_id[5:]

            payload: dict = {"state": decision.state}
            if decision.state == "deferred" and decision.retry_after_days is not None:
                payload["retry_after_days"] = decision.retry_after_days

            try:
                await api.async_put(f"/api/v1/candidates/{core_id}", payload)
                _LOGGER.info("Decision sync (retry): %s → %s synced", core_id, decision.state)
                synced += 1
            except CopilotApiError:
                decision.attempts += 1
                if decision.attempts < _SYNC_QUEUE_MAX_RETRIES:
                    requeue.append(decision)
                else:
                    _LOGGER.warning(
                        "Decision sync dropped after %d attempts: %s → %s",
                        decision.attempts, decision.candidate_id, decision.state,
                    )

        if requeue:
            async with self._lock:
                for item in requeue:
                    self._queue.append(item)
            _LOGGER.debug("Decision sync: %d items re-queued for retry", len(requeue))

        return synced

    def start_periodic_retry(self, hass: HomeAssistant) -> None:
        """Start periodic retry timer."""
        if self._cancel_timer is not None:
            return

        from datetime import timedelta

        async def _retry_callback(_now) -> None:
            if self.pending_count > 0:
                synced = await self.process(hass)
                if synced:
                    _LOGGER.info("Decision sync retry: %d synced, %d remaining", synced, self.pending_count)

        self._cancel_timer = async_track_time_interval(
            hass, _retry_callback, timedelta(seconds=_SYNC_QUEUE_RETRY_INTERVAL),
        )

    def stop(self) -> None:
        """Stop periodic retry timer."""
        if self._cancel_timer is not None:
            self._cancel_timer()
            self._cancel_timer = None


def _get_sync_queue(hass: HomeAssistant) -> DecisionSyncQueue:
    """Get or create the decision sync queue singleton."""
    hass.data.setdefault(DOMAIN, {})
    queue = hass.data[DOMAIN].get("_decision_sync_queue")
    if isinstance(queue, DecisionSyncQueue):
        return queue
    queue = DecisionSyncQueue()
    hass.data[DOMAIN]["_decision_sync_queue"] = queue
    queue.start_periodic_retry(hass)
    return queue


# --- Repair UX helpers (PS-UX-014) -----------------------------------------

_RE_EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_RE_JWT = re.compile(r"(?<![A-Za-z0-9_-])(eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})")
_RE_BEARER = re.compile(r"(?i)(bearer\s+)(\S+)")
_RE_URL_CREDS = re.compile(r"(?i)(https?://)([^\s:/]+):([^\s@/]+)@")


def _redact_text(text: str, *, max_len: int = 4000) -> str:
    """Best-effort redaction for user-visible repair diagnostics."""
    s = str(text or "")
    s = _RE_URL_CREDS.sub(r"\1**REDACTED**:**REDACTED**@", s)
    s = _RE_BEARER.sub(r"\1**REDACTED**", s)
    s = _RE_JWT.sub("**REDACTED_JWT**", s)
    s = _RE_EMAIL.sub("**REDACTED_EMAIL**", s)
    if len(s) > max_len:
        s = s[: max_len - 50] + "...(truncated)..."
    return s


def _safe_tb(err: Exception, *, max_lines: int = 25) -> str:
    """Return a compact, redacted traceback snippet."""
    try:
        tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    except Exception:  # noqa: BLE001
        tb = repr(err)

    tb = _redact_text(tb, max_len=8000)
    lines = [ln.rstrip("\n") for ln in tb.splitlines() if ln.strip()]
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    return "\n".join(lines)


def _safe_notification_id(prefix: str, *parts: str) -> str:
    raw = "_".join([prefix, *[str(p or "") for p in parts if p]])
    raw = re.sub(r"[^a-zA-Z0-9_-]+", "_", raw).strip("_")
    if len(raw) > 80:
        raw = raw[:80]
    return raw or prefix


def _notify_repair_diagnostics(
    hass: HomeAssistant,
    *,
    title: str,
    message: str,
    notification_id: str,
) -> None:
    """Publish diagnostics via persistent notification (HA UI)."""
    try:
        persistent_notification.async_create(
            hass,
            _redact_text(message, max_len=12000),
            title=title,
            notification_id=notification_id,
        )
    except Exception:  # noqa: BLE001
        _LOGGER.debug("Failed to create persistent_notification for diagnostics", exc_info=True)
def _get_core_api(hass: HomeAssistant, entry_id: str) -> CopilotApiClient | None:
    """Retrieve the shared CopilotApiClient for this config entry."""
    ent_data = hass.data.get(DOMAIN, {}).get(entry_id)
    if isinstance(ent_data, dict):
        coord = ent_data.get("coordinator")
        api = getattr(coord, "api", None)
        if isinstance(api, CopilotApiClient):
            return api
    return None


async def async_sync_decision_to_core(
    hass: HomeAssistant,
    entry_id: str,
    candidate_id: str,
    state: str,
    retry_after_days: int | None = None,
) -> None:
    """Sync user decision back to Core Add-on with retry queue.

    Maps HA candidate_id (prefixed ``core_``) back to the Core UUID and
    calls ``PUT /api/v1/candidates/{candidate_id}`` to close the feedback loop.
    If the sync fails, the decision is queued for periodic retry.
    """
    api = _get_core_api(hass, entry_id)
    if api is None:
        _LOGGER.debug("Decision sync: no Core API client — queuing for retry")
        queue = _get_sync_queue(hass)
        await queue.enqueue(_PendingDecision(
            entry_id=entry_id,
            candidate_id=candidate_id,
            state=state,
            retry_after_days=retry_after_days,
        ))
        return

    # HA candidate IDs from the poller are prefixed with "core_".
    core_id = candidate_id
    if core_id.startswith("core_"):
        core_id = core_id[5:]

    payload: dict = {"state": state}
    if state == "deferred" and retry_after_days is not None:
        payload["retry_after_days"] = retry_after_days

    try:
        await api.async_put(f"/api/v1/candidates/{core_id}", payload)
        _LOGGER.info("Decision sync: %s → %s synced to Core", core_id, state)
    except CopilotApiError as err:
        _LOGGER.warning("Decision sync: failed for %s → %s: %s — queuing retry", core_id, state, err)
        queue = _get_sync_queue(hass)
        await queue.enqueue(_PendingDecision(
            entry_id=entry_id,
            candidate_id=candidate_id,
            state=state,
            retry_after_days=retry_after_days,
        ))


STEP_CHOICE = vol.Schema(
    {
        vol.Required("decision", default="imported"): vol.In(
            {
                "imported": "Blueprint importiert / Automation erstellt",
                "defer": "Später nochmal erinnern",
                "dismiss": "Nicht mehr vorschlagen",
            }
        )
    }
)

STEP_DEFER = vol.Schema(
    {
        vol.Required("days", default=7): vol.All(int, vol.Range(min=1, max=365)),
    }
)

STEP_SEED_CHOICE = vol.Schema(
    {
        vol.Required("decision", default="done"): vol.In(
            {
                "done": "Ich habe daraus eine Automation erstellt",
                "defer": "Später nochmal erinnern",
                "dismiss": "Nicht mehr vorschlagen",
            }
        )
    }
)

STEP_DISABLE_INTEGRATION = vol.Schema(
    {
        vol.Required("confirm", default=False): bool,
    }
)


class CandidateRepairFlow(RepairsFlow):
    def __init__(
        self,
        hass: HomeAssistant,
        *,
        entry_id: str,
        candidate_id: str,
        issue_id: str | None = None,
    ) -> None:
        self.hass = hass
        self._entry_id = entry_id
        self._candidate_id = candidate_id
        self._issue_id = issue_id

    async def _maybe_delete_issue(self) -> None:
        # Best-effort cleanup to avoid UI leftovers.
        if not self._issue_id:
            return
        try:
            ir.async_delete_issue(self.hass, DOMAIN, self._issue_id)
        except Exception:  # noqa: BLE001
            return

    async def async_step_init(self, user_input=None) -> data_entry_flow.FlowResult:
        if user_input is not None:
            if user_input["decision"] == "dismiss":
                await async_set_candidate_state(
                    self.hass, self._entry_id, self._candidate_id, CandidateState.DISMISSED
                )
                await async_sync_decision_to_core(
                    self.hass, self._entry_id, self._candidate_id, "dismissed"
                )
                await self._maybe_delete_issue()
                return self.async_create_entry(title="", data={"result": "dismissed"})

            if user_input["decision"] == "defer":
                return await self.async_step_defer()

            await async_set_candidate_state(
                self.hass, self._entry_id, self._candidate_id, CandidateState.ACCEPTED
            )
            await async_sync_decision_to_core(
                self.hass, self._entry_id, self._candidate_id, "accepted"
            )
            await self._maybe_delete_issue()
            return self.async_create_entry(title="", data={"result": "accepted"})

        return self.async_show_form(step_id="init", data_schema=STEP_CHOICE)

    async def async_step_defer(self, user_input=None) -> data_entry_flow.FlowResult:
        if user_input is not None:
            from homeassistant.util import dt as dt_util

            days = int(user_input.get("days", 7))
            until = dt_util.utcnow().timestamp() + days * 86400
            await async_defer_candidate(
                self.hass,
                self._entry_id,
                self._candidate_id,
                until_ts=until,
            )
            await async_sync_decision_to_core(
                self.hass, self._entry_id, self._candidate_id, "deferred",
                retry_after_days=days,
            )
            return self.async_create_entry(
                title="", data={"result": "deferred", "days": days}
            )

        return self.async_show_form(step_id="defer", data_schema=STEP_DEFER)


class SeedRepairFlow(RepairsFlow):
    def __init__(
        self,
        hass: HomeAssistant,
        *,
        entry_id: str,
        candidate_id: str,
        source: str,
        entities: str,
        excerpt: str,
        issue_data: dict | None = None,
        issue_id: str | None = None,
    ) -> None:
        self.hass = hass
        self._entry_id = entry_id
        self._candidate_id = candidate_id
        self._source = source
        self._entities = entities
        self._excerpt = excerpt
        self._issue_data = issue_data or {}
        self._issue_id = issue_id

    async def _maybe_delete_issue(self) -> None:
        if not self._issue_id:
            return
        try:
            ir.async_delete_issue(self.hass, DOMAIN, self._issue_id)
        except Exception:  # noqa: BLE001
            return

    async def async_step_init(self, user_input=None) -> data_entry_flow.FlowResult:
        if user_input is not None:
            if user_input["decision"] == "dismiss":
                await async_set_candidate_state(
                    self.hass, self._entry_id, self._candidate_id, CandidateState.DISMISSED
                )
                await async_sync_decision_to_core(
                    self.hass, self._entry_id, self._candidate_id, "dismissed"
                )
                await self._maybe_delete_issue()
                return self.async_create_entry(title="", data={"result": "dismissed"})

            if user_input["decision"] == "defer":
                return await self.async_step_defer()

            # Accept
            await async_set_candidate_state(
                self.hass, self._entry_id, self._candidate_id, CandidateState.ACCEPTED
            )
            await async_sync_decision_to_core(
                self.hass, self._entry_id, self._candidate_id, "accepted"
            )

            # Special-case: graph edge candidates can be applied to the Core graph (governance-first).
            if self._issue_data.get("candidate_type") == "graph_edge_candidate":
                from_id = self._issue_data.get("from")
                to_id = self._issue_data.get("to")
                edge_type = self._issue_data.get("edge_type")
                if isinstance(from_id, str) and isinstance(to_id, str) and isinstance(edge_type, str):
                    try:
                        data = self.hass.data.get(DOMAIN, {}).get(self._entry_id)
                        co = data.get("coordinator") if isinstance(data, dict) else None
                        api = getattr(co, "api", None) if co is not None else None
                        if api is not None:
                            await api.async_post(
                                "/api/v1/graph/ops",
                                {
                                    "op": "touch_edge",
                                    "from": from_id,
                                    "to": to_id,
                                    "type": edge_type,
                                    "delta": 1.0,
                                    "idempotency_key": self._candidate_id,
                                },
                            )
                    except Exception:  # noqa: BLE001
                        # Best-effort only; decision is still recorded.
                        pass

            await self._maybe_delete_issue()
            return self.async_create_entry(title="", data={"result": "accepted"})

        return self.async_show_form(
            step_id="init",
            data_schema=STEP_SEED_CHOICE,
            description_placeholders={
                "source": self._source,
                "entities": self._entities,
                "excerpt": self._excerpt,
            },
        )

    async def async_step_defer(self, user_input=None) -> data_entry_flow.FlowResult:
        if user_input is not None:
            from homeassistant.util import dt as dt_util

            days = int(user_input.get("days", 7))
            until = dt_util.utcnow().timestamp() + days * 86400
            await async_defer_candidate(
                self.hass,
                self._entry_id,
                self._candidate_id,
                until_ts=until,
            )
            await async_sync_decision_to_core(
                self.hass, self._entry_id, self._candidate_id, "deferred",
                retry_after_days=days,
            )
            return self.async_create_entry(
                title="", data={"result": "deferred", "days": days}
            )

        return self.async_show_form(step_id="defer", data_schema=STEP_DEFER)


class DisableCustomIntegrationRepairFlow(RepairsFlow):
    def __init__(
        self,
        hass: HomeAssistant,
        *,
        issue_id: str,
        integration: str,
    ) -> None:
        self.hass = hass
        self._issue_id = issue_id
        self._integration = integration

        # Runtime state (PS-UX-014)
        self._failures: int = 0
        self._last_error: str | None = None
        self._last_tb: str | None = None

    async def async_step_init(self, user_input=None) -> data_entry_flow.FlowResult:
        if user_input is not None:
            if not user_input.get("confirm"):
                return self.async_show_form(
                    step_id="init",
                    data_schema=STEP_DISABLE_INTEGRATION,
                    errors={"base": "confirm_required"},
                    description_placeholders={
                        "integration": self._integration,
                    },
                )

            try:
                tx = await async_disable_custom_integration_for_manifest_error(
                    self.hass, integration=self._integration, issue_id=self._issue_id
                )
            except Exception as err:  # noqa: BLE001
                self._failures += 1
                self._last_error = _redact_text(str(err), max_len=800)
                self._last_tb = _safe_tb(err)

                _notify_repair_diagnostics(
                    self.hass,
                    title="PilotSuite Repair fehlgeschlagen",
                    message=(
                        f"Integration: {self._integration}\n"
                        f"Aktion: Disable integration\n"
                        f"Fehler: {self._last_error}\n\n"
                        f"Traceback (gekürzt):\n{self._last_tb}"
                    ),
                    notification_id=_safe_notification_id(
                        "pilotsuite_repair_disable_failed",
                        self._integration,
                        self._issue_id,
                        str(self._failures),
                    ),
                )

                return await self.async_step_failed()

            return self.async_create_entry(title="", data={"result": "disabled", "tx": tx.data})

        return self.async_show_form(
            step_id="init",
            data_schema=STEP_DISABLE_INTEGRATION,
            description_placeholders={
                "integration": self._integration,
            },
        )

    def _failed_schema(self) -> vol.Schema:
        actions: dict[str, str] = {}
        if self._failures < 3:
            actions["retry"] = "Erneut versuchen"
        actions["export_logs"] = "Logs exportieren"
        actions["details"] = "Details anzeigen"
        actions["close"] = "Schließen"

        default = "retry" if "retry" in actions else "export_logs"
        return vol.Schema({vol.Required("action", default=default): vol.In(actions)})

    async def async_step_failed(self, user_input=None) -> data_entry_flow.FlowResult:
        """Failure panel with Retry + Export logs + Details (PS-UX-014)."""
        if user_input is not None:
            action = str(user_input.get("action") or "")

            if action == "retry":
                # Re-run with explicit confirm step to keep governance-first behavior.
                return await self.async_step_init()

            if action in ("export_logs", "details"):
                _notify_repair_diagnostics(
                    self.hass,
                    title="PilotSuite Repair — Details",
                    message=(
                        f"Integration: {self._integration}\n"
                        f"Fehlversuche: {self._failures}\n"
                        f"Letzter Fehler: {self._last_error or 'unknown'}\n\n"
                        + ("Traceback (gekürzt):\n" + (self._last_tb or "(keine)") if action == "details" else "")
                    ),
                    notification_id=_safe_notification_id(
                        "pilotsuite_repair_disable_details",
                        self._integration,
                        self._issue_id,
                        action,
                        str(self._failures),
                    ),
                )
                return await self.async_step_failed()

            return self.async_create_entry(title="", data={"result": "failed"})

        return self.async_show_form(step_id="failed", data_schema=self._failed_schema())


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict | None,
) -> RepairsFlow:
    if not data:
        raise data_entry_flow.UnknownFlow

    # 1) Candidate suggestions
    entry_id = data.get("entry_id")
    candidate_id = data.get("candidate_id")
    if isinstance(entry_id, str) and isinstance(candidate_id, str):
        # Seed candidates
        if data.get("kind") == "seed":
            source = str(data.get("seed_source") or "")
            entities = data.get("seed_entities")
            entities_str = ", ".join(entities) if isinstance(entities, list) else ""
            excerpt = str(data.get("seed_text") or "")
            # keep placeholders small
            excerpt = excerpt.strip().replace("\n", " ")
            if len(excerpt) > 160:
                excerpt = excerpt[:159] + "…"
            if len(entities_str) > 120:
                entities_str = entities_str[:119] + "…"
            return SeedRepairFlow(
                hass,
                entry_id=entry_id,
                candidate_id=candidate_id,
                source=source,
                entities=entities_str,
                excerpt=excerpt,
                issue_data=data,
                issue_id=issue_id,
            )

        # Blueprint apply candidates (governance-first)
        if data.get("blueprint_id") or data.get("blueprint_path"):
            return RepairsBlueprintApplyFlow(
                hass,
                issue_id=issue_id,
                entry_id=entry_id,
                candidate_id=candidate_id,
                issue_data=data,
            )

        # Generic candidate (user does manual blueprint import)
        return CandidateRepairFlow(
            hass,
            entry_id=entry_id,
            candidate_id=candidate_id,
            issue_id=issue_id,
        )

    # 2) Log findings
    finding_id = data.get("finding_id")
    if isinstance(finding_id, str) and issue_id.startswith("log_"):
        state = await async_get_log_fixer_state(hass)
        finding = (state.get("findings") or {}).get(finding_id)
        if (
            isinstance(finding, dict)
            and finding.get("finding_type") == FindingType.MANIFEST_PARSE_ERROR
        ):
            integration = (finding.get("details") or {}).get("integration")
            if isinstance(integration, str) and integration:
                return DisableCustomIntegrationRepairFlow(
                    hass,
                    issue_id=issue_id,
                    integration=integration,
                )

    raise data_entry_flow.UnknownFlow


# --- Blueprint apply (governance-first) ---

STEP_BP_INIT = vol.Schema(
    {
        vol.Required("decision", default="preview"): vol.In(
            {
                "preview": "Vorschlag ansehen",
                "apply": "Automation jetzt erstellen (Blueprint anwenden)",
                "defer": "Später nochmal erinnern",
                "dismiss": "Nicht mehr vorschlagen",
            }
        )
    }
)

STEP_BP_CONFIGURE = vol.Schema(
    {
        vol.Required("a_entity"): str,
        vol.Optional("a_to_state", default="on"): str,
        vol.Required("b_target_entity_id"): str,
        vol.Optional("b_action", default="turn_on"): vol.In(["turn_on", "turn_off", "toggle"]),
    }
)

STEP_BP_CONFIRM = vol.Schema(
    {
        vol.Required("confirm", default=False): bool,
        vol.Optional("confirm_text", default=""): str,
    }
)

STEP_BP_RESULT_FAILED = vol.Schema(
    {
        vol.Required("action", default="retry"): vol.In(
            {
                "retry": "Retry",
                "export_logs": "Export logs (analyze)",
                "defer": "Später nochmal erinnern",
                "dismiss": "Schließen",
            }
        )
    }
)


class RepairsBlueprintApplyFlow(RepairsFlow):
    def __init__(
        self,
        hass: HomeAssistant,
        *,
        issue_id: str,
        entry_id: str,
        candidate_id: str,
        issue_data: dict,
    ) -> None:
        self.hass = hass
        self._issue_id = issue_id
        self._entry_id = entry_id
        self._candidate_id = candidate_id
        self._issue_data = issue_data

        # Runtime state
        self._plan = None
        self._apply_failures: int = 0
        self._last_confirm_input: dict | None = None
        self._last_apply_error: str | None = None
        self._last_apply_tb: str | None = None
        self._last_log_export: str | None = None

    async def _maybe_delete_issue(self) -> None:
        try:
            ir.async_delete_issue(self.hass, DOMAIN, self._issue_id)
        except Exception:  # noqa: BLE001
            return

    def _risk(self) -> str:
        return str(self._issue_data.get("risk") or "medium")

    def _needs_configure(self, inputs: dict) -> bool:
        # For our shipped blueprint, we need at least a_entity + b_target.
        if not isinstance(inputs, dict):
            return True
        if not inputs.get("a_entity"):
            return True
        if not inputs.get("b_target"):
            return True
        return False

    async def async_step_init(self, user_input=None) -> data_entry_flow.FlowResult:
        if user_input is not None:
            decision = user_input.get("decision")

            if decision == "dismiss":
                await async_set_candidate_state(
                    self.hass, self._entry_id, self._candidate_id, CandidateState.DISMISSED
                )
                await self._maybe_delete_issue()
                return self.async_create_entry(title="", data={"result": "dismissed"})

            if decision == "defer":
                return await self.async_step_defer()

            if decision == "apply":
                # Build plan from issue data.
                from .repairs_blueprints import async_build_plan_from_issue_data

                self._plan = async_build_plan_from_issue_data(
                    entry_id=self._entry_id,
                    candidate_id=self._candidate_id,
                    issue_id=self._issue_id,
                    data=self._issue_data,
                )

                # Ensure inputs exist (v0.1: allow user to enter minimal required).
                inputs = dict(getattr(self._plan, "blueprint_inputs", {}) or {})
                if self._needs_configure(inputs):
                    return await self.async_step_configure()

                return await self.async_step_confirm()

            # preview
            return self.async_show_form(
                step_id="init",
                data_schema=STEP_BP_INIT,
                description_placeholders={
                    "blueprint": str(self._issue_data.get("blueprint_id") or "pilotsuite/a_to_b_safe.yaml"),
                    "risk": self._risk(),
                },
            )

        return self.async_show_form(
            step_id="init",
            data_schema=STEP_BP_INIT,
            description_placeholders={
                "blueprint": str(self._issue_data.get("blueprint_id") or "pilotsuite/a_to_b_safe.yaml"),
                "risk": self._risk(),
            },
        )

    async def async_step_configure(self, user_input=None) -> data_entry_flow.FlowResult:
        if user_input is not None:
            # Validate entities exist (best-effort).
            a_entity = str(user_input.get("a_entity") or "").strip()
            b_entity = str(user_input.get("b_target_entity_id") or "").strip()
            if not a_entity or not b_entity:
                return self.async_show_form(
                    step_id="configure",
                    data_schema=STEP_BP_CONFIGURE,
                    errors={"base": "invalid"},
                )
            if self.hass.states.get(a_entity) is None or self.hass.states.get(b_entity) is None:
                return self.async_show_form(
                    step_id="configure",
                    data_schema=STEP_BP_CONFIGURE,
                    errors={"base": "invalid"},
                )

            # Map to blueprint inputs.
            inputs = {
                "a_entity": a_entity,
                "a_to_state": str(user_input.get("a_to_state") or "on"),
                "a_for": {"seconds": 0},
                "conditions": [],
                "b_target": {"entity_id": b_entity},
                "b_action": str(user_input.get("b_action") or "turn_on"),
            }

            if self._plan is None:
                from .repairs_blueprints import async_build_plan_from_issue_data

                self._plan = async_build_plan_from_issue_data(
                    entry_id=self._entry_id,
                    candidate_id=self._candidate_id,
                    issue_id=self._issue_id,
                    data=self._issue_data,
                )

            # Freeze updated inputs.
            self._plan = type(self._plan)(
                **{
                    **self._plan.__dict__,
                    "blueprint_inputs": inputs,
                }
            )

            return await self.async_step_confirm()

        return self.async_show_form(step_id="configure", data_schema=STEP_BP_CONFIGURE)

    async def async_step_confirm(self, user_input=None) -> data_entry_flow.FlowResult:
        if user_input is not None:
            if not user_input.get("confirm"):
                return self.async_show_form(
                    step_id="confirm",
                    data_schema=STEP_BP_CONFIRM,
                    errors={"base": "confirm_required"},
                )

            if self._risk() == "high":
                txt = str(user_input.get("confirm_text") or "").strip()
                if txt != "CONFIRM":
                    return self.async_show_form(
                        step_id="confirm",
                        data_schema=STEP_BP_CONFIRM,
                        errors={"base": "confirm_required"},
                    )

            self._last_confirm_input = dict(user_input)

            # Apply.
            from .repairs_blueprints import async_apply_plan

            if self._plan is None:
                raise data_entry_flow.UnknownFlow

            try:
                await async_apply_plan(self.hass, self._plan)
            except Exception as err:  # noqa: BLE001
                self._apply_failures += 1
                self._last_apply_error = str(err)
                _LOGGER.warning(
                    "Repair apply failed (candidate=%s, failures=%s): %s",
                    self._candidate_id,
                    self._apply_failures,
                    err,
                )
                return await self.async_step_result_failed()

            await async_set_candidate_state(
                self.hass, self._entry_id, self._candidate_id, CandidateState.ACCEPTED
            )
            await self._maybe_delete_issue()

            return self.async_create_entry(title="", data={"result": "applied"})

        return self.async_show_form(
            step_id="confirm",
            data_schema=STEP_BP_CONFIRM,
            description_placeholders={
                "risk": self._risk(),
                "note": "Bei risk=high musst du zusätzlich CONFIRM eintippen.",
            },
        )

    async def async_step_result_failed(self, user_input=None) -> data_entry_flow.FlowResult:
        """ResultPanel.failed: Controlled recovery with Retry + Export-logs."""

        if user_input is not None:
            action = user_input.get("action")

            if action == "retry":
                # Re-run apply without forcing the user to re-navigate.
                return await self.async_step_confirm(self._last_confirm_input or {"confirm": True, "confirm_text": "CONFIRM"})

            if action == "export_logs":
                try:
                    result = await async_analyze_logs(self.hass)
                    findings = result.findings or []
                    lines = [
                        f"Scanned lines: {result.scanned_lines}",
                        f"Findings: {len(findings)}",
                    ]
                    for f in findings[:8]:
                        details = f.details or {}
                        samples = details.get("sample_lines") or []
                        lines.append(f"- {f.title} (count={details.get('count','?')})")
                        for s in samples[:3]:
                            lines.append(f"  · {s}")
                    self._last_log_export = "\n".join(lines)
                except Exception as err:  # noqa: BLE001
                    self._last_log_export = f"Log export failed: {err}"

                return await self.async_step_result_failed()

            if action == "defer":
                return await self.async_step_defer()

            # dismiss/close
            return self.async_create_entry(
                title="",
                data={
                    "result": "apply_failed",
                    "failures": self._apply_failures,
                    "error": self._last_apply_error,
                },
            )

        export = self._last_log_export or "(noch kein Log-Export erzeugt)"
        err = self._last_apply_error or "unknown"
        hint = (
            "Repair konnte nicht angewendet werden. Du kannst es erneut versuchen oder Logs exportieren."
            + ("\n\nHinweis: Mehrere Fehlversuche erkannt — prüfe Token/Netzwerk und die System-Logs." if self._apply_failures >= 3 else "")
        )

        return self.async_show_form(
            step_id="result_failed",
            data_schema=STEP_BP_RESULT_FAILED,
            description_placeholders={
                "hint": hint,
                "error": err,
                "export": export,
            },
        )

    async def async_step_defer(self, user_input=None) -> data_entry_flow.FlowResult:
        # Reuse the generic defer UI.
        if user_input is not None:
            from homeassistant.util import dt as dt_util

            days = int(user_input.get("days", 7))
            until = dt_util.utcnow().timestamp() + days * 86400
            await async_defer_candidate(
                self.hass,
                self._entry_id,
                self._candidate_id,
                until_ts=until,
            )
            return self.async_create_entry(title="", data={"result": "deferred", "days": days})

        return self.async_show_form(step_id="defer", data_schema=STEP_DEFER)
