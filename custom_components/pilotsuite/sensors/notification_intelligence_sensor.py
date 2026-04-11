"""Notification Intelligence Sensor for PilotSuite HA Integration (v7.2.0).

Displays notification overview, unread count, DND status, and delivery stats.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

logger = logging.getLogger(__name__)


def _as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    return default


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _as_string(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return default


class NotificationIntelligenceSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing notification intelligence overview."""

    _attr_name = "Notification Intelligence"
    _attr_icon = "mdi:bell-ring"
    _attr_unique_id = "pilotsuite_notification_intelligence"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}

    async def _fetch(self) -> dict | None:
        import aiohttp
        try:
            url = f"{self._core_base_url()}/api/v1/hub/notifications"
            headers = self._core_headers()
            session = async_get_clientsession(self.hass)
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            logger.debug("Failed to fetch notification intelligence data")
        return None

    async def async_update(self) -> None:
        data = await self._fetch()
        if isinstance(data, dict) and data.get("ok"):
            self._data = data

    @property
    def native_value(self) -> str:
        data = _as_mapping(self._data)
        total = _as_int(data.get("total_notifications"), 0)
        unread = _as_int(data.get("unread_count"), 0)
        if total == 0:
            return "Keine Benachrichtigungen"
        if unread == 0:
            return "Alle gelesen"
        return f"{unread} ungelesen"

    @property
    def icon(self) -> str:
        data = _as_mapping(self._data)
        dnd = _as_bool(data.get("dnd_active"), False)
        if dnd:
            return "mdi:bell-off"
        unread = _as_int(data.get("unread_count"), 0)
        if unread > 0:
            return "mdi:bell-badge"
        return "mdi:bell-check"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = _as_mapping(self._data)
        attrs: dict[str, Any] = {
            "total_notifications": _as_int(data.get("total_notifications"), 0),
            "unread_count": _as_int(data.get("unread_count"), 0),
            "dnd_active": _as_bool(data.get("dnd_active"), False),
            "batch_pending": _as_int(data.get("batch_pending"), 0),
            "rules_count": _as_int(data.get("rules_count"), 0),
            "channels_active": [
                channel
                for channel in (_as_string(item) for item in _as_list(data.get("channels_active")))
                if channel
            ],
        }

        stats = _as_mapping(data.get("stats"))
        if stats:
            attrs["total_sent"] = _as_int(stats.get("total_sent"), 0)
            attrs["total_suppressed"] = _as_int(stats.get("total_suppressed"), 0)
            attrs["by_priority"] = _as_mapping(stats.get("by_priority"))

        recent_entries = []
        for notification in _as_list(data.get("recent"))[:5]:
            notification_data = _as_mapping(notification)
            if not notification_data:
                continue
            recent_entries.append(
                {
                    "title": _as_string(notification_data.get("title")),
                    "priority": _as_string(notification_data.get("priority")),
                    "channel": _as_string(notification_data.get("channel")),
                    "read": _as_bool(notification_data.get("read"), False),
                }
            )
        if recent_entries:
            attrs["recent"] = recent_entries

        return attrs
