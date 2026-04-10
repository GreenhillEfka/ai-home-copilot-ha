"""Hub Dashboard Sensor for Home Assistant (v6.0.0).

Exposes PilotSuite Hub dashboard overview as an HA sensor.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)


def _as_mapping(val: Any, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if isinstance(val, dict) and val:
        return val
    return default if default is not None else {}


def _as_list(val: Any, default: list[Any] | None = None) -> list[Any]:
    if isinstance(val, list):
        return val
    return default if default is not None else []


def _as_string(val: Any, default: str = "") -> str:
    if isinstance(val, str):
        normalized = val.strip()
        if normalized:
            return normalized
    return default


def _as_int(val: Any, default: int = 0) -> int:
    if isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val):
        return int(val)
    return default


def _as_float(val: Any, default: float = 0.0) -> float:
    if isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val):
        return float(val)
    return default


class HubDashboardSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing PilotSuite Hub dashboard overview."""

    _attr_name = "Hub Dashboard"
    _attr_unique_id = "copilot_hub_dashboard"
    _attr_icon = "mdi:view-dashboard"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._overview: dict[str, Any] = {}

    @property
    def native_value(self) -> int | None:
        overview = _as_mapping(self._overview)
        return _as_int(overview.get("active_devices"), 0)

    @property
    def icon(self) -> str:
        overview = _as_mapping(self._overview)
        alerts = _as_int(overview.get("alerts_count"), 0)
        if alerts > 0:
            return "mdi:view-dashboard-alert"
        return "mdi:view-dashboard"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        overview = _as_mapping(self._overview)
        summary = _as_mapping(overview.get("summary"))
        return {
            "active_devices": _as_int(overview.get("active_devices"), 0),
            "alerts_count": _as_int(overview.get("alerts_count"), 0),
            "savings_today_eur": _as_float(overview.get("savings_today_eur"), 0.0),
            "total_widgets": _as_int(summary.get("total_widgets"), 0),
            "layout_name": _as_string(summary.get("layout_name"), "default"),
            "theme": _as_string(summary.get("theme"), "auto"),
            "language": _as_string(summary.get("language"), "de"),
            "data_sources": _as_list(summary.get("data_sources"), []),
        }

    async def async_update(self) -> None:
        session = async_get_clientsession(self.hass)
        base = f"{self._core_base_url()}/api/v1/hub"
        headers = self._core_headers()

        try:
            async with session.get(
                f"{base}/dashboard", headers=headers, timeout=10
            ) as resp:
                if resp.status == 200:
                    data = _as_mapping(await resp.json())
                    if data.get("ok"):
                        self._overview = data
        except Exception as exc:
            _LOGGER.debug("Failed to fetch hub dashboard data: %s", exc)


class HubPluginsSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing PilotSuite Hub plugin status."""

    _attr_name = "Hub Plugins"
    _attr_unique_id = "copilot_hub_plugins"
    _attr_icon = "mdi:puzzle"
    _attr_native_unit_of_measurement = "plugins"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._plugins: dict[str, Any] = {}

    @property
    def native_value(self) -> int | None:
        plugins = _as_mapping(self._plugins)
        return _as_int(plugins.get("active"), 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        plugins = _as_mapping(self._plugins)
        return {
            "total": _as_int(plugins.get("total"), 0),
            "active": _as_int(plugins.get("active"), 0),
            "disabled": _as_int(plugins.get("disabled"), 0),
            "error": _as_int(plugins.get("error"), 0),
            "categories": _as_mapping(plugins.get("categories")),
        }

    async def async_update(self) -> None:
        session = async_get_clientsession(self.hass)
        base = f"{self._core_base_url()}/api/v1/hub"
        headers = self._core_headers()

        try:
            async with session.get(
                f"{base}/plugins", headers=headers, timeout=10
            ) as resp:
                if resp.status == 200:
                    data = _as_mapping(await resp.json())
                    if data.get("ok"):
                        self._plugins = data
        except Exception as exc:
            _LOGGER.debug("Failed to fetch hub plugins data: %s", exc)


class HubMultiHomeSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing PilotSuite multi-home status."""

    _attr_name = "Hub Homes"
    _attr_unique_id = "copilot_hub_homes"
    _attr_icon = "mdi:home-group"
    _attr_native_unit_of_measurement = "homes"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._homes: dict[str, Any] = {}

    @property
    def native_value(self) -> int | None:
        homes = _as_mapping(self._homes)
        return _as_int(homes.get("total_homes"), 0)

    @property
    def icon(self) -> str:
        homes = _as_mapping(self._homes)
        count = _as_int(homes.get("total_homes"), 0)
        if count > 1:
            return "mdi:home-group"
        return "mdi:home"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        homes = _as_mapping(self._homes)
        return {
            "total_homes": _as_int(homes.get("total_homes"), 0),
            "online_homes": _as_int(homes.get("online_homes"), 0),
            "total_devices": _as_int(homes.get("total_devices"), 0),
            "total_energy_kwh": _as_float(homes.get("total_energy_kwh"), 0.0),
            "total_cost_eur": _as_float(homes.get("total_cost_eur"), 0.0),
            "active_home_id": _as_string(homes.get("active_home_id"), ""),
        }

    async def async_update(self) -> None:
        session = async_get_clientsession(self.hass)
        base = f"{self._core_base_url()}/api/v1/hub"
        headers = self._core_headers()

        try:
            async with session.get(
                f"{base}/homes", headers=headers, timeout=10
            ) as resp:
                if resp.status == 200:
                    data = _as_mapping(await resp.json())
                    if data.get("ok"):
                        self._homes = data
        except Exception as exc:
            _LOGGER.debug("Failed to fetch hub homes data: %s", exc)
