"""Projection Contract Tests for remaining sensors (batch D — HA-lokal).

Covers HA-lokal sensors: activity_sensors, anomaly_alert, anomaly_detection_sensor,
appliance_fingerprint_sensor, area_presence_sensor, automation_template_sensor,
autonomy_status_sensor, battery_optimizer_sensor, brain_activity_sensor,
brain_architecture_sensor, calendar_sensors, cognitive_sensors,
comfort_index_sensor, demand_response_sensor, energy_insights, energy_sensors,
environment_sensors, habit_learning_v2, light_intelligence_sensor,
presence_sensors, regional_context_sensor, zone_presence_trigger.
"""
import pytest
from unittest.mock import MagicMock


def make_coord(**kw):
    c = MagicMock()
    c.data = kw
    return c


# ─── activity_sensors ─────────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.activity_sensors import ActivityLevelSensor


@pytest.mark.asyncio
async def test_activity_sensors_ha_lokal():
    sensor = ActivityLevelSensor(make_coord(current_activity="working", confidence=0.92))
    assert not hasattr(sensor, '_core_base_url')
    assert sensor.native_value == "working"


# ─── anomaly_alert ─────────────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.anomaly_alert import AnomalyAlertSensor


@pytest.mark.asyncio
async def test_anomaly_alert_ha_lokal():
    sensor = AnomalyAlertSensor(make_coord(anomaly_detected=False, alert_level="normal"))
    assert not hasattr(sensor, '_core_base_url')
    assert sensor.native_value == "normal"


# ─── anomaly_detection_sensor ───────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.anomaly_detection_sensor import AnomalyDetectionSensor


@pytest.mark.asyncio
async def test_anomaly_detection_sensor_ha_lokal():
    sensor = AnomalyDetectionSensor(make_coord(anomalies_detected=0, threshold=0.85))
    assert not hasattr(sensor, '_core_base_url')
    assert sensor.native_value == 0


# ─── appliance_fingerprint_sensor ──────────────────────────────────────────────
from custom_components.copilot_ha.sensors.appliance_fingerprint_sensor import ApplianceFingerprintSensor


@pytest.mark.asyncio
async def test_appliance_fingerprint_sensor_ha_lokal():
    sensor = ApplianceFingerprintSensor(make_coord(detected_appliances=8, power_w=420))
    assert not hasattr(sensor, '_core_base_url')
    assert sensor.native_value == 8


# ─── area_presence_sensor ─────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.area_presence_sensor import AreaPresenceSensor


@pytest.mark.asyncio
async def test_area_presence_sensor_ha_lokal():
    sensor = AreaPresenceSensor(make_coord(area_id="living_room", presence_count=2))
    assert not hasattr(sensor, '_core_base_url')


# ─── automation_template_sensor ───────────────────────────────────────────────
from custom_components.copilot_ha.sensors.automation_template_sensor import AutomationTemplateSensor


@pytest.mark.asyncio
async def test_automation_template_sensor_ha_lokal():
    sensor = AutomationTemplateSensor(make_coord(suggestions=[], last_triggered=None))
    assert not hasattr(sensor, '_core_base_url')


# ─── autonomy_status_sensor ───────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.autonomy_status_sensor import AutonomyStatusSensor


@pytest.mark.asyncio
async def test_autonomy_status_sensor_ha_lokal():
    sensor = AutonomyStatusSensor(make_coord(autonomy_level=0.85, active_modes=["learning"]))
    assert not hasattr(sensor, '_core_base_url')


# ─── battery_optimizer_sensor ───────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.battery_optimizer_sensor import BatteryOptimizerSensor


@pytest.mark.asyncio
async def test_battery_optimizer_sensor_ha_lokal():
    sensor = BatteryOptimizerSensor(make_coord(battery_level=85, discharging=False))
    assert not hasattr(sensor, '_core_base_url')
    assert sensor.native_value == 85


# ─── brain_activity_sensor ───────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.brain_activity_sensor import BrainActivitySensor


@pytest.mark.asyncio
async def test_brain_activity_sensor_ha_lokal():
    sensor = BrainActivitySensor(make_coord(active_modules=5, processed_events=128))
    assert not hasattr(sensor, '_core_base_url')
    assert sensor.native_value == 5


# ─── brain_architecture_sensor ──────────────────────────────────────────────
from custom_components.copilot_ha.sensors.brain_architecture_sensor import BrainArchitectureSensor


@pytest.mark.asyncio
async def test_brain_architecture_sensor_ha_lokal():
    sensor = BrainArchitectureSensor(make_coord(module_count=12, active_neurons=48))
    assert not hasattr(sensor, '_core_base_url')


# ─── calendar_sensors ─────────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.calendar_sensors import CalendarLoadSensor


@pytest.mark.asyncio
async def test_calendar_sensors_ha_lokal():
    sensor = CalendarLoadSensor(make_coord(upcoming_events=3, next_event="Meeting at 10:00"))
    assert not hasattr(sensor, '_core_base_url')


