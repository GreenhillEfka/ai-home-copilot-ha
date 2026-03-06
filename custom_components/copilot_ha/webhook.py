from __future__ import annotations

import logging
from typing import Any

from aiohttp.web import Response, json_response

from homeassistant.core import HomeAssistant
from homeassistant.components import webhook

from .api import CopilotStatus
from .const import CONF_TOKEN, CONF_WEBHOOK_ID, DOMAIN, HEADER_AUTH

_LOGGER = logging.getLogger(__name__)

# Canonical webhook event types (Core ↔ HA contract)
EVENT_TYPE_STATUS = "status"
EVENT_TYPE_MOOD = "mood"
EVENT_TYPE_SUGGESTION = "suggestion"
EVENT_TYPE_NEURON = "neuron"

_ALLOWED_EVENT_TYPES = {
    EVENT_TYPE_STATUS,
    EVENT_TYPE_MOOD,
    EVENT_TYPE_SUGGESTION,
    EVENT_TYPE_NEURON,
}

# Legacy aliases accepted for backward compatibility (older Core/HA versions)
_EVENT_TYPE_ALIAS_TO_CANONICAL = {
    "status": EVENT_TYPE_STATUS,
    "mood": EVENT_TYPE_MOOD,
    "mood_changed": EVENT_TYPE_MOOD,
    "suggestion": EVENT_TYPE_SUGGESTION,
    "suggestion_new": EVENT_TYPE_SUGGESTION,
    "neuron": EVENT_TYPE_NEURON,
    "neuron_update": EVENT_TYPE_NEURON,
}


def _normalize_event_type(raw_event_type: object) -> str:
    """Map legacy and canonical event types to canonical contract values."""
    if isinstance(raw_event_type, str):
        key = raw_event_type.strip().lower()
    else:
        key = ""

    if not key:
        return ""

    return _EVENT_TYPE_ALIAS_TO_CANONICAL.get(key, key)


def _error_response(
    *,
    status: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> Response:
    payload: dict[str, Any] = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details:
        payload["error"]["details"] = details
    return json_response(payload, status=status)


def _ok_response() -> Response:
    return json_response({"ok": True}, status=200)


def _make_webhook_url(hass: HomeAssistant, webhook_id: str) -> str:
    # Public base url or internal depending on HA config.
    return webhook.async_generate_url(hass, webhook_id)


async def async_ensure_webhook(hass: HomeAssistant, entry) -> str:
    webhook_id = entry.data.get(CONF_WEBHOOK_ID)
    if webhook_id:
        return webhook_id

    webhook_id = webhook.async_generate_id()
    hass.config_entries.async_update_entry(entry, data={**entry.data, CONF_WEBHOOK_ID: webhook_id})
    return webhook_id


def _merge_coordinator_data(coordinator, updates: dict) -> dict:
    """Merge partial updates into existing coordinator data dict."""
    current = coordinator.data if isinstance(coordinator.data, dict) else {}
    merged = {**current, **updates}
    return merged


async def async_register_webhook(hass: HomeAssistant, entry, coordinator) -> str:
    webhook_id = await async_ensure_webhook(hass, entry)

    async def _handle(hass: HomeAssistant, webhook_id: str, request):
        token_expected = (entry.data | entry.options).get(CONF_TOKEN)
        token_got = request.headers.get(HEADER_AUTH)

        if token_expected and token_got != token_expected:
            _LOGGER.warning("Rejected webhook: invalid token")
            return Response(status=401)

        try:
            payload = await request.json()
        except Exception:  # noqa: BLE001
            return _error_response(
                status=400,
                code="invalid_json",
                message="Request body must be valid JSON.",
            )

        if not isinstance(payload, dict):
            return _error_response(
                status=400,
                code="invalid_payload",
                message="Request body must be a JSON object.",
                details={"expected": "object"},
            )

        if "type" not in payload or not isinstance(payload.get("type"), str) or not payload.get("type", "").strip():
            return _error_response(
                status=400,
                code="missing_type",
                message="Webhook envelope must include a non-empty 'type' field.",
                details={"required_field": "type"},
            )

        if "data" not in payload:
            return _error_response(
                status=400,
                code="missing_data",
                message="Webhook envelope must include a 'data' field.",
                details={"required_field": "data"},
            )

        data = payload.get("data")
        if not isinstance(data, dict):
            return _error_response(
                status=400,
                code="invalid_data",
                message="Webhook envelope field 'data' must be a JSON object.",
                details={"field": "data", "expected": "object"},
            )

        # Typed envelope: {"type": "mood|neuron|suggestion|status", "data": {...}}
        event_type = _normalize_event_type(payload.get("type"))
        if event_type not in _ALLOWED_EVENT_TYPES:
            return _error_response(
                status=400,
                code="unknown_type",
                message="Unsupported webhook event type.",
                details={
                    "received": payload.get("type"),
                    "allowed": sorted(_ALLOWED_EVENT_TYPES),
                },
            )

        if event_type == EVENT_TYPE_MOOD:
            # Add-on pushes mood change: merge into coordinator data
            updates = {
                "mood": data,
                "dominant_mood": data.get("mood", "unknown"),
                "mood_confidence": data.get("confidence", 0.0),
            }
            merged = _merge_coordinator_data(coordinator, updates)
            coordinator.async_set_updated_data(merged)
            _LOGGER.debug("Webhook: mood push received – %s", data.get("mood"))

        elif event_type == EVENT_TYPE_NEURON:
            # Add-on pushes neuron state update
            updates = {"neurons": data.get("neurons", {})}
            merged = _merge_coordinator_data(coordinator, updates)
            coordinator.async_set_updated_data(merged)
            _LOGGER.debug("Webhook: neuron update received")

        elif event_type == EVENT_TYPE_SUGGESTION:
            # Add-on pushes new suggestion – fire HA event for suggestion panel
            hass.bus.async_fire(
                f"{DOMAIN}_suggestion_received",
                {"suggestion": data},
            )
            _LOGGER.debug("Webhook: suggestion push received")

        else:
            # Legacy status push (online/version)
            online = data.get("online")
            version = data.get("version")

            updates = {}
            if online is not None:
                updates["ok"] = bool(online)
            if isinstance(version, str):
                updates["version"] = version

            if updates:
                merged = _merge_coordinator_data(coordinator, updates)
                coordinator.async_set_updated_data(merged)

        return _ok_response()

    webhook.async_register(
        hass,
        DOMAIN,
        f"PilotSuite webhook ({entry.entry_id})",
        webhook_id,
        _handle,
    )

    return webhook_id


async def async_unregister_webhook(hass: HomeAssistant, webhook_id: str) -> None:
    webhook.async_unregister(hass, webhook_id)
