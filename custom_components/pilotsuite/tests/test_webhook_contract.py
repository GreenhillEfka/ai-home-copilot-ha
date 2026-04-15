"""Contract tests for Core -> HA webhook envelope validation."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import custom_components.copilot_ha.webhook as webhook_module
from custom_components.pilotsuite.const import (
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


class _BodyRequest:
    def __init__(self, body_bytes: bytes, headers: dict[str, str] | None = None):
        self._body_bytes = body_bytes
        self.headers = headers or {}

    async def read(self):
        return self._body_bytes


def _json_bytes(payload) -> bytes:
    # Must match Core signing input (json.dumps(...).encode('utf-8'))
    return json.dumps(payload, default=str).encode("utf-8")


def _signature_header(secret: str, timestamp: int, nonce: str, body_bytes: bytes) -> str:
    signing_input = f"{timestamp}.{nonce}.".encode("utf-8") + body_bytes
    digest = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


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
        "custom_components.pilotsuite.webhook.webhook.async_register",
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
    monkeypatch.delenv(webhook_module.ENV_WEBHOOK_SIGNING_SECRET_PRIMARY, raising=False)
    monkeypatch.delenv(webhook_module.ENV_WEBHOOK_SIGNING_SECRET_SECONDARY, raising=False)
    monkeypatch.delenv(webhook_module.ENV_WEBHOOK_SIGNING_TIMESTAMP_TTL_SECONDS, raising=False)

    # Prevent cross-test leakage from the module-level nonce cache.
    if hasattr(webhook_module, "_SIGNING_NONCE_CACHE"):
        webhook_module._SIGNING_NONCE_CACHE.clear()


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
    ("autonomy_executed", {"zone_id": "wohnbereich", "module_id": "licht", "actions": []}),
    ("autonomy_failed", {"zone_id": "wohnbereich", "error": "timeout"}),
    ("scene_captured", {"zone_id": "wohnbereich", "scene_id": "s1"}),
    ("scene_applied", {"zone_id": "wohnbereich", "scene_id": "s1"}),
    ("module_zone_state_changed", {"zone_id": "wohnbereich", "module_id": "licht", "new_state": "active"}),
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
async def test_legacy_api_key_rejected_at_exact_sunset_with_structured_error(monkeypatch, hass, coordinator):
    """Edgecase: now == sunset_at must be treated as sunset (reject legacy header)."""

    monkeypatch.setenv(ENV_LEGACY_HEADER_SUNSET_AT, "2026-03-06T12:00:00Z")
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
    assert body["error"]["details"]["mode"] == "sunset"


@pytest.mark.asyncio
async def test_legacy_api_key_invalid_sunset_env_fails_closed(monkeypatch, hass, coordinator):
    """Invalid sunset config must fail-closed (reject legacy header)."""

    monkeypatch.setenv(ENV_LEGACY_HEADER_SUNSET_AT, "not-a-date")
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
    assert body["error"]["details"]["mode"] == "sunset"
    assert body["error"]["details"]["sunset_at_raw"] == "not-a-date"


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
async def test_invalid_token_returns_structured_error(hass, coordinator):
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
    assert body["error"]["code"] == "invalid_token"
    assert body["error"]["details"]["sources"] == ["canonical"]


@pytest.mark.asyncio
async def test_missing_token_returns_invalid_token_with_structured_error(hass, coordinator):
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
    assert body["error"]["code"] == "invalid_token"
    assert body["error"]["details"]["sources"] == ["missing"]


@pytest.mark.asyncio
async def test_autonomy_executed_merges_history_and_fires_event(hass, coordinator):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)
    request = _FakeRequest(
        payload={"type": "autonomy_executed", "data": {
            "zone_id": "wohnbereich", "module_id": "licht",
            "actions": [{"type": "turn_on_light"}], "mood": "relax",
        }},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)
    assert response.status == 200
    coordinator.async_set_updated_data.assert_called_once()
    hass.bus.async_fire.assert_called_once()
    call_args = hass.bus.async_fire.call_args
    assert call_args[0][0] == "pilotsuite_autonomy_executed"


@pytest.mark.asyncio
async def test_module_zone_state_updates_coordinator(hass, coordinator):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)
    request = _FakeRequest(
        payload={"type": "module_zone_state_changed", "data": {
            "zone_id": "wohnbereich", "module_id": "musik", "new_state": "learning",
        }},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)
    assert response.status == 200
    coordinator.async_set_updated_data.assert_called_once()


@pytest.mark.asyncio
async def test_scene_captured_fires_ha_event(hass, coordinator):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)
    request = _FakeRequest(
        payload={"type": "scene_captured", "data": {
            "zone_id": "kueche", "scene_id": "s1", "name": "Test",
        }},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)
    assert response.status == 200
    hass.bus.async_fire.assert_called_once()
    assert hass.bus.async_fire.call_args[0][0] == "pilotsuite_scene_captured"


@pytest.mark.asyncio
async def test_signing_enabled_missing_signature_headers_returns_401(monkeypatch, hass, coordinator):
    monkeypatch.setenv(webhook_module.ENV_WEBHOOK_SIGNING_SECRET_PRIMARY, "primary-secret")
    monkeypatch.setattr(
        webhook_module,
        "_utcnow",
        lambda: datetime(2026, 3, 6, 12, 0, 0, tzinfo=timezone.utc),
    )

    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    payload = {"type": "status", "data": {"online": True}}
    body_bytes = _json_bytes(payload)
    request = _BodyRequest(
        body_bytes,
        headers={
            HEADER_AUTH: "secret-token",
            # Missing X-Webhook-* headers
        },
    )

    response = await handler(hass, "webhook-test-id", request)
    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 401
    assert body["error"]["code"] == "missing_signature_headers"


@pytest.mark.asyncio
async def test_signing_enabled_valid_signature_returns_200(monkeypatch, hass, coordinator):
    secret = "primary-secret"
    monkeypatch.setenv(webhook_module.ENV_WEBHOOK_SIGNING_SECRET_PRIMARY, secret)

    now = datetime(2026, 3, 6, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(webhook_module, "_utcnow", lambda: now)
    timestamp = int(now.timestamp())
    nonce = "a" * 32

    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    payload = {"type": "status", "data": {"online": True}}
    body_bytes = _json_bytes(payload)
    signature = _signature_header(secret, timestamp, nonce, body_bytes)

    request = _BodyRequest(
        body_bytes,
        headers={
            HEADER_AUTH: "secret-token",
            webhook_module.HEADER_WEBHOOK_TIMESTAMP: str(timestamp),
            webhook_module.HEADER_WEBHOOK_NONCE: nonce,
            webhook_module.HEADER_WEBHOOK_SIGNATURE: signature,
        },
    )

    response = await handler(hass, "webhook-test-id", request)
    assert response.status == 200
    assert _response_json(response) == {"ok": True}


@pytest.mark.asyncio
async def test_signing_enabled_stale_timestamp_returns_401(monkeypatch, hass, coordinator):
    secret = "primary-secret"
    monkeypatch.setenv(webhook_module.ENV_WEBHOOK_SIGNING_SECRET_PRIMARY, secret)
    monkeypatch.setenv(webhook_module.ENV_WEBHOOK_SIGNING_TIMESTAMP_TTL_SECONDS, "300")

    now = datetime(2026, 3, 6, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(webhook_module, "_utcnow", lambda: now)

    timestamp = int(now.timestamp()) - 1000
    nonce = "b" * 32

    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    payload = {"type": "status", "data": {"online": True}}
    body_bytes = _json_bytes(payload)
    signature = _signature_header(secret, timestamp, nonce, body_bytes)

    request = _BodyRequest(
        body_bytes,
        headers={
            HEADER_AUTH: "secret-token",
            webhook_module.HEADER_WEBHOOK_TIMESTAMP: str(timestamp),
            webhook_module.HEADER_WEBHOOK_NONCE: nonce,
            webhook_module.HEADER_WEBHOOK_SIGNATURE: signature,
        },
    )

    response = await handler(hass, "webhook-test-id", request)
    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 401
    assert body["error"]["code"] == "stale_timestamp"


@pytest.mark.asyncio
async def test_signing_enabled_invalid_signature_returns_401(monkeypatch, hass, coordinator):
    secret = "primary-secret"
    monkeypatch.setenv(webhook_module.ENV_WEBHOOK_SIGNING_SECRET_PRIMARY, secret)

    now = datetime(2026, 3, 6, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(webhook_module, "_utcnow", lambda: now)
    timestamp = int(now.timestamp())
    nonce = "c" * 32

    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    payload = {"type": "status", "data": {"online": True}}
    body_bytes = _json_bytes(payload)
    signature = _signature_header("wrong-secret", timestamp, nonce, body_bytes)

    request = _BodyRequest(
        body_bytes,
        headers={
            HEADER_AUTH: "secret-token",
            webhook_module.HEADER_WEBHOOK_TIMESTAMP: str(timestamp),
            webhook_module.HEADER_WEBHOOK_NONCE: nonce,
            webhook_module.HEADER_WEBHOOK_SIGNATURE: signature,
        },
    )

    response = await handler(hass, "webhook-test-id", request)
    body = _response_json(response)
    _assert_error_contract(response, body)
    assert response.status == 401
    assert body["error"]["code"] == "invalid_signature"


@pytest.mark.asyncio
async def test_signing_enabled_replay_detected_returns_401(monkeypatch, hass, coordinator):
    secret = "primary-secret"
    monkeypatch.setenv(webhook_module.ENV_WEBHOOK_SIGNING_SECRET_PRIMARY, secret)

    now = datetime(2026, 3, 6, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(webhook_module, "_utcnow", lambda: now)
    timestamp = int(now.timestamp())
    nonce = "d" * 32

    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    payload = {"type": "status", "data": {"online": True}}
    body_bytes = _json_bytes(payload)
    signature = _signature_header(secret, timestamp, nonce, body_bytes)

    headers = {
        HEADER_AUTH: "secret-token",
        webhook_module.HEADER_WEBHOOK_TIMESTAMP: str(timestamp),
        webhook_module.HEADER_WEBHOOK_NONCE: nonce,
        webhook_module.HEADER_WEBHOOK_SIGNATURE: signature,
    }

    first = await handler(hass, "webhook-test-id", _BodyRequest(body_bytes, headers=headers))
    assert first.status == 200

    second = await handler(hass, "webhook-test-id", _BodyRequest(body_bytes, headers=headers))
    body = _response_json(second)
    _assert_error_contract(second, body)
    assert second.status == 401
    assert body["error"]["code"] == "replay_detected"


@pytest.mark.asyncio
async def test_signing_key_rotation_accepts_secondary(monkeypatch, hass, coordinator):
    old = "old-secret"
    new = "new-secret"
    monkeypatch.setenv(webhook_module.ENV_WEBHOOK_SIGNING_SECRET_PRIMARY, old)
    monkeypatch.setenv(webhook_module.ENV_WEBHOOK_SIGNING_SECRET_SECONDARY, new)

    now = datetime(2026, 3, 6, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(webhook_module, "_utcnow", lambda: now)
    timestamp = int(now.timestamp())
    nonce = "e" * 32

    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    payload = {"type": "status", "data": {"online": True}}
    body_bytes = _json_bytes(payload)
    signature = _signature_header(new, timestamp, nonce, body_bytes)

    request = _BodyRequest(
        body_bytes,
        headers={
            HEADER_AUTH: "secret-token",
            webhook_module.HEADER_WEBHOOK_TIMESTAMP: str(timestamp),
            webhook_module.HEADER_WEBHOOK_NONCE: nonce,
            webhook_module.HEADER_WEBHOOK_SIGNATURE: signature,
        },
    )

    response = await handler(hass, "webhook-test-id", request)
    assert response.status == 200
    assert _response_json(response) == {"ok": True}
