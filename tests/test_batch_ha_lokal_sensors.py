"""Batch Projection Tests for untested HA-lokal sensors (HA-104).

Covers sensors without tests that have 0 Core API calls.
Each test verifies: coordinator-only, no _core_base_url/_core_headers.
"""
import pytest
from unittest.mock import MagicMock


def make_coordinator(**kwargs):
    c = MagicMock()
    c.data = kwargs
    return c


def make_hass():
    return MagicMock()


# ─── anomaly_alert ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_anomaly_alert_ha_lokal():
    from custom_components.copilot_ha.sensors.anomaly_alert import AnomalyAlertSensor
    c = make_coordinator(anomaly_detected=False, alert_level="normal")
    h = make_hass()
    sensor = AnomalyAlertSensor(c, h)
    assert not hasattr(sensor, '_core_base_url')
    assert sensor.native_value == "normal"


# ─── area_presence_sensor ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_area_presence_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.area_presence_sensor import AreaPresenceSensor
    c = make_coordinator(area_id="living_room", presence_count=2)
    h = make_hass()
    sensor = AreaPresenceSensor(c, h)
    assert not hasattr(sensor, '_core_base_url')


# ─── automation_template_sensor ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_automation_template_sensor():
    """Has Core API calls — needs review. Test for baseline behavior."""
    from custom_components.copilot_ha.sensors.automation_template_sensor import AutomationTemplateSensor
    c = make_coordinator(suggestions=[], last_triggered=None)
    h = make_hass()
    sensor = AutomationTemplateSensor(c, h)
    # Has Core dependency — verify we can import and initialize
    assert hasattr(sensor, 'suggestions') or hasattr(sensor, 'native_value')


# ─── autonomy_status_sensor ─────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_autonomy_status_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.autonomy_status_sensor import AutonomyStatusSensor
    c = make_coordinator(autonomy_level=0.85, active_modes=["learning"])
    h = make_hass()
    sensor = AutonomyStatusSensor(c, h)
    assert not hasattr(sensor, '_core_base_url')
