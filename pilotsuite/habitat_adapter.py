"""Home Assistant habitat adapter helpers.

DEPRECATED: habitat_adapter.py is renamed to habitus_adapter.py.
All new code must import from habitus_adapter.
habitat_adapter.py is kept as alias for backward compatibility only.
Will be removed in future release.

---

Keeps the HA↔Core boundary explicit by attaching normalized inbound contracts
when forwarding HA events and by normalizing outbound Core suggestion payloads
into proposal/action command shapes.
"""

from __future__ import annotations

from typing import Any, Mapping

ADAPTER_ID = "homeassistant"
INBOUND_CONTRACT_VERSION = "ha.input.v1"
OUTBOUND_CONTRACT_VERSION = "ha.output.v1"
INPUT_MODEL = "NeuronInputV1"
VALID_AUTONOMY_MODES = {"autonomous", "learning", "off"}


def _copy_dict(value: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return dict(value or {})


def _copy_list(value: list[Any] | tuple[Any, ...] | None = None) -> list[Any]:
    return list(value or [])


def _coerce_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_ms(ts: Any) -> int | None:
    if isinstance(ts, (int, float)):
        return int(ts)
    if isinstance(ts, str):
        numeric = ts.strip()
        if numeric.isdigit():
            return int(numeric)
    return None


def _entity_domain(entity_id: Any) -> str | None:
    if isinstance(entity_id, str) and "." in entity_id:
        return entity_id.split(".", 1)[0]
    return None


def _zone_id(zone_ids: list[str] | None) -> str | None:
    if isinstance(zone_ids, list):
        for zone_id in zone_ids:
            if isinstance(zone_id, str) and zone_id:
                return zone_id
    return None


def _adapter_metadata(direction: str, event_type: str, version: str) -> dict[str, Any]:
    return {
        "name": ADAPTER_ID,
        "direction": direction,
        "contract_version": version,
        "event_type": event_type,
    }


def _coerce_autonomy_mode(value: Any, default: str = "learning") -> str:
    if isinstance(value, str) and value in VALID_AUTONOMY_MODES:
        return value
    return default


def build_state_changed_forward_item(
    *,
    item_id: str,
    ts: str,
    entity_id: str,
    old_state: Any,
    new_state: Any,
    zone_ids: list[str] | None,
    state_attributes: Mapping[str, Any] | None = None,
    neuron_tags: list[str] | None = None,
    occurred_at_ms: int | None = None,
) -> dict[str, Any]:
    zone_ids = _copy_list(zone_ids)
    neuron_tags = _copy_list(neuron_tags)
    domain = _entity_domain(entity_id) or ADAPTER_ID
    attrs = {
        "domain": domain,
        "zone_ids": zone_ids,
        "old_state": old_state,
        "new_state": new_state,
        "state_attributes": _copy_dict(state_attributes),
    }
    if neuron_tags:
        attrs["neuron_tags"] = list(neuron_tags)

    occurred_at_ms = occurred_at_ms if occurred_at_ms is not None else _coerce_ms(item_id)
    habitat_event = {
        "event_id": item_id,
        "module_id": domain,
        "event_type": "state_changed",
        "entity_id": entity_id,
        "zone_id": _zone_id(zone_ids),
        "domain": domain,
        "state": new_state,
        "attributes": dict(attrs),
        "context": {"source": "homeassistant", "ts": ts, "direction": "homeassistant_to_core"},
        "tags": list(neuron_tags),
        "raw_event": {},
        "occurred_at_ms": occurred_at_ms,
        "input_model": INPUT_MODEL,
    }
    neuron_input = {
        "input_id": f"nin:{item_id}",
        "input_model": INPUT_MODEL,
        "module_id": domain,
        "source_event_id": item_id,
        "zone_id": _zone_id(zone_ids),
        "entity_id": entity_id,
        "domain": domain,
        "signal": "state_changed",
        "value": new_state,
        "confidence": 1.0,
        "observed_at_ms": occurred_at_ms,
        "context": {"source": "homeassistant", "ts": ts, "event_type": "state_changed"},
        "tags": list(neuron_tags),
        "neuron_targets": list(neuron_tags),
        "metadata": {
            "old_state": old_state,
            "new_state": new_state,
            "state_attributes": _copy_dict(state_attributes),
            "zone_ids": list(zone_ids),
        },
    }
    return {
        "id": item_id,
        "ts": ts,
        "type": "state_changed",
        "source": "home_assistant",
        "entity_id": entity_id,
        "attributes": attrs,
        "adapter": _adapter_metadata("homeassistant_to_core", "state_changed", INBOUND_CONTRACT_VERSION),
        "habitat_event": habitat_event,
        "neuron_input": neuron_input,
    }


def build_call_service_forward_item(
    *,
    item_id: str,
    ts: str,
    domain: str,
    service: str,
    entity_ids: list[str],
    zone_ids: list[str] | None,
    occurred_at_ms: int | None = None,
) -> dict[str, Any]:
    entity_ids = [entity_id for entity_id in entity_ids if isinstance(entity_id, str) and entity_id]
    zone_ids = _copy_list(zone_ids)
    lead_entity_id = entity_ids[0] if entity_ids else f"{domain}.unknown"
    occurred_at_ms = occurred_at_ms if occurred_at_ms is not None else _coerce_ms(item_id)

    attrs = {
        "domain": domain,
        "service": service,
        "entity_ids": list(entity_ids),
        "zone_ids": list(zone_ids),
    }
    habitat_event = {
        "event_id": item_id,
        "module_id": domain or ADAPTER_ID,
        "event_type": "call_service",
        "entity_id": lead_entity_id,
        "zone_id": _zone_id(zone_ids),
        "domain": domain or _entity_domain(lead_entity_id),
        "state": {"domain": domain, "service": service, "entity_ids": list(entity_ids)},
        "attributes": dict(attrs),
        "context": {"source": "homeassistant", "ts": ts, "direction": "homeassistant_to_core"},
        "tags": [],
        "raw_event": {},
        "occurred_at_ms": occurred_at_ms,
        "input_model": INPUT_MODEL,
    }
    neuron_input = {
        "input_id": f"nin:{item_id}",
        "input_model": INPUT_MODEL,
        "module_id": domain or ADAPTER_ID,
        "source_event_id": item_id,
        "zone_id": _zone_id(zone_ids),
        "entity_id": lead_entity_id,
        "domain": domain or _entity_domain(lead_entity_id),
        "signal": f"{domain}.{service}" if domain and service else "call_service",
        "value": {"domain": domain, "service": service},
        "confidence": 1.0,
        "observed_at_ms": occurred_at_ms,
        "context": {"source": "homeassistant", "ts": ts, "event_type": "call_service"},
        "tags": [],
        "neuron_targets": [],
        "metadata": {"entity_ids": list(entity_ids), "zone_ids": list(zone_ids)},
    }
    return {
        "id": item_id,
        "ts": ts,
        "type": "call_service",
        "source": "home_assistant",
        "entity_id": lead_entity_id,
        "attributes": attrs,
        "adapter": _adapter_metadata("homeassistant_to_core", "call_service", INBOUND_CONTRACT_VERSION),
        "habitat_event": habitat_event,
        "neuron_input": neuron_input,
    }


def _extract_target_payload(data: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    target = _copy_dict(data.get("target") if isinstance(data.get("target"), Mapping) else None)
    payload = _copy_dict(data.get("payload") if isinstance(data.get("payload"), Mapping) else None)

    entity_id = data.get("entity_id") or data.get("target_entity")
    if isinstance(entity_id, str) and entity_id and "entity_id" not in target:
        target["entity_id"] = entity_id

    if not payload and isinstance(data.get("service_data"), Mapping):
        payload = _copy_dict(data.get("service_data"))

    actions = data.get("actions")
    first_action = actions[0] if isinstance(actions, list) and actions else None
    if isinstance(first_action, Mapping):
        if not target:
            if isinstance(first_action.get("target"), Mapping):
                target = _copy_dict(first_action.get("target"))
            elif isinstance(first_action.get("entity_id"), str):
                target = {"entity_id": first_action["entity_id"]}
        if not payload:
            if isinstance(first_action.get("service_data"), Mapping):
                payload = _copy_dict(first_action.get("service_data"))
            elif isinstance(first_action.get("data"), Mapping):
                payload = _copy_dict(first_action.get("data"))

    return target, payload


def _extract_action_type(data: Mapping[str, Any], target: Mapping[str, Any]) -> str:
    for key in ("action_type", "service", "service_name"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value

    actions = data.get("actions")
    first_action = actions[0] if isinstance(actions, list) and actions else None
    if isinstance(first_action, Mapping):
        domain = first_action.get("domain")
        service = first_action.get("service")
        if isinstance(domain, str) and isinstance(service, str) and domain and service:
            return f"{domain}.{service}"

    entity_domain = _entity_domain(target.get("entity_id"))
    kind = data.get("kind") or data.get("type") or "command"
    if isinstance(kind, str) and kind:
        return f"{entity_domain}.{kind}" if entity_domain else kind
    return f"{entity_domain}.command" if entity_domain else "homeassistant.command"


def _module_id(data: Mapping[str, Any], action_type: str, target: Mapping[str, Any]) -> str:
    raw = data.get("module_id")
    if isinstance(raw, str) and raw:
        return raw
    domain = _entity_domain(target.get("entity_id"))
    if domain:
        return domain
    if "." in action_type:
        return action_type.split(".", 1)[0]
    return ADAPTER_ID


def _zone_from_payload(data: Mapping[str, Any]) -> str | None:
    zone_id = data.get("zone_id")
    if isinstance(zone_id, str) and zone_id:
        return zone_id
    zone_ids = data.get("zone_ids")
    if isinstance(zone_ids, list):
        return _zone_id([zone for zone in zone_ids if isinstance(zone, str)])
    return None


def normalize_received_webhook_payload(event_type: str, data: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(data)
    normalized.setdefault(
        "adapter",
        _adapter_metadata("core_to_homeassistant", event_type, OUTBOUND_CONTRACT_VERSION),
    )

    if event_type == "suggestion" and "proposal_intent" not in normalized:
        target, payload = _extract_target_payload(data)
        action_type = _extract_action_type(data, target)
        title = str(data.get("title") or data.get("alias") or action_type)
        summary = str(data.get("summary") or data.get("description") or title)
        explanation = str(data.get("explanation") or data.get("reason") or "")
        proposal_intent = {
            "proposal_id": str(data.get("proposal_id") or f"proposal:{normalized.get('adapter', {}).get('event_type', event_type)}"),
            "module_id": _module_id(data, action_type, target),
            "zone_id": _zone_from_payload(data),
            "action_type": action_type,
            "title": title,
            "summary": summary,
            "target": target,
            "payload": payload,
            "confidence": _coerce_float(data.get("confidence") or data.get("score"), 0.0),
            "explanation": explanation,
            "suggestion_mode": str(data.get("suggestion_mode") or "explainable_manual"),
            "autonomy_mode": _coerce_autonomy_mode(data.get("autonomy_mode")),
            "direct_execution_enabled": _coerce_bool(data.get("direct_execution_enabled"), False),
            "approval_required": _coerce_bool(data.get("approval_required"), True),
            "explanation_required": _coerce_bool(data.get("explanation_required"), True),
            "requires_confirmation": _coerce_bool(data.get("requires_confirmation"), True),
            "output_adapter": ADAPTER_ID,
            "source_input_ids": _copy_list(data.get("source_input_ids") if isinstance(data.get("source_input_ids"), list) else None),
            "source_event_ids": _copy_list(data.get("source_event_ids") if isinstance(data.get("source_event_ids"), list) else None),
            "evidence": _copy_dict(data.get("evidence") if isinstance(data.get("evidence"), Mapping) else None),
            "metadata": {"raw_suggestion": dict(data)},
        }
        normalized["proposal_intent"] = proposal_intent
        normalized.setdefault(
            "module_command",
            {
                "command_id": str(data.get("command_id") or f"cmd:{proposal_intent['proposal_id']}"),
                "module_id": proposal_intent["module_id"],
                "command_name": proposal_intent["action_type"],
                "zone_id": proposal_intent["zone_id"],
                "proposal_id": proposal_intent["proposal_id"],
                "action_id": None,
                "target": dict(proposal_intent["target"]),
                "payload": dict(proposal_intent["payload"]),
                "command_mode": "suggest",
                "explanation": proposal_intent["explanation"],
                "approved": False,
                "metadata": {
                    "title": proposal_intent["title"],
                    "summary": proposal_intent["summary"],
                    "confidence": proposal_intent["confidence"],
                    "suggestion_mode": proposal_intent["suggestion_mode"],
                    "autonomy_mode": proposal_intent["autonomy_mode"],
                    "direct_execution_enabled": proposal_intent["direct_execution_enabled"],
                    "approval_required": proposal_intent["approval_required"],
                    "requires_confirmation": proposal_intent["requires_confirmation"],
                    "output_adapter": ADAPTER_ID,
                },
            },
        )

    if event_type in {"autonomy_executed", "action", "execute"} and "action_intent" not in normalized:
        target, payload = _extract_target_payload(data)
        action_type = _extract_action_type(data, target)
        approved = _coerce_bool(data.get("approved"), True)
        action_intent = {
            "action_id": str(data.get("action_id") or f"action:{event_type}"),
            "proposal_id": data.get("proposal_id"),
            "module_id": _module_id(data, action_type, target),
            "zone_id": _zone_from_payload(data),
            "action_type": action_type,
            "target": target,
            "payload": payload,
            "confidence": _coerce_float(data.get("confidence") or data.get("score"), 0.0),
            "explanation": str(data.get("explanation") or data.get("reason") or ""),
            "suggestion_mode": str(data.get("suggestion_mode") or "explainable_manual"),
            "autonomy_mode": _coerce_autonomy_mode(data.get("autonomy_mode")),
            "direct_execution_enabled": _coerce_bool(data.get("direct_execution_enabled"), False),
            "approval_required": _coerce_bool(data.get("approval_required"), True),
            "explanation_required": _coerce_bool(data.get("explanation_required"), True),
            "requires_confirmation": _coerce_bool(data.get("requires_confirmation"), True),
            "output_adapter": ADAPTER_ID,
            "source_input_ids": _copy_list(data.get("source_input_ids") if isinstance(data.get("source_input_ids"), list) else None),
            "source_event_ids": _copy_list(data.get("source_event_ids") if isinstance(data.get("source_event_ids"), list) else None),
            "evidence": _copy_dict(data.get("evidence") if isinstance(data.get("evidence"), Mapping) else None),
            "metadata": {"raw_payload": dict(data)},
            "approved": approved,
        }
        normalized["action_intent"] = action_intent
        normalized.setdefault(
            "module_command",
            {
                "command_id": str(data.get("command_id") or f"cmd:{action_intent['action_id']}"),
                "module_id": action_intent["module_id"],
                "command_name": action_intent["action_type"],
                "zone_id": action_intent["zone_id"],
                "proposal_id": action_intent["proposal_id"],
                "action_id": action_intent["action_id"],
                "target": dict(action_intent["target"]),
                "payload": dict(action_intent["payload"]),
                "command_mode": "execute" if approved else "suggest",
                "explanation": action_intent["explanation"],
                "approved": approved,
                "metadata": {
                    "confidence": action_intent["confidence"],
                    "suggestion_mode": action_intent["suggestion_mode"],
                    "autonomy_mode": action_intent["autonomy_mode"],
                    "direct_execution_enabled": action_intent["direct_execution_enabled"],
                    "approval_required": action_intent["approval_required"],
                    "requires_confirmation": action_intent["requires_confirmation"],
                    "output_adapter": ADAPTER_ID,
                },
            },
        )

    return normalized


__all__ = [
    "ADAPTER_ID",
    "INBOUND_CONTRACT_VERSION",
    "OUTBOUND_CONTRACT_VERSION",
    "INPUT_MODEL",
    "build_state_changed_forward_item",
    "build_call_service_forward_item",
    "normalize_received_webhook_payload",
]