# ─── cognitive_sensors ────────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.cognitive_sensors import AttentionLoadSensor


@pytest.mark.asyncio
async def test_cognitive_sensors_ha_lokal():
    sensor = AttentionLoadSensor(make_coord(focus_score=0.88, cognitive_load="normal"))
    assert not hasattr(sensor, '_core_base_url')


# ─── comfort_index_sensor ────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.comfort_index_sensor import ComfortIndexSensor


@pytest.mark.asyncio
async def test_comfort_index_sensor_ha_lokal():
    sensor = ComfortIndexSensor(make_coord(comfort_score=0.85, temperature_c=22.0))
    assert not hasattr(sensor, '_core_base_url')
    assert sensor.native_value == 0.85


# ─── demand_response_sensor ──────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.demand_response_sensor import DemandResponseSensor


@pytest.mark.asyncio
async def test_demand_response_sensor_ha_lokal():
    sensor = DemandResponseSensor(make_coord(event_active=False, incentive_eur=0.0))
    assert not hasattr(sensor, '_core_base_url')


# ─── energy_insights ─────────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.energy_insights import EnergyInsightSensor


@pytest.mark.asyncio
async def test_energy_insights_ha_lokal():
    sensor = EnergyInsightSensor(make_coord(insights=["Shift washing"], potential_savings_kwh=4.2))
    assert not hasattr(sensor, '_core_base_url')


# ─── energy_sensors ─────────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.energy_sensors import EnergyProxySensor


@pytest.mark.asyncio
async def test_energy_sensors_ha_lokal():
    sensor = EnergyProxySensor(make_coord(current_power_w=450, today_kwh=12.5))
    assert not hasattr(sensor, '_core_base_url')


# ─── environment_sensors ────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.environment_sensors import LightLevelSensor


@pytest.mark.asyncio
async def test_environment_sensors_ha_lokal():
    sensor = LightLevelSensor(make_coord(indoor_temp=21.5, indoor_humidity=45))
    assert not hasattr(sensor, '_core_base_url')


# ─── habit_learning_v2 ───────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.habit_learning_v2 import HabitLearningSensor


@pytest.mark.asyncio
async def test_habit_learning_v2_ha_lokal():
    sensor = HabitLearningSensor(make_coord(learned_habits=5, confidence=0.78))
    assert not hasattr(sensor, '_core_base_url')


# ─── light_intelligence_sensor ───────────────────────────────────────────────
from custom_components.copilot_ha.sensors.light_intelligence_sensor import LightIntelligenceSensor


@pytest.mark.asyncio
async def test_light_intelligence_sensor_ha_lokal():
    sensor = LightIntelligenceSensor(make_coord(brightness_avg=215, active_zones=3))
    assert not hasattr(sensor, '_core_base_url')


# ─── presence_sensors ────────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.presence_sensors import PresenceRoomSensor


@pytest.mark.asyncio
async def test_presence_sensors_ha_lokal():
    sensor = PresenceRoomSensor(make_coord(primary_person="Andreas", confidence=0.95))
    assert not hasattr(sensor, '_core_base_url')


# ─── regional_context_sensor ─────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.regional_context_sensor import RegionalContextSensor


@pytest.mark.asyncio
async def test_regional_context_sensor_ha_lokal():
    sensor = RegionalContextSensor(make_coord(country="DE", tariff_active=True))
    assert not hasattr(sensor, '_core_base_url')


# ─── zone_presence_trigger ───────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.zone_presence_trigger import ZonePresenceTriggerSensor


@pytest.mark.asyncio
async def test_zone_presence_trigger_ha_lokal():
    sensor = ZonePresenceTriggerSensor(make_coord(active_zone="living_room", presence_detected=True))
    assert not hasattr(sensor, '_core_base_url')


# ─── automation_suggestion_sensor ───────────────────────────────────────────────
from custom_components.copilot_ha.sensors.automation_suggestion_sensor import AutomationSuggestionSensor

class FakeRespAuto:
    def __init__(self, status, json_data=None):
        self._status = status
        self._json = json_data or {}
    status = property(lambda s: s._status)
    async def json(self): return self._json
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass


class FakeSessionAuto:
    def __init__(self, resp): self._resp = resp
    def get(self, *args, **kwargs): return self._resp


def make_core_coord():
    c = MagicMock()
    c._core_base_url = lambda: "http://core:8765"
    c._core_headers = lambda: {"Authorization": "Bearer test"}
    return c


@pytest.mark.asyncio
async def test_automation_suggestion_sensor_200():
    from unittest.mock import patch
    data = {"ok": True, "suggestions": ["Light dim at 22:00"], "count": 1, "confidence": 0.85}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSessionAuto(FakeRespAuto(200, data))
        sensor = AutomationSuggestionSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs["count"] == 1
