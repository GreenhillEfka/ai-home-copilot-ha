"""Projection Contract Tests — voice_status_sensor.

Verifies VoiceStatusSensor is a pure projection shell on Core
`/api/v1/styx/voice/status` truth.
"""

from __future__ import annotations

import pytest


# Contract mirror

def _as_mapping(val, default=None):
    if isinstance(val, dict):
        return val
    return default if default is not None else {}


def _as_list(val, default=None):
    if isinstance(val, list):
        return val
    return default if default is not None else []


def _as_string(val, default=""):
    if isinstance(val, str):
        normalized = val.strip()
        if normalized:
            return normalized
    return default


def _as_bool(val, default=False):
    return bool(val) if isinstance(val, bool) else default


class VoiceStatusSensorContract:
    @staticmethod
    def native_value(api_response) -> str:
        data = _as_mapping(api_response)
        stt = _as_mapping(data.get("stt"))
        tts = _as_mapping(data.get("tts"))
        stt_available = _as_bool(stt.get("available"), False)
        tts_available = _as_bool(tts.get("available"), False)
        if stt_available and tts_available:
            return "ready"
        if stt_available or tts_available:
            return "degraded"
        return "offline"

    @staticmethod
    def icon(api_response) -> str:
        status = VoiceStatusSensorContract.native_value(api_response)
        if status == "ready":
            return "mdi:microphone-message"
        if status == "degraded":
            return "mdi:microphone-message-off"
        return "mdi:microphone-off"

    @staticmethod
    def extra_state_attributes(api_response) -> dict:
        data = _as_mapping(api_response)
        stt = _as_mapping(data.get("stt"))
        tts = _as_mapping(data.get("tts"))
        supported_languages = [_as_string(v) for v in _as_list(data.get("supported_languages"), [])]
        supported_languages = [v for v in supported_languages if v]
        return {
            "ok": _as_bool(data.get("ok"), False),
            "stt_available": _as_bool(stt.get("available"), False),
            "tts_available": _as_bool(tts.get("available"), False),
            "stt_backend": _as_string(stt.get("backend"), _as_string(stt.get("provider"), "")),
            "tts_backend": _as_string(tts.get("backend"), _as_string(tts.get("provider"), "")),
            "supported_languages": supported_languages,
        }


@pytest.mark.parametrize(
    "api_response,expected",
    [
        ({"stt": {"available": True}, "tts": {"available": True}}, "ready"),
        ({"stt": {"available": True}, "tts": {"available": False}}, "degraded"),
        ({"stt": {"available": False}, "tts": {"available": True}}, "degraded"),
        ({"stt": {"available": False}, "tts": {"available": False}}, "offline"),
        ({}, "offline"),
    ],
)
def test_vs1_native_value(api_response, expected):
    assert VoiceStatusSensorContract.native_value(api_response) == expected


@pytest.mark.parametrize(
    "api_response,expected_icon",
    [
        ({"stt": {"available": True}, "tts": {"available": True}}, "mdi:microphone-message"),
        ({"stt": {"available": True}, "tts": {"available": False}}, "mdi:microphone-message-off"),
        ({"stt": {"available": False}, "tts": {"available": False}}, "mdi:microphone-off"),
        ({}, "mdi:microphone-off"),
    ],
)
def test_vs2_icon(api_response, expected_icon):
    assert VoiceStatusSensorContract.icon(api_response) == expected_icon


@pytest.mark.parametrize(
    "api_response,attr_key,expected",
    [
        ({"ok": True}, "ok", True),
        ({"stt": {"available": True}}, "stt_available", True),
        ({"tts": {"available": True}}, "tts_available", True),
        ({"stt": {"backend": "whisper"}}, "stt_backend", "whisper"),
        ({"tts": {"provider": "edge-tts"}}, "tts_backend", "edge-tts"),
        ({"supported_languages": ["de", "en"]}, "supported_languages", ["de", "en"]),
    ],
)
def test_vs3_attribute_passthrough(api_response, attr_key, expected):
    attrs = VoiceStatusSensorContract.extra_state_attributes(api_response)
    assert attrs[attr_key] == expected


@pytest.mark.parametrize(
    "api_response,expected_attrs",
    [
        (
            {},
            {
                "ok": False,
                "stt_available": False,
                "tts_available": False,
                "stt_backend": "",
                "tts_backend": "",
                "supported_languages": [],
            },
        ),
        (
            {
                "ok": "yes",
                "stt": {"available": "true", "backend": 123},
                "tts": {"available": None, "provider": "  edge-tts  "},
                "supported_languages": ["de", 42, None, "  en  ", "  "],
            },
            {
                "ok": False,
                "stt_available": False,
                "tts_available": False,
                "stt_backend": "",
                "tts_backend": "edge-tts",
                "supported_languages": ["de", "en"],
            },
        ),
    ],
)
def test_vs4_edge_cases(api_response, expected_attrs):
    assert VoiceStatusSensorContract.extra_state_attributes(api_response) == expected_attrs
