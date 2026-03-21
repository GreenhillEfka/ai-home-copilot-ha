"""System-status sensors for Production Readiness (ROADMAP Phase 7).

Tracks:
- Core connection state (connected / degraded / disconnected)
- Current adaptive poll interval
- Consecutive API failures
- Modules ready / failed count

All entities are DIAGNOSTIC — visible in HA developer tools but not in normal UI.
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import CopilotBaseEntity


class CoreConnectionSensor(CopilotBaseEntity, SensorEntity):
    """Core Add-on connection state.

    States: connected | degraded | disconnected
    - connected:    Core replied to last poll
    - degraded:    Core replied but with elevated latency (>5s)
    - disconnected: Core unreachable for >= 3 consecutive polls
    """

    _attr_icon = "mdi:api"
    _attr_has_entity_name = False
    _attr_name = "PilotSuite Core Connection"
    _attr_unique_id = "copilot_ha_core_connection"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass, entry, coordinator) -> None:
        self._hass = hass
        self._entry = entry
        self._coordinator = coordinator
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self) -> str:
        coord = self._coordinator
        if coord is None:
            return "unavailable"

        failures = getattr(coord, "_consecutive_failures", 0)
        last_duration = getattr(coord, "_last_fetch_duration_s", 0.0)

        if failures >= 3:
            return "disconnected"
        if last_duration > 5.0:
            return "degraded"
        return "connected"

    @property
    def extra_state_attributes(self) -> dict:
        coord = self._coordinator
        if coord is None:
            return {"coordinator": "not loaded"}
        return {
            "consecutive_failures": getattr(coord, "_consecutive_failures", 0),
            "last_fetch_duration_s": round(getattr(coord, "_last_fetch_duration_s", 0.0), 2),
            "poll_interval_s": self._current_interval_s(),
            "data_age_s": self._data_age_s(),
        }

    def _current_interval_s(self) -> int:
        coord = self._coordinator
        if coord is None:
            return 0
        iv = getattr(coord, "update_interval", None)
        if iv is None:
            return 0
        return int(iv.total_seconds())

    def _data_age_s(self) -> int:
        coord = self._coordinator
        if coord is None:
            return -1
        last = getattr(coord, "_last_webhook_ts", 0.0)
        if not last:
            return -1
        import time
        return int(time.monotonic() - last)


class PollIntervalSensor(CopilotBaseEntity, SensorEntity):
    """Current adaptive poll interval in seconds.

    Shows the live poll interval as the coordinator adapts:
    - POLL_INTERVAL_NORMAL_S (30s) when data changes regularly
    - POLL_INTERVAL_IDLE_S (300s) after sustained idle
    """

    _attr_icon = "mdi:timer-outline"
    _attr_has_entity_name = False
    _attr_name = "PilotSuite Poll Interval"
    _attr_unique_id = "copilot_ha_poll_interval"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = "s"

    def __init__(self, hass, entry, coordinator) -> None:
        self._hass = hass
        self._entry = entry
        self._coordinator = coordinator

    @property
    def native_value(self) -> int:
        coord = self._coordinator
        if coord is None:
            return 0
        iv = getattr(coord, "update_interval", None)
        if iv is None:
            return 0
        return int(iv.total_seconds())


class ApiFailuresSensor(CopilotBaseEntity, SensorEntity):
    """Consecutive API failures toward Core.

    Resets to 0 on successful fetch. Value >= 3 triggers degraded/disconnected
    on CoreConnectionSensor.
    """

    _attr_icon = "mdi:alert-circle-outline"
    _attr_has_entity_name = False
    _attr_name = "PilotSuite API Failures"
    _attr_unique_id = "pilotsuite_api_failures"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass, entry, coordinator) -> None:
        self._hass = hass
        self._entry = entry
        self._coordinator = coordinator

    @property
    def native_value(self) -> int:
        coord = self._coordinator
        if coord is None:
            return -1
        return getattr(coord, "_consecutive_failures", 0)


class ModulesReadySensor(CopilotBaseEntity, SensorEntity):
    """How many CopilotRuntime modules are loaded / failed.

    Shows "N/M" where N = loaded, M = total registered.
    """

    _attr_icon = "mdi:view-module-outline"
    _attr_has_entity_name = False
    _attr_name = "PilotSuite Modules Ready"
    _attr_unique_id = "copilot_ha_modules_ready"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass, entry, runtime) -> None:
        self._hass = hass
        self._entry = entry
        self._runtime = runtime

    @property
    def native_value(self) -> str:
        runtime = self._runtime
        if runtime is None:
            return "unavailable"

        loaded = getattr(runtime, "_modules_loaded", 0)
        total = getattr(runtime, "_modules_total", 0)
        failed = getattr(runtime, "_modules_failed", 0)

        if total == 0:
            return "not started"
        return f"{loaded}/{total}"

    @property
    def extra_state_attributes(self) -> dict:
        runtime = self._runtime
        if runtime is None:
            return {"runtime": "not loaded"}
        return {
            "loaded": getattr(runtime, "_modules_loaded", 0),
            "total": getattr(runtime, "_modules_total", 0),
            "failed": getattr(runtime, "_modules_failed", 0),
        }
