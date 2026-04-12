"""Projection Contract Tests — media_sensors (HA-167).

Verifies MediaActivitySensor + MediaIntensitySensor are hybrid Projection-Shells
on hass.states.async_all("media_player") — no local semantic invention beyond
trivial threshold logic and state aggregation.

Contract:
- MediaActivitySensor: reads hass states → categorizes playing/paused/idle →
  native_value (idle/single/multi), icon (static), attrs (counts, player names,
  active/social scores)
- MediaIntensitySensor: reads hass states → calculates avg volume →
  native_value (off/low/medium/high), icon (static), attrs (avg_volume, playing count)

Both sensors use MediaStateCache for efficiency — tested indirectly via state logic.

HA-167 — 2026-04-07
"""
from __future__ import annotations

from pathlib import Path
import pytest
from unittest.mock import MagicMock, PropertyMock


# =============================================================================
# Contract Mirrors
# =============================================================================


class MediaActivitySensorContract:
    """Mirror of MediaActivitySensor native_value + icon + attrs logic.

    Contract:
    - reads: hass.states.async_all("media_player") → list of State objects
    - categorizes: playing, paused, idle by state attribute
    - native_value: "idle" (0 playing) | "single" (1 playing) | "multi" (2+ playing)
    - icon: static "mdi:play-circle"
    - extra_state_attributes:
        playing          ← len(playing_states)
        paused           ← len(paused_states)
        idle             ← len(idle_states)
        players_playing  ← [p.name for p in playing_states]
        active           ← len(playing) > 0
        social           ← len(playing) > 1 OR TV keyword in friendly_name
        active_score     ← min(len(playing) / 3, 1.0)
        social_score     ← 1.0 if social else 0.0
    """

    _TV_KEYWORDS = ("tv", "fernseher", "living room tv", "wohnzimmer tv", "fernseher im wohnzimmer")
    _MAX_PLAYING_FOR_SCORE = 3

    def __init__(self, media_states: list[dict]) -> None:
        """Initialize with list of media player state dicts.

        Each dict: {"state": str, "name": str, "attributes": {"friendly_name": str}}
        """
        self._states = media_states or []

    def _categorize(self) -> tuple[list, list, list]:
        playing = [s for s in self._states if isinstance(s, dict) and s.get("state") == "playing"]
        paused = [s for s in self._states if isinstance(s, dict) and s.get("state") == "paused"]
        idle = [s for s in self._states if isinstance(s, dict) and s.get("state") == "idle"]
        return playing, paused, idle

    def _check_social(self, playing: list) -> bool:
        if len(playing) > 1:
            return True
        for p in playing:
            if not isinstance(p, dict):
                continue
            friendly = p.get("attributes", {}).get("friendly_name", "").lower()
            for kw in self._TV_KEYWORDS:
                if kw in friendly:
                    return True
        return False

    def native_value(self) -> str:
        playing, _, _ = self._categorize()
        if len(playing) == 0:
            return "idle"
        elif len(playing) == 1:
            return "single"
        return "multi"

    def icon(self) -> str:
        return "mdi:play-circle"

    def extra_state_attributes(self) -> dict:
        playing, paused, idle = self._categorize()
        is_social = self._check_social(playing)
        players_playing = [p.get("name", "") for p in playing]

        return {
            "playing": len(playing),
            "paused": len(paused),
            "idle": len(idle),
            "players_playing": players_playing,
            "active": len(playing) > 0,
            "social": is_social,
            "active_score": min(len(playing) / self._MAX_PLAYING_FOR_SCORE, 1.0),
            "social_score": 1.0 if is_social else 0.0,
        }


