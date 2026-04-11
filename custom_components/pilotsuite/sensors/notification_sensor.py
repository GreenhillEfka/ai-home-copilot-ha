"""Notification Sensor for PilotSuite (v5.8.0).

Exposes notification count and latest alerts as a HA sensor.
Polls Core notification engine for pending/digest data.
"""
from __future__ import annotations

import logging
from typing import Any

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# Guard helpers
# =============================================================================

def _as_mapping(val: Any) -> dict[str, Any]:
    """Reject non-dict top-level payloads."""
    if isinstance(val, dict):
        return val
    return {}


def _as_list(val: Any) -> list:
    """Accept only list payloads."""
    if isinstance(val, list):
        return val
    return []


def _safe_count(val: Any) -> int:
    """Accept only non-negative integer counts; reject floats, negatives, non-int."""
    if isinstance(val, int) and not isinstance(val, bool) and val >= 0:
        return val
    return 0


# =============================================================================
# NotificationSensor
# =============================================================================

class NotificationSensor(CopilotBaseEntity):
    """Sensor exposing notification engine state."""

    _attr_name = "PilotSuite Notifications"
    _attr_icon = "mdi:bell-badge"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "copilot_notifications"
        self._notif_data: dict[str, Any] | None = None
        self._digest_data: dict[str, Any] | None = None

    @property
    def native_value(self) -> str | None:
        """Return unread notification count as state."""
        notif = _as_mapping(self._notif_data)
        if not notif or not _is_ok(notif):
            return "unavailable"
        count = _safe_count(notif.get("count"))
        return f"{count} pending" if count > 0 else "no alerts"

    @property
    def icon(self) -> str:
        """Dynamic icon based on pending count."""
        notif = _as_mapping(self._notif_data)
        if not notif or not _is_ok(notif):
            return "mdi:bell-outline"
        count = _safe_count(notif.get("count"))
        return "mdi:bell-alert" if count > 0 else "mdi:bell-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return notification details."""
        attrs: dict[str, Any] = {
            "notifications_url": (
                f"{self._core_base_url()}/api/v1/notifications"
            ),
            "digest_url": (
                f"{self._core_base_url()}/api/v1/notifications/digest"
            ),
        }

        notif = _as_mapping(self._notif_data)
        if notif and _is_ok(notif):
            notifications = _as_list(notif.get("notifications"))
            count = _safe_count(notif.get("count"))
            attrs["pending_count"] = count
            attrs["latest"] = notifications[:5]

        digest = _as_mapping(self._digest_data)
        if digest and _is_ok(digest):
            attrs["digest_count"] = _safe_count(digest.get("count"))
            attrs["by_source"] = _as_mapping(digest.get("by_source"))
            attrs["by_priority"] = _as_mapping(digest.get("by_priority"))

        return attrs

    async def async_update(self) -> None:
        """Fetch notification data from Core API."""
        try:
            session = self.coordinator._session
            if session is None:
                return

            headers = self._core_headers()

            base = f"{self._core_base_url()}"

            async with session.get(
                f"{base}/api/v1/notifications?limit=10",
                headers=headers, timeout=10,
            ) as resp:
                if resp.status == 200:
                    raw = await resp.json()
                    self._notif_data = _as_mapping(raw) if isinstance(raw, dict) else {}

            async with session.get(
                f"{base}/api/v1/notifications/digest?hours=24",
                headers=headers, timeout=10,
            ) as resp:
                if resp.status == 200:
                    raw = await resp.json()
                    self._digest_data = _as_mapping(raw) if isinstance(raw, dict) else {}

        except Exception as e:
            _LOGGER.debug("Failed to fetch notification data: %s", e)


# =============================================================================
# Internal
# =============================================================================

def _is_ok(data: dict[str, Any]) -> bool:
    """Return True only when data contains an explicit ok=True."""
    return data.get("ok") is True
