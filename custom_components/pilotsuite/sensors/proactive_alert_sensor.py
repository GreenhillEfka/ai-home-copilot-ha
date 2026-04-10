"""Proactive Alert Sensor for Home Assistant (v5.19.0).

Exposes combined weather+price+grid proactive alerts as an HA sensor
with priority levels and actionable recommendations.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)

_PRIORITY_ICONS = {
    0: "mdi:check-circle",
    1: "mdi:information",
    2: "mdi:alert-outline",
    3: "mdi:alert",
    4: "mdi:alert-octagon",
}


def _as_mapping(value: Any) -> dict[str, Any]:
    """Return dict payloads, otherwise a safe empty mapping."""
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    """Return list payloads, otherwise a safe empty list."""
    return value if isinstance(value, list) else []


def _as_string(value: Any, default: str = "") -> str:
    """Return string payloads, otherwise a safe default."""
    return value if isinstance(value, str) else default


def _as_int(value: Any, default: int = 0) -> int:
    """Return finite int-like payloads, otherwise a safe default."""
    if isinstance(value, bool):
        return default
    if not isinstance(value, (int, float)):
        return default
    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        return default
    return int(numeric_value)


class ProactiveAlertSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing proactive energy alerts."""

    _attr_name = "Proactive Alerts"
    _attr_unique_id = "copilot_proactive_alerts"
    _attr_icon = "mdi:bell-alert"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}

    @property
    def native_value(self) -> str:
        data = _as_mapping(self._data)
        total = _as_int(data.get("total"), 0)
        if total == 0:
            return "Keine Alerts"
        highest = _as_string(data.get("highest_priority_label"), "Info")
        return f"{total}x {highest}"

    @property
    def icon(self) -> str:
        data = _as_mapping(self._data)
        priority = _as_int(data.get("highest_priority"), 0)
        return _PRIORITY_ICONS.get(priority, "mdi:bell-alert")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = _as_mapping(self._data)
        by_priority = _as_mapping(data.get("by_priority"))
        by_category = _as_mapping(data.get("by_category"))
        alerts = _as_list(data.get("alerts"))

        # Compact alert list
        alert_list = []
        for a in alerts[:10]:
            if not isinstance(a, dict):
                continue
            alert_list.append({
                "title": _as_string(a.get("title_de"), ""),
                "priority": _as_string(a.get("priority_label"), ""),
                "category": _as_string(a.get("category"), ""),
                "action": _as_string(a.get("action"), ""),
                "message": _as_string(a.get("message_de"), ""),
                "icon": _as_string(a.get("icon"), ""),
            })

        return {
            "total_alerts": _as_int(data.get("total"), 0),
            "highest_priority": _as_int(data.get("highest_priority"), 0),
            "highest_priority_label": _as_string(data.get("highest_priority_label"), ""),
            "info_count": _as_int(by_priority.get("info"), 0),
            "advisory_count": _as_int(by_priority.get("advisory"), 0),
            "warning_count": _as_int(by_priority.get("warning"), 0),
            "critical_count": _as_int(by_priority.get("critical"), 0),
            "categories": by_category,
            "alerts": alert_list,
            "last_evaluated": _as_string(data.get("last_evaluated"), ""),
        }

    async def async_update(self) -> None:
        session = async_get_clientsession(self.hass)
        base = f"{self._core_base_url()}/api/v1/regional"
        headers = self._core_headers()

        try:
            async with session.get(
                f"{base}/alerts", headers=headers, timeout=15
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("ok"):
                        self._data = data
        except Exception as exc:
            _LOGGER.error("Failed to fetch proactive alerts: %s", exc)