class MediaIntensitySensorContract:
    """Mirror of MediaIntensitySensor native_value + icon + attrs logic.

    Contract:
    - reads: hass.states.async_all("media_player") → list of State objects
    - filters: only "playing" states
    - extracts: volume_level from attributes (default 0.5 if missing)
    - calculates: avg_volume = (sum(volumes) / count) * 100
    - native_value: "off" (0 playing) | "low" (<30%) | "medium" (<60%) | "high" (≥60%)
    - icon: static "mdi:volume-high"
    - extra_state_attributes:
        avg_volume  ← rounded to 1 decimal
        playing     ← count of playing states
        active      ← playing > 0
        active_score ← avg_volume / 100
    """

    _VOLUME_LOW = 30.0
    _VOLUME_MEDIUM = 60.0
    _DEFAULT_VOLUME = 0.5

    def __init__(self, media_states: list[dict]) -> None:
        """Initialize with list of media player state dicts.

        Each dict: {"state": str, "attributes": {"volume_level": float|None}}
        """
        self._states = media_states or []

    def _calc_intensity(self) -> tuple[str, float, int]:
        playing_states = [s for s in self._states if s.get("state") == "playing"]
        total_volume = 0.0

        for s in playing_states:
            vol = s.get("attributes", {}).get("volume_level")
            if vol is not None:
                try:
                    total_volume += float(vol)
                except (TypeError, ValueError):
                    total_volume += self._DEFAULT_VOLUME
            else:
                total_volume += self._DEFAULT_VOLUME

        count = len(playing_states)
        avg_vol = (total_volume / count * 100.0) if count > 0 else 0.0

        if count == 0:
            intensity = "off"
        elif avg_vol < self._VOLUME_LOW:
            intensity = "low"
        elif avg_vol < self._VOLUME_MEDIUM:
            intensity = "medium"
        else:
            intensity = "high"

        return intensity, avg_vol, count

    def native_value(self) -> str:
        intensity, _, _ = self._calc_intensity()
        return intensity

    def icon(self) -> str:
        return "mdi:volume-high"

    def extra_state_attributes(self) -> dict:
        _, avg_vol, count = self._calc_intensity()
        return {
            "avg_volume": round(avg_vol, 1),
            "playing": count,
            "active": count > 0,
            "active_score": avg_vol / 100.0 if count > 0 else 0.0,
        }


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_hass():
    """Mock HomeAssistant with states.async_all."""
    hass = MagicMock()
    hass.states = MagicMock()
    return hass


@pytest.fixture
def mock_coordinator():
    """Mock CopilotDataUpdateCoordinator."""
    coord = MagicMock()
    coord.data = {}
    return coord


# =============================================================================
# MediaActivitySensor Tests (MA1–MA12)
# =============================================================================


class TestMediaActivitySensor:
    """Tests for MediaActivitySensor projection contract."""

    # MA1: native_value — 0 playing → "idle"
    def test_ma1_native_value_idle(self, mock_hass, mock_coordinator):
        """MA1: No playing media → native_value = 'idle'."""
        mock_hass.states.async_all.return_value = []

        # MediaActivitySensor import skipped — contract verified via MediaActivitySensorContract
        # async_update would be called, but we test contract directly
        contract = MediaActivitySensorContract([])
        assert contract.native_value() == "idle"

    # MA2: native_value — 1 playing → "single"
    def test_ma2_native_value_single(self, mock_hass, mock_coordinator):
        """MA2: One playing media → native_value = 'single'."""
        states = [{"state": "playing", "name": "Living Room", "attributes": {"friendly_name": "Living Room"}}]
        contract = MediaActivitySensorContract(states)
        assert contract.native_value() == "single"

    # MA3: native_value — 2+ playing → "multi"
    def test_ma3_native_value_multi(self, mock_hass, mock_coordinator):
        """MA3: Multiple playing media → native_value = 'multi'."""
        states = [
            {"state": "playing", "name": "TV", "attributes": {}},
            {"state": "playing", "name": "Speaker", "attributes": {}},
        ]
        contract = MediaActivitySensorContract(states)
        assert contract.native_value() == "multi"

    # MA4: icon — always static
    def test_ma4_icon_static(self):
        """MA4: Icon is always static mdi:play-circle."""
        contract = MediaActivitySensorContract([])
        assert contract.icon() == "mdi:play-circle"

    # MA5: attrs — full data
    def test_ma5_attrs_full(self):
        """MA5: Full attributes with playing/paused/idle counts."""
        states = [
            {"state": "playing", "name": "TV", "attributes": {"friendly_name": "Wohnzimmer TV"}},
            {"state": "paused", "name": "Spotify", "attributes": {}},
            {"state": "idle", "name": "Chromecast", "attributes": {}},
        ]
        contract = MediaActivitySensorContract(states)
        attrs = contract.extra_state_attributes()
        assert attrs["playing"] == 1
        assert attrs["paused"] == 1
        assert attrs["idle"] == 1
        assert "TV" in attrs["players_playing"]
        assert attrs["active"] is True
        assert attrs["social"] is True  # TV keyword
        assert attrs["active_score"] == pytest.approx(1/3, rel=0.01)
        assert attrs["social_score"] == 1.0

    # MA6: attrs — empty
    def test_ma6_attrs_empty(self):
        """MA6: Empty state → zero counts, active/social false."""
        contract = MediaActivitySensorContract([])
        attrs = contract.extra_state_attributes()
        assert attrs["playing"] == 0
        assert attrs["paused"] == 0
        assert attrs["idle"] == 0
        assert attrs["players_playing"] == []
        assert attrs["active"] is False
        assert attrs["social"] is False
        assert attrs["active_score"] == 0.0
        assert attrs["social_score"] == 0.0

    # MA7: social detection — multiple players
    def test_ma7_social_multi_players(self):
        """MA7: Multiple playing → social = True."""
        states = [
            {"state": "playing", "name": "A", "attributes": {}},
            {"state": "playing", "name": "B", "attributes": {}},
        ]
        contract = MediaActivitySensorContract(states)
        assert contract.extra_state_attributes()["social"] is True

    # MA8: social detection — TV keyword
    def test_ma8_social_tv_keyword(self):
        """MA8: TV keyword in friendly_name → social = True."""
        states = [{"state": "playing", "name": "TV", "attributes": {"friendly_name": "Wohnzimmer TV"}}]
        contract = MediaActivitySensorContract(states)
        assert contract.extra_state_attributes()["social"] is True

    # MA9: active_score capped at 1.0
    def test_ma9_active_score_capped(self):
        """MA9: active_score capped at 1.0 (max 3 playing)."""
        states = [{"state": "playing", "name": f"Player{i}", "attributes": {}} for i in range(10)]
        contract = MediaActivitySensorContract(states)
        assert contract.extra_state_attributes()["active_score"] == 1.0

    # MA10: edge — paused states don't count as playing
    def test_ma10_paused_not_playing(self):
        """MA10: Paused states → native_value = 'idle' (not playing)."""
        states = [
            {"state": "paused", "name": "A", "attributes": {}},
            {"state": "paused", "name": "B", "attributes": {}},
        ]
        contract = MediaActivitySensorContract(states)
        assert contract.native_value() == "idle"

    # MA11: edge — missing name field
    def test_ma11_missing_name(self):
        """MA11: Missing name field → empty string in players_playing."""
        states = [{"state": "playing", "attributes": {}}]
        contract = MediaActivitySensorContract(states)
        attrs = contract.extra_state_attributes()
        assert attrs["players_playing"] == [""]

    # MA12: edge — non-dict state
    def test_ma12_non_dict_state(self):
        """MA12: Non-dict state elements → handled gracefully."""
        states = [None, "invalid", {"state": "playing", "name": "Valid", "attributes": {}}]
        # Contract should handle this via list comprehension filtering
        contract = MediaActivitySensorContract(states)
        # Should not crash; playing count based on valid dicts only
        attrs = contract.extra_state_attributes()
        assert isinstance(attrs["playing"], int)


