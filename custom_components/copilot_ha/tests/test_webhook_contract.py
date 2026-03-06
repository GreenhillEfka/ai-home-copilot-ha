"""Contract tests for Core -> HA webhook envelope validation."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from custom_components.copilot_ha import webhook as webhook_module
from custom_components.copilot_ha.const import CONF_TOKEN, CONF_WEBHOOK_ID, HEADER_AUTH


class _FakeRequest:
    def __init__(self, payload, headers: dict[str, str] | None = None):
        self._payload = payload
        self.headers = headers or {}

    async def json(self):
        return self._payload


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


@pytest.mark.asyncio
async def test_missing_type_returns_400_with_structured_error(hass, coordinator):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"data": {"online": True}},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
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
    assert response.status == 400
    assert body["ok"] is False
    assert body["error"]["code"] == "missing_data"
    assert body["error"]["details"]["required_field"] == "data"


@pytest.mark.asyncio
async def test_unknown_type_returns_400_with_structured_error(hass, coordinator):
    handler = await _capture_registered_handler(hass, _make_entry(), coordinator)

    request = _FakeRequest(
        payload={"type": "mystery_event", "data": {}},
        headers={HEADER_AUTH: "secret-token"},
    )
    response = await handler(hass, "webhook-test-id", request)

    body = _response_json(response)
    assert response.status == 400
    assert body["ok"] is False
    assert body["error"]["code"] == "unknown_type"
    assert body["error"]["details"]["received"] == "mystery_event"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("event_type", "data"),
    [
        ("status", {"online": True, "version": "13.5.0"}),
        ("mood", {"mood": "calm", "confidence": 0.9}),
        ("neuron", {"neurons": {"n1": {"active": True}}}),
        ("suggestion", {"title": "Test suggestion", "action": "noop"}),
    ],
)
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
