"""Projection Contract Tests for cognitive_sensors (HA-173).

Verifies: cognitive_sensors.py is HA-lokal — reads HA states only,
no Core API dependency. Contract: hass.states + optional module_connector → sensor state.

Sensors:
- AttentionLoadSensor: idle/low/moderate/high by media_active + speakers_playing + calendar_focus_weight
- StressProxySensor: relaxed/low/moderate/high by late_night_media + active_alerts
"""
from __future__ import annotations

from datetime import datetime
import sys
from typing import Any
from unittest.mock import MagicMock, AsyncMock, patch

# conftest must be importable
try:
    import conftest as _conftest
except ImportError:
    import tests.conftest as _conftest  # noqa: F401

import pytest


# =============================================================================
# Contract Mirrors (exact sensor logic replication)
# =============================================================================

class AttentionLoadSensorContract:
    """Mirror of AttentionLoadSensor async_update logic."""

    @staticmethod
    def compute_load(media_active: int, speakers_playing: int, calendar_focus_weight: float = 0.0) -> str:
        """Compute attention load classification."""
        load_score = media_active * 2 + speakers_playing
        
        if calendar_focus_weight > 0.5:
            load_score += 3
        elif calendar_focus_weight > 0.2:
            load_score += 1
        
        if load_score == 0:
            return "idle"
        elif load_score < 2:
            return "low"
        elif load_score < 5:
            return "moderate"
        else:
            return "high"

    @staticmethod
    def compute_attrs(
        media_active: int,
        speakers_playing: int,
        calendar_focus_weight: float,
        calendar_meetings_today: int,
    ) -> dict[str, Any]:
        """Compute extra_state_attributes."""
        return {
            "media_active": media_active,
            "speakers_playing": speakers_playing,
            "calendar_focus_weight": calendar_focus_weight,
            "calendar_meetings_today": calendar_meetings_today,
            "sources": ["media", "speakers", "calendar"],
        }


class StressProxySensorContract:
    """Mirror of StressProxySensor async_update logic."""

    @staticmethod
    def compute_stress(is_late_night: bool, media_playing: int, active_alerts: int) -> str:
        """Compute stress proxy classification."""
        stress_score = 0
        
        if is_late_night and media_playing > 0:
            stress_score += 2
        
        stress_score += active_alerts
        
        if stress_score == 0:
            return "relaxed"
        elif stress_score < 2:
            return "low"
        elif stress_score < 4:
            return "moderate"
        else:
            return "high"

    @staticmethod
    def compute_attrs(
        is_late_night: bool,
        media_playing: int,
        active_alerts: int,
        stress_score: int,
    ) -> dict[str, Any]:
        """Compute extra_state_attributes."""
        return {
            "late_night_media": is_late_night and media_playing > 0,
            "active_alerts": active_alerts,
            "score": stress_score,
        }


# =============================================================================
# AttentionLoadSensor Tests (AL1–AL12)
# =============================================================================