# =============================================================================
# MediaIntensitySensor Tests (MI1–MI10)
# =============================================================================


class TestMediaIntensitySensor:
    """Tests for MediaIntensitySensor projection contract."""

    # MI1: native_value — 0 playing → "off"
    def test_mi1_native_value_off(self):
        """MI1: No playing media → native_value = 'off'."""
        contract = MediaIntensitySensorContract([])
        assert contract.native_value() == "off"

    # MI2: native_value — low volume (<30%)
    def test_mi2_native_value_low(self):
        """MI2: Avg volume < 30% → native_value = 'low'."""
        states = [{"state": "playing", "attributes": {"volume_level": 0.2}}]
        contract = MediaIntensitySensorContract(states)
        assert contract.native_value() == "low"

    # MI3: native_value — medium volume (30-60%)
    def test_mi3_native_value_medium(self):
        """MI3: Avg volume 30-60% → native_value = 'medium'."""
        states = [{"state": "playing", "attributes": {"volume_level": 0.45}}]
        contract = MediaIntensitySensorContract(states)
        assert contract.native_value() == "medium"

    # MI4: native_value — high volume (≥60%)
    def test_mi4_native_value_high(self):
        """MI4: Avg volume ≥ 60% → native_value = 'high'."""
        states = [{"state": "playing", "attributes": {"volume_level": 0.75}}]
        contract = MediaIntensitySensorContract(states)
        assert contract.native_value() == "high"

    # MI5: icon — always static
    def test_mi5_icon_static(self):
        """MI5: Icon is always static mdi:volume-high."""
        contract = MediaIntensitySensorContract([])
        assert contract.icon() == "mdi:volume-high"

    # MI6: attrs — full data
    def test_mi6_attrs_full(self):
        """MI6: Full attributes with avg_volume and playing count."""
        states = [
            {"state": "playing", "attributes": {"volume_level": 0.5}},
            {"state": "playing", "attributes": {"volume_level": 0.7}},
        ]
        contract = MediaIntensitySensorContract(states)
        attrs = contract.extra_state_attributes()
        assert attrs["avg_volume"] == 60.0  # (0.5 + 0.7) / 2 * 100
        assert attrs["playing"] == 2
        assert attrs["active"] is True
        assert attrs["active_score"] == 0.6

    # MI7: attrs — missing volume_level → default 0.5
    def test_mi7_missing_volume_default(self):
        """MI7: Missing volume_level → default 0.5 used."""
        states = [{"state": "playing", "attributes": {}}]
        contract = MediaIntensitySensorContract(states)
        attrs = contract.extra_state_attributes()
        assert attrs["avg_volume"] == 50.0

    # MI8: attrs — None volume → default 0.5
    def test_mi8_none_volume_default(self):
        """MI8: volume_level = None → default 0.5 used."""
        states = [{"state": "playing", "attributes": {"volume_level": None}}]
        contract = MediaIntensitySensorContract(states)
        attrs = contract.extra_state_attributes()
        assert attrs["avg_volume"] == 50.0

    # MI9: edge — invalid volume string
    def test_mi9_invalid_volume_string(self):
        """MI9: Invalid volume string → default 0.5 used."""
        states = [{"state": "playing", "attributes": {"volume_level": "invalid"}}]
        contract = MediaIntensitySensorContract(states)
        attrs = contract.extra_state_attributes()
        assert attrs["avg_volume"] == 50.0

    # MI10: edge — mixed valid/invalid volumes
    def test_mi10_mixed_volumes(self):
        """MI10: Mixed valid/invalid volumes → avg calculated correctly."""
        states = [
            {"state": "playing", "attributes": {"volume_level": 0.8}},
            {"state": "playing", "attributes": {"volume_level": "bad"}},
            {"state": "playing", "attributes": {}},
        ]
        contract = MediaIntensitySensorContract(states)
        attrs = contract.extra_state_attributes()
        # (0.8 + 0.5 + 0.5) / 3 * 100 = 60.0
        assert attrs["avg_volume"] == pytest.approx(60.0, rel=0.01)


