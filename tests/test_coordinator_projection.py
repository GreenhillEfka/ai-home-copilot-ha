"""Projection contract for coordinator.py ML context hass.data parity.

HA-467: Ensure coordinator.py uses canonical hass.data["pilotsuite"]
lookup, not a hardcoded stale copilot_ha string.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

# tests/ → repo-root (parents[1])
REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_FILE = REPO_ROOT / "custom_components" / "pilotsuite" / "coordinator.py"


def _read_source() -> str:
    """Raw source text of the production module."""
    with open(TARGET_FILE, encoding="utf-8") as f:
        return f.read()


class TestCoordinatorProjection:
    """ML context hass.data reference contract for coordinator.py."""

    def test_cd1_no_stale_copilot_ha_in_get_habit_learning_data(self) -> None:
        """CD1: _get_habit_learning_data uses pilotsuite, not copilot_ha."""
        source = _read_source()
        # Isolate the _get_habit_learning_data method body
        m = re.search(
            r'async def _get_habit_learning_data\(self\).*?(?=\n    async def |\n    def |\Z)',
            source,
            re.DOTALL,
        )
        assert m, "_get_habit_learning_data method not found"
        method_body = m.group(0)
        # Must use pilotsuite, not copilot_ha
        assert "pilotsuite" in method_body, (
            "_get_habit_learning_data must use 'pilotsuite' as the hass.data key"
        )
        assert "copilot_ha" not in method_body, (
            "_get_habit_learning_data must not contain hardcoded 'copilot_ha'; "
            "use 'pilotsuite' instead"
        )

    def test_cd2_ast_scan_no_unexplained_copilot_ha_literal(self) -> None:
        """CD2: AST scan — no unexplained copilot_ha literals in coordinator.py."""
        source = _read_source()
        # These patterns are LEGITIMATE legacy-bridge migration comments, not production refs
        LEGITIMATE = re.compile(r'LEGACY_DOMAIN|llegacy.*copilot_ha|legacy.*mirror|copilot_ha/')
        for lineno, line in enumerate(source.splitlines(), 1):
            if "copilot_ha" in line:
                assert LEGITIMATE.search(line), (
                    f"Line {lineno} contains unexplained copilot_ha literal: {line.strip()}"
                )

    def test_cd3_syntax_ok(self) -> None:
        """CD3: coordinator.py is syntactically valid."""
        source = _read_source()
        try:
            ast.parse(source, filename=str(TARGET_FILE))
        except SyntaxError as e:
            pytest.fail(f"coordinator.py has a SyntaxError: {e}")


class CoreVoiceCommandStateFallbackContract:
    """Mirror the HA idle-safe fallback contract for Core command-state reads."""

    _MAX_SCALAR_LENGTH = 64

    @staticmethod
    def _project_state_shape(command_state_data) -> dict:
        command_state = command_state_data if isinstance(command_state_data, dict) else {}
        pending_confirmation = command_state.get("pending_confirmation")
        last_status = command_state.get("last_status")
        pending_action_label = command_state.get("pending_action_label")
        confirmation_expires_at = command_state.get("confirmation_expires_at")
        return {
            "last_status": last_status[:CoreVoiceCommandStateFallbackContract._MAX_SCALAR_LENGTH]
            if isinstance(last_status, str) and last_status.strip()
            else "idle",
            "pending_confirmation": pending_confirmation if isinstance(pending_confirmation, bool) else False,
            "pending_action_label": pending_action_label[:CoreVoiceCommandStateFallbackContract._MAX_SCALAR_LENGTH]
            if isinstance(pending_action_label, str)
            else "",
            "confirmation_expires_at": confirmation_expires_at[:CoreVoiceCommandStateFallbackContract._MAX_SCALAR_LENGTH]
            if isinstance(confirmation_expires_at, str)
            else None,
        }

    @staticmethod
    def fallback(core_voice_data, *, session_id: str) -> dict:
        payload = core_voice_data if isinstance(core_voice_data, dict) else {}
        response_session_id = payload.get("session_id")

        if payload.get("status") != "ok":
            return CoreVoiceCommandStateFallbackContract._project_state_shape({})
        if not isinstance(response_session_id, str) or response_session_id != session_id:
            return CoreVoiceCommandStateFallbackContract._project_state_shape({})

        return CoreVoiceCommandStateFallbackContract._project_state_shape(payload.get("state"))


@pytest.mark.parametrize(
    ("core_voice_data", "session_id", "expected"),
    [
        (
            {
                "status": "ok",
                "session_id": "home_assistant",
                "state": {
                    "last_status": "confirmation_required",
                    "pending_confirmation": True,
                    "pending_action_label": "Wohnzimmerlicht einschalten",
                    "confirmation_expires_at": "2026-04-27T22:40:00Z",
                    "slot_values": {"_internal": "ignored"},
                },
            },
            "home_assistant",
            {
                "last_status": "confirmation_required",
                "pending_confirmation": True,
                "pending_action_label": "Wohnzimmerlicht einschalten",
                "confirmation_expires_at": "2026-04-27T22:40:00Z",
            },
        ),
        (
            {
                "status": "error",
                "message": "stale state",
                "session_id": "home_assistant",
                "state": {
                    "last_status": "confirmation_required",
                    "pending_confirmation": True,
                    "pending_action_label": "Should not leak",
                    "confirmation_expires_at": "2026-04-27T22:40:00Z",
                },
            },
            "home_assistant",
            {
                "last_status": "idle",
                "pending_confirmation": False,
                "pending_action_label": "",
                "confirmation_expires_at": None,
            },
        ),
        (
            {
                "status": "ok",
                "session_id": "other-session",
                "state": {
                    "last_status": "confirmation_required",
                    "pending_confirmation": True,
                    "pending_action_label": "Wrong session",
                    "confirmation_expires_at": "2026-04-27T22:40:00Z",
                },
            },
            "home_assistant",
            {
                "last_status": "idle",
                "pending_confirmation": False,
                "pending_action_label": "",
                "confirmation_expires_at": None,
            },
        ),
        (
            {
                "status": "ok",
                "session_id": "home_assistant",
                "state": {
                    "last_status": ["bad"],
                    "pending_confirmation": "yes",
                    "pending_action_label": {"bad": True},
                    "confirmation_expires_at": 123,
                },
            },
            "home_assistant",
            {
                "last_status": "idle",
                "pending_confirmation": False,
                "pending_action_label": "",
                "confirmation_expires_at": None,
            },
        ),
        (
            {"status": "ok", "session_id": "home_assistant", "state": "bad"},
            "home_assistant",
            {
                "last_status": "idle",
                "pending_confirmation": False,
                "pending_action_label": "",
                "confirmation_expires_at": None,
            },
        ),
        (
            {
                "status": "ok",
                "session_id": "home_assistant",
                "state": {
                    "last_status": "confirmation_required" * 5,
                    "pending_confirmation": True,
                    "pending_action_label": "Wohnzimmerlicht einschalten " * 4,
                    "confirmation_expires_at": "2026-04-27T22:40:00Z" * 4,
                },
            },
            "home_assistant",
            {
                "last_status": ("confirmation_required" * 5)[:64],
                "pending_confirmation": True,
                "pending_action_label": ("Wohnzimmerlicht einschalten " * 4)[:64],
                "confirmation_expires_at": ("2026-04-27T22:40:00Z" * 4)[:64],
            },
        ),
        (
            ["bad-payload"],
            "home_assistant",
            {
                "last_status": "idle",
                "pending_confirmation": False,
                "pending_action_label": "",
                "confirmation_expires_at": None,
            },
        ),
    ],
)
def test_cd4_core_voice_command_state_fallback_contract(core_voice_data, session_id, expected) -> None:
    """CD4: stale, malformed, or wrong-session command-state reads collapse to one idle-safe shape."""
    assert CoreVoiceCommandStateFallbackContract.fallback(
        core_voice_data,
        session_id=session_id,
    ) == expected


def test_cd5_source_locks_core_voice_command_state_fallback_to_one_idle_safe_shape() -> None:
    """CD5: coordinator.py normalizes Core command-state reads before exposing HA attrs."""
    source = _read_source()

    assert '_VOICE_COMMAND_STATE_MAX_SCALAR_LENGTH = 64' in source
    assert 'def _project_core_voice_command_state(core_voice_data: Any, *, session_id: str) -> dict[str, Any]:' in source
    assert 'if payload.get("status") != "ok":' in source
    assert 'if not isinstance(response_session_id, str) or response_session_id != session_id:' in source
    assert 'last_status[:_VOICE_COMMAND_STATE_MAX_SCALAR_LENGTH]' in source
    assert 'pending_action_label[:_VOICE_COMMAND_STATE_MAX_SCALAR_LENGTH]' in source
    assert 'confirmation_expires_at[:_VOICE_COMMAND_STATE_MAX_SCALAR_LENGTH]' in source
    assert 'return _project_voice_command_state_shape(payload.get("state"))' in source
    assert 'return _project_core_voice_command_state(data, session_id=session_id)' in source