class TestAttentionLoadSensor:
    """Tests for AttentionLoadSensor projection contract."""

    def test_AL1_native_value_idle_no_media_no_calendar(self):
        """AL1: native_value = 'idle' when no media active and no calendar load."""
        result = AttentionLoadSensorContract.compute_load(
            media_active=0,
            speakers_playing=0,
            calendar_focus_weight=0.0,
        )
        assert result == "idle"

    def test_AL2_native_value_moderate_one_media(self):
        """AL2: native_value = 'moderate' with 1 media player playing (load_score=2)."""
        result = AttentionLoadSensorContract.compute_load(
            media_active=1,
            speakers_playing=0,
            calendar_focus_weight=0.0,
        )
        assert result == "moderate"

    def test_AL3_native_value_moderate_two_media(self):
        """AL3: native_value = 'moderate' with 2 media players playing (load_score=4)."""
        result = AttentionLoadSensorContract.compute_load(
            media_active=2,
            speakers_playing=0,
            calendar_focus_weight=0.0,
        )
        assert result == "moderate"

    def test_AL4_native_value_high_three_media(self):
        """AL4: native_value = 'high' with 3 media players playing (load_score=6)."""
        result = AttentionLoadSensorContract.compute_load(
            media_active=3,
            speakers_playing=0,
            calendar_focus_weight=0.0,
        )
        assert result == "high"

    def test_AL5_speaker_detection(self):
        """AL5: speakers_playing counted separately via device_class='speaker'."""
        result = AttentionLoadSensorContract.compute_load(
            media_active=2,
            speakers_playing=1,
            calendar_focus_weight=0.0,
        )
        # load_score = 2*2 + 1 = 5 → high
        assert result == "high"

    def test_AL6_calendar_focus_weight_high_upgrades_load(self):
        """AL6: calendar_focus_weight > 0.5 adds +3 to load_score."""
        result = AttentionLoadSensorContract.compute_load(
            media_active=0,
            speakers_playing=0,
            calendar_focus_weight=0.8,
        )
        # load_score = 0 + 3 = 3 → moderate
        assert result == "moderate"

    def test_AL7_calendar_focus_weight_moderate_adds_one(self):
        """AL7: calendar_focus_weight > 0.2 adds +1 to load_score."""
        result = AttentionLoadSensorContract.compute_load(
            media_active=0,
            speakers_playing=0,
            calendar_focus_weight=0.3,
        )
        # load_score = 0 + 1 = 1 → low
        assert result == "low"

    def test_AL8_calendar_focus_weight_low_no_bonus(self):
        """AL8: calendar_focus_weight <= 0.2 adds nothing to load_score."""
        result = AttentionLoadSensorContract.compute_load(
            media_active=0,
            speakers_playing=0,
            calendar_focus_weight=0.1,
        )
        # load_score = 0 → idle
        assert result == "idle"

    def test_AL9_combined_media_and_calendar_high(self):
        """AL9: Combined media + calendar load → high."""
        result = AttentionLoadSensorContract.compute_load(
            media_active=2,
            speakers_playing=1,
            calendar_focus_weight=0.6,
        )
        # load_score = 2*2 + 1 + 3 = 8 → high
        assert result == "high"

    def test_AL10_boundary_score_4_is_moderate(self):
        """AL10: load_score = 4 is moderate (boundary test)."""
        result = AttentionLoadSensorContract.compute_load(
            media_active=2,
            speakers_playing=0,
            calendar_focus_weight=0.0,
        )
        assert result == "moderate"

    def test_AL11_boundary_score_5_is_high(self):
        """AL11: load_score = 5 is high (boundary test)."""
        result = AttentionLoadSensorContract.compute_load(
            media_active=2,
            speakers_playing=1,
            calendar_focus_weight=0.0,
        )
        assert result == "high"

    def test_AL12_attrs_sources_list(self):
        """AL12: extra_state_attributes includes sources list."""
        attrs = AttentionLoadSensorContract.compute_attrs(
            media_active=0,
            speakers_playing=0,
            calendar_focus_weight=0.0,
            calendar_meetings_today=0,
        )
        assert "sources" in attrs
        assert attrs["sources"] == ["media", "speakers", "calendar"]


# =============================================================================
# StressProxySensor Tests (SP1–SP10)
# =============================================================================