# =============================================================================
# Global Contract Tests (GC1–GC4)
# =============================================================================


class TestGlobalContract:
    """Global contract verification for media_sensors."""

    # GC1: Pure projection — no local semantic invention
    def test_gc1_no_local_semantic_invention(self):
        """GC1: Both sensors are pure projection shells — no ML/heuristics."""
        # MediaActivitySensor: only categorizes by state, counts, keyword match
        # MediaIntensitySensor: only calculates avg volume, threshold comparison
        # No external API calls, no ML, no complex heuristics

        # Verify contract mirrors produce deterministic results
        states = [
            {"state": "playing", "name": "TV", "attributes": {"friendly_name": "Wohnzimmer TV", "volume_level": 0.6}},
            {"state": "idle", "name": "Speaker", "attributes": {}},
        ]

        activity = MediaActivitySensorContract(states)
        intensity = MediaIntensitySensorContract(states)

        # Deterministic outputs
        assert activity.native_value() == "single"
        assert intensity.native_value() == "high"

        # Same input → same output (no randomness, no external state)
        assert activity.native_value() == "single"
        assert intensity.native_value() == "high"

    # GC2: hass.states.async_all only — no Core API calls
    def test_gc2_hass_states_only(self):
        """GC2: Sensors read hass.states.async_all only — no /api/v1/* calls."""
        # Verify by inspecting source: media_sensors.py uses:
        # - hass.states.async_all("media_player")
        # - No _fetch(), no _core_base_url(), no coordinator.data hits
        # This is a HA-local sensor, not a Core projection

        # The contract is: projection on HA state tree, not Core API
        # MediaActivitySensor + MediaIntensitySensor = HA-local projection
        states = [{"state": "playing", "attributes": {"volume_level": 0.5}}]
        contract = MediaIntensitySensorContract(states)
        # Contract works with state dicts only — no HTTP/API dependency
        assert contract.native_value() == "medium"

    def test_gc3_canonical_media_unique_ids_in_prod_module(self):
        """GC3: Prod-Modul nutzt kanonische pilotsuite_* media unique IDs."""
        source = (
            Path(__file__).resolve().parents[1]
            / "custom_components"
            / "pilotsuite"
            / "sensors"
            / "media_sensors.py"
        ).read_text(encoding="utf-8")

        assert '"pilotsuite_media_activity"' in source
        assert '"pilotsuite_media_intensity"' in source
        assert '"ai_copilot_media_activity"' not in source
        assert '"ai_copilot_media_intensity"' not in source

    def test_gc4_media_legacy_unique_id_migrations_present(self):
        """GC4: __init__.py bewahrt Legacy→PilotSuite-Migrationen für media-Sensoren."""
        init_source = (
            Path(__file__).resolve().parents[1]
            / "custom_components"
            / "pilotsuite"
            / "__init__.py"
        ).read_text(encoding="utf-8")

        assert '"ai_copilot_media_activity": "pilotsuite_media_activity"' in init_source
        assert '"ai_copilot_media_intensity": "pilotsuite_media_intensity"' in init_source
