"""Contract tests for Core -> HA webhook envelope validation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import custom_components.copilot_ha.webhook as webhook_module
from custom_components.copilot_ha.const import (
    CONF_TOKEN,
    CONF_WEBHOOK_ID,
    ENV_LEGACY_HEADER_SUNSET_AT,
    HEADER_AUTH,
    HEADER_AUTH_LEGACY,
)


LARGE_TYPE_STRING = "x" * 1024

FUZZED_TYPE_CASES = [
    ("type_none", {"type": None, "data": {}}, "missing_type", {"required_field": "type"}),
    ("type_empty", {"type": "", "data": {}}, "missing_type", {"required_field": "type"}),
    ("type_whitespace", {"type": "   ", "data": {}}, "missing_type", {"required_field": "type"}),
    ("type_list", {"type": ["status"], "data": {}}, "missing_type", {"required_field": "type"}),
    ("type_dict", {"type": {"foo": "bar"}, "data": {}}, "missing_type", {"required_field": "type"}),
    ("nested_payload", {"payload": {"type": "status", "data": {}}}, "missing_type", {"required_field": "type"}),
    ("type_unicode", {"type": "💥", "data": {}}, "unknown_type", {"received": "💥"}),
    ("type_nullbyte", {"type": "status\0", "data": {}}, "unknown_type", {"received": "status\0"}),
    ("type_long", {"type": "x" * 1024, "data": {}}, "unknown_type", {"received": "x" * 1024}),
]

INVALID_DATA_CASES = [
    ("data_none", None),
    ("data_list", []),
    ("data_string", "oops"),
    ("data_int", 123),
    ("data_float", 1.23),
    ("data_bool", True),
]


class _FakeRequest:
    def __init__(self, payload, headers: dict[str, str] | None = None):
        self._payload = payload
        self.headers = headers or {}

    async def json(self):
        return self._payload


class _BadJsonRequest:
    def __init__(self, headers: dict[str, str] | None = None):
        self.headers = headers or {}

    async def json(self):
        raise ValueError("boom")


def _make_entry(token: str = "secret-token") -> SimpleNamespace:
    return SimpleNamespace(
        entry_id="entry-test",
        data={
            CONF_TOKEN: token,
            CONF_WEBHOOK_ID: "webhook-test-id",
        },
        options={},
    )


async def _capture_registered_handler(hass, entry, coordinator):
    holder: dict[str, object] = {}

    def _fake_register(_hass, _domain, _name, _webhook_id, handler):
        holder["handler"] = handler

    with patch(
        "custom_components.copilot_ha.webhook.webhook.async_register",
        side_effect=_fake_register,
    ):
        webhook_id = await webhook_module.async_register_webhook(hass, entry, coordinator)

    assert webhook_id == "webhook-test-id"
    assert "handler" in holder
    return holder["handler"]


def _response_json(response) -> dict:
    assert response.content_type == "application/json"
    return json.loads(response.text)


def _assert_error_contract(response, body: dict):
    code = body["error"]["code"]
    assert code in webhook_module.ERROR_CODE_SPECS
    spec = webhook_module.ERROR_CODE_SPECS[code]
    assert response.status == spec["status"]
    required = spec.get("required_details", ())
    if required:
        assert "details" in body["error"]
    for field in required:
        assert field in body["error"].get("details", {})


@pytest.fixture(autouse=True)
def _force_transition_modes(monkeypatch):
    # Keep default behavior explicit and test-stable.
    monkeypatch.setenv("PILOTSUITE_WEBHOOK_ALIAS_MODE", "transition")
    monkeypatch.delenv(ENV_LEGACY_HEADER_SUNSET_AT, raising=False)


@pytest.fixture
def hass():
    instance = MagicMock()
    instance.bus = MagicMock()
    instance.bus.async_fire = MagicMock()
    return instance


@pytest.fixture
def coordinator():
    instance = MagicMock()
    instance.data = {}
    instance.async_set_updated_data = MagicMock()
    return instance


CANONICAL_CASES = [
    ("status", {"online": True, "version": "13.5.0"}),
    ("mood", {"mood": "calm", "confidence": 0.9}),
    ("neuron", {"neurons": {"n1": {"active": True}}}),
    ("suggestion", {"title": "Test suggestion", "action": "noop"}),
]

LEGACY_CASES = [
    ("mood_changed", "mood", {"mood": "calm", "confidence": 0.9}),
    ("suggestion_new", "suggestion", {"title": "Legacy suggestion", "action": "noop"}),
    ("neuron_update", "neuron", {"neurons": {"n1": {"active": True}}}),
]


@pytest.mark.asyncio
async def test_missing_type_returns_400_with_structured_error(hass, coordinator):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"data": {"online": True}},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 400
    assert body["ok"] is False
    assert body["error"]["code"] == "missing_type"
    assert body["error"]["details"]["required_field"] == "type"


@pytest.mark.asyncio
async def test_missing_data_returns_400_with_structured_error(hass, coordinator):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"type": "status"},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 400
    assert body["ok"] is False
    assert body["error"]["code"] == "missing_data"
    assert body["error"]["details"]["required_field"] == "data"


@pytest.mark.asyncio
async def test_invalid_json_returns_400_with_structured_error(hass, coordinator):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _BadJsonRequest(headers={HEADER_AUTH: "secret-token"})
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 400
    assert body["ok"] is False
    assert body["error"]["code"] == "invalid_json"


@pytest.mark.asyncio
async def test_non_object_payload_returns_invalid_payload_structured_error(hass, coordinator):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload=["not", "an", "object"],
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 400
    assert body["ok"] is False
    assert body["error"]["code"] == "invalid_payload"
    assert body["error"]["details"]["expected"] == "object"


@pytest.mark.asyncio
async def test_unknown_type_returns_400_with_structured_error(hass, coordinator):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"type": "mystery_event", "data": {}},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 400
    assert body["ok"] is False
    assert body["error"]["code"] == "unknown_type"
    assert body["error"]["details"]["received"] == "mystery_event"
    assert "allowed" in body["error"]["details"]


@pytest.mark.asyncio
@pytest.mark.parametrize(("_label", "payload", "expected_code", "expected_details"), FUZZED_TYPE_CASES)
async def test_fuzzed_type_values_return_deterministic_errors(
    hass,
    coordinator,
    _label,
    payload,
    expected_code,
    expected_details,
):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload=payload,
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 400
    assert body["ok"] is False
    assert body["error"]["code"] == expected_code
    for key, value in expected_details.items():
        assert body["error"]["details"][key] == value


@pytest.mark.asyncio
@pytest.mark.parametrize(("_label", "data_value"), INVALID_DATA_CASES)
async def test_invalid_data_types_return_400_with_structured_error(
    hass,
    coordinator,
    _label,
    data_value,
):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"type": "status", "data": data_value},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 400
    assert body["ok"] is False
    assert body["error"]["code"] == "invalid_data"
    assert body["error"]["details"]["field"] == "data"
    assert body["error"]["details"]["expected"] == "object"


@pytest.mark.asyncio
async def test_nested_payload_with_large_unicode_data_returns_200(hass, coordinator):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    nested_payload = {
        "online": True,
        "version": f"v-{LARGE_TYPE_STRING}",
        "meta": {"unicode": "über", "nested": {"depth": 3}},
    }
    request = _FakeRequest(
        payload={"type": "status", "data": nested_payload},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    assert response.status == 200
    assert body == {"ok": True}
    coordinator.async_set_updated_data.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(("event_type", "data"), CANONICAL_CASES)
async def test_canonical_types_with_valid_data_return_200(hass, coordinator, event_type, data):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"type": event_type, "data": data},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    assert response.status == 200
    assert body == {"ok": True}

    if event_type == "suggestion":
        hass.bus.async_fire.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(("event_type", "canonical_type", "data"), LEGACY_CASES)
async def test_legacy_aliases_in_transition_mode_still_map_to_canonical(hass, coordinator, event_type, canonical_type, data):
    # Transition mode keeps backward-compatibility aliases active.
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"type": event_type, "data": data},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    assert response.status == 200
    assert body == {"ok": True}
    if canonical_type == "suggestion":
        hass.bus.async_fire.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(("event_type", "canonical_type", "data"), LEGACY_CASES)
async def test_legacy_aliases_in_sunset_mode_return_400_with_stable_error_code(
    hass,
    coordinator,
    event_type,
    canonical_type,
    data,
    monkeypatch,
):
    # Sunset mode explicitly rejects legacy aliases with stable contract code.
    monkeypatch.setenv("PILOTSUITE_WEBHOOK_ALIAS_MODE", "sunset")
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"type": event_type, "data": data},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 400
    assert body["ok"] is False
    assert body["error"]["code"] == "legacy_type_unsupported"
    assert body["error"]["details"]["received"] == event_type
    assert body["error"]["details"]["canonical_type"] == canonical_type
    assert body["error"]["details"]["mode"] == "sunset"


@pytest.mark.asyncio
async def test_legacy_api_key_accepted_before_sunset(monkeypatch, hass, coordinator):
    monkeypatch.setenv(ENV_LEGACY_HEADER_SUNSET_AT, "2026-03-07T00:00:00Z")
    monkeypatch.setattr(
        webhook_module,
        "_utcnow",
        lambda: datetime(2026, 3, 6, 12, 0, 0, tzinfo=timezone.utc),
    )

    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"type": "status", "data": {"online": True}},
        headers={HEADER_AUTH_LEGACY: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    assert response.status == 200
    assert body == {"ok": True}


@pytest.mark.asyncio
async def test_legacy_api_key_rejected_after_sunset_with_structured_error(monkeypatch, hass, coordinator):
    monkeypatch.setenv(ENV_LEGACY_HEADER_SUNSET_AT, "2026-03-05T00:00:00Z")
    monkeypatch.setattr(
        webhook_module,
        "_utcnow",
        lambda: datetime(2026, 3, 6, 12, 0, 0, tzinfo=timezone.utc),
    )

    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"type": "status", "data": {"online": True}},
        headers={HEADER_AUTH_LEGACY: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 401
    assert body["ok"] is False
    assert body["error"]["code"] == "legacy_header_sunset"
    assert body["error"]["details"]["header"] == HEADER_AUTH_LEGACY
    assert "2026-03-05" in body["error"]["details"]["sunset_at"]


@pytest.mark.asyncio
async def test_canonical_header_still_valid_after_sunset(monkeypatch, hass, coordinator):
    monkeypatch.setenv(ENV_LEGACY_HEADER_SUNSET_AT, "2026-03-05T00:00:00Z")
    monkeypatch.setattr(
        webhook_module,
        "_utcnow",
        lambda: datetime(2026, 3, 6, 12, 0, 0, tzinfo=timezone.utc),
    )

    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"type": "status", "data": {"online": True}},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    assert response.status == 200
    assert body == {"ok": True}


@pytest.mark.asyncio
async def test_invalid_token_returns_auth_failed_with_structured_error(hass, coordinator):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"type": "status", "data": {"online": True}},
        headers={HEADER_AUTH: "wrong-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 401
    assert body["ok"] is False
    assert body["error"]["code"] == "auth_failed"
    assert body["error"]["details"]["sources"] == ["canonical"]


@pytest.mark.asyncio
async def test_missing_token_returns_auth_missing_with_structured_error(hass, coordinator):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"type": "status", "data": {"online": True}},
        headers={},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 401
    assert body["ok"] is False
    assert body["error"]["code"] == "auth_missing"
    assert body["error"]["details"]["sources"] == ["missing"]