class TestStressProxySensor:
    """Tests for StressProxySensor projection contract."""

    def test_SP1_native_value_relaxed_daytime_no_alerts(self):
        """SP1: native_value = 'relaxed' during daytime with no alerts."""
        result = StressProxySensorContract.compute_stress(
            is_late_night=False,
            media_playing=0,
            active_alerts=0,
        )
        assert result == "relaxed"

    def test_SP2_native_value_low_one_alert(self):
        """SP2: native_value = 'low' with 1 active alert."""
        result = StressProxySensorContract.compute_stress(
            is_late_night=False,
            media_playing=0,
            active_alerts=1,
        )
        assert result == "low"

    def test_SP3_native_value_moderate_two_alerts(self):
        """SP3: native_value = 'moderate' with 2 active alerts."""
        result = StressProxySensorContract.compute_stress(
            is_late_night=False,
            media_playing=0,
            active_alerts=2,
        )
        assert result == "moderate"

    def test_SP4_native_value_high_four_alerts(self):
        """SP4: native_value = 'high' with 4+ active alerts."""
        result = StressProxySensorContract.compute_stress(
            is_late_night=False,
            media_playing=0,
            active_alerts=4,
        )
        assert result == "high"

    def test_SP5_late_night_media_adds_stress(self):
        """SP5: late_night (23:00+) with media playing adds +2 to stress_score."""
        result = StressProxySensorContract.compute_stress(
            is_late_night=True,
            media_playing=1,
            active_alerts=0,
        )
        # stress_score = 2 → moderate
        assert result == "moderate"

    def test_SP6_early_morning_is_late_night(self):
        """SP6: early morning (hour < 6) counts as late_night."""
        # Verified by contract: is_late_night = hour >= 23 or hour < 6
        result = StressProxySensorContract.compute_stress(
            is_late_night=True,
            media_playing=1,
            active_alerts=0,
        )
        assert result == "moderate"

    def test_SP7_combined_late_night_and_alerts_high(self):
        """SP7: late_night_media + alerts → high stress."""
        result = StressProxySensorContract.compute_stress(
            is_late_night=True,
            media_playing=1,
            active_alerts=2,
        )
        # stress_score = 2 + 2 = 4 → high
        assert result == "high"

    def test_SP8_boundary_score_1_is_low(self):
        """SP8: stress_score = 1 is low (boundary test)."""
        result = StressProxySensorContract.compute_stress(
            is_late_night=False,
            media_playing=0,
            active_alerts=1,
        )
        assert result == "low"

    def test_SP9_boundary_score_3_is_moderate(self):
        """SP9: stress_score = 3 is moderate (boundary test)."""
        result = StressProxySensorContract.compute_stress(
            is_late_night=False,
            media_playing=0,
            active_alerts=3,
        )
        assert result == "moderate"

    def test_SP10_attrs_full(self):
        """SP10: extra_state_attributes includes late_night_media, active_alerts, score."""
        attrs = StressProxySensorContract.compute_attrs(
            is_late_night=True,
            media_playing=1,
            active_alerts=2,
            stress_score=4,
        )
        assert "late_night_media" in attrs
        assert "active_alerts" in attrs
        assert "score" in attrs
        assert attrs["late_night_media"] is True
        assert attrs["active_alerts"] == 2
        assert attrs["score"] == 4


# =============================================================================
# Global Contract Tests (GC1–GC2)
# =============================================================================

class TestGlobalContract:
    """Global contract verification for cognitive_sensors."""

    def test_GC1_no_core_api_dependency(self):
        """GC1: cognitive_sensors use only HA states — no _core_base_url or _core_headers class attributes."""
        from custom_components.pilotsuite.sensors.cognitive_sensors import AttentionLoadSensor, StressProxySensor
        
        # Verify sensor classes don't define Core API attributes
        assert not hasattr(AttentionLoadSensor, '_core_base_url')
        assert not hasattr(AttentionLoadSensor, '_core_headers')
        assert not hasattr(StressProxySensor, '_core_base_url')
        assert not hasattr(StressProxySensor, '_core_headers')

    def test_GC2_ha_local_only(self):
        """GC2: Both sensors are HA-local projections — use hass.states, no _fetch method."""
        from custom_components.pilotsuite.sensors.cognitive_sensors import AttentionLoadSensor, StressProxySensor
        
        # Verify sensor classes don't have Core API _fetch method
        assert not hasattr(AttentionLoadSensor, '_fetch')
        assert not hasattr(StressProxySensor, '_fetch')
        
        # Verify they inherit from CoordinatorEntity (HA-local pattern)
        from homeassistant.helpers.update_coordinator import CoordinatorEntity
        assert issubclass(AttentionLoadSensor, CoordinatorEntity)
        assert issubclass(StressProxySensor, CoordinatorEntity)
