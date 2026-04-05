"""Demand Response Sensor for Home Assistant (v5.14.0).

Exposes demand response status as an HA sensor.
State shows current grid signal level.

HA-83: Core endpoint /energy/demand-response/status may not exist.
Sensor gracefully degrades to state=Normal with warning log.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)

SIGNAL_LABELS = {0: "Normal", 1: "Advisory", 2: "Moderate", 3: "Critical"}
SIGNAL_ICONS = {
    0: "mdi:transmission-tower",
    1: "mdi:alert-circle-outline",
    2: "mdi:alert",
    3: "mdi:alert-octagon",
}


class DemandResponseSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing demand response status."""

    _attr_name = "Demand Response"
    _attr_unique_id = "copilot_demand_response"
    _attr_native_unit_of_measurement = "level"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}
        self._signal_level = 0

    @property
    def native_value(self) -> str:
        return SIGNAL_LABELS.get(self._signal_level, "Unknown")

    @property
    def icon(self) -> str:
        return SIGNAL_ICONS.get(self._signal_level, "mdi:transmission-tower")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "signal_level": self._signal_level,
            "active_signals": self._data.get("active_signals", 0),
            "managed_devices": self._data.get("managed_devices", 0),
            "curtailed_devices": self._data.get("curtailed_devices", 0),
            "total_reduction_watts": self._data.get("total_reduction_watts", 0),
            "response_active": self._data.get("response_active", False),
        }

    async def async_update(self) -> None:
        """Fetch demand response status from Core API.

        HA-83: Core endpoint GET /api/v1/energy/demand-response/status missing.
        Gracefully degrades: state=Normal, warning logged.
        """
        session = async_get_clientsession(self.hass)
        url = f"{self._core_base_url()}/api/v1/energy/demand-response/status"
        headers = self._core_headers()
        try:
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("ok"):
                        self._data = data
                        self._signal_level = data.get("current_signal", 0)
                elif resp.status == 404:
                    _LOGGER.warning(
                        "demand_response_sensor: Core endpoint "
                        "/energy/demand-response/status not found (HA-83). "
                        "Sensor state=Normal until PilotClaw implements endpoint."
                    )
                    self._signal_level = 0
                else:
                    _LOGGER.debug("Demand response API returned %s", resp.status)
        except Exception as exc:
            _LOGGER.debug("Failed to fetch demand response status: %s", exc)
