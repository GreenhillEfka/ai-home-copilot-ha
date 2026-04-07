"""Habitus Zone Presence Trigger Sensors (v1.0.0).

Creates per-zone binary sensors that reflect presence state from the
Core Zone Automation Controller. Each zone gets:
- A binary_sensor indicating presence (on/off)
- Attributes: mode (off/learning/autonomy), confidence, trigger sources
- Configurable automation mode per zone

Modes:
- **off**: Sensor reports state but triggers NO automations
- **learning**: Sensor reports state, records patterns, no actions
- **autonomy**: Sensor reports state AND triggers automations (lights, music)

Core API: GET /api/v1/zone-automation/dashboard
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from ..entity import CopilotBaseEntity

logger = logging.getLogger(__name__)

# Valid automation modes
AUTOMATION_MODES = ("off", "learning", "autonomy")

# Default mode for new zones
DEFAULT_MODE = "learning"


class ZonePresenceTriggerSensor(CopilotBaseEntity, BinarySensorEntity):
    """Per-zone binary sensor: ON when zone is occupied.

    Attributes expose automation mode, light/music state, and config.
    The mode controls whether zone automations (lights, music) are active.
    """

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        zone_id: str,
        zone_name: str = "",
    ) -> None:
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._zone_name = zone_name or zone_id.replace("_", " ").title()
        self._attr_name = f"Praesenz {self._zone_name}"
        self._attr_unique_id = f"pilotsuite_zone_presence_{zone_id}"

        # State
        self._occupied = False
        self._presence_confirmed = False
        self._lights_on = False
        self._music_playing = False
        self._brightness_pct = 0
        self._zone_config: dict[str, Any] = {}

        # Automation mode (persisted via HA entity registry extra_data)
        self._automation_mode: str = DEFAULT_MODE

    @property
    def is_on(self) -> bool | None:
        """Return True if zone is occupied."""
        return self._occupied

    @property
    def icon(self) -> str:
        if self._automation_mode == "off":
            return "mdi:motion-sensor-off"
        if self._automation_mode == "learning":
            return "mdi:brain"
        if self._occupied:
            return "mdi:motion-sensor"
        return "mdi:motion-sensor-off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        light_cfg = self._zone_config.get("light", {})
        music_cfg = self._zone_config.get("music", {})

        return {
            "zone_id": self._zone_id,
            "zone_name": self._zone_name,
            "automation_mode": self._automation_mode,
            "presence_confirmed": self._presence_confirmed,
            "lights_on": self._lights_on,
            "lights_enabled": light_cfg.get("enabled", True),
            "brightness_target_pct": light_cfg.get("brightness_target_pct", 0),
            "current_brightness_pct": self._brightness_pct,
            "music_playing": self._music_playing,
            "music_enabled": music_cfg.get("enabled", True),
            "music_follow_mode": music_cfg.get("follow_mode", False),
            "presence_delay_s": light_cfg.get("presence_delay_s", 5),
            "absence_delay_s": light_cfg.get("absence_delay_s", 120),
        }

    async def async_update(self) -> None:
        """Fetch zone automation dashboard from Core API."""
        data = await self._fetch("/api/v1/zone-automation/dashboard")
        if not data:
            return

        zones = data.get("zones", [])
        for zone in zones:
            if zone.get("zone_id") == self._zone_id:
                state = zone.get("state", {})
                self._occupied = state.get("occupied", False)
                self._presence_confirmed = state.get("presence_confirmed", False)
                self._lights_on = state.get("lights_on", False)
                self._music_playing = state.get("music_playing", False)
                self._brightness_pct = state.get("current_brightness_pct", 0)
                self._zone_config = zone.get("config", {})
                break

    async def async_set_automation_mode(self, mode: str) -> bool:
        """Set the automation mode for this zone and persist to Core.

        Returns True if mode was changed successfully.
        """
        if mode not in AUTOMATION_MODES:
            logger.warning(
                "Invalid automation mode '%s' for zone %s. Valid: %s",
                mode, self._zone_id, AUTOMATION_MODES,
            )
            return False

        old_mode = self._automation_mode
        self._automation_mode = mode
        logger.info(
            "Zone %s automation mode: %s → %s",
            self._zone_id, old_mode, mode,
        )
        self.async_write_ha_state()

        # Persist mode change to Core API
        if self.coordinator and hasattr(self.coordinator, "api"):
            try:
                await self.coordinator.api.async_set_zone_automation_mode(
                    self._zone_id, mode
                )
                logger.debug(
                    "Zone %s mode '%s' persisted to Core", self._zone_id, mode
                )
            except Exception:
                logger.warning(
                    "Failed to persist zone %s mode to Core", self._zone_id,
                    exc_info=True,
                )

        return True

    def set_automation_mode(self, mode: str) -> bool:
        """Set the automation mode (sync wrapper, no Core persistence).

        Prefer async_set_automation_mode() for full persistence.
        """
        if mode not in AUTOMATION_MODES:
            return False
        self._automation_mode = mode
        self.async_write_ha_state()
        return True


class ZonePresenceOverviewSensor(CopilotBaseEntity, BinarySensorEntity):
    """Global presence overview: ON when any zone is occupied."""

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_name = "Praesenz Gesamt"
    _attr_unique_id = "pilotsuite_zone_presence_overview"
    _attr_icon = "mdi:home-account"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._occupied_zones = 0
        self._total_zones = 0
        self._active_lights = 0
        self._active_music = 0

    @property
    def is_on(self) -> bool | None:
        return self._occupied_zones > 0

    @property
    def icon(self) -> str:
        if self._occupied_zones == 0:
            return "mdi:home-export-outline"
        return "mdi:home-account"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "total_zones": self._total_zones,
            "occupied_zones": self._occupied_zones,
            "active_lights": self._active_lights,
            "active_music": self._active_music,
        }

    async def async_update(self) -> None:
        data = await self._fetch("/api/v1/zone-automation/dashboard")
        if not data:
            return

        summary = data.get("summary", {})
        self._total_zones = summary.get("total_zones", 0)
        self._occupied_zones = summary.get("occupied_zones", 0)
        self._active_lights = summary.get("active_lights", 0)
        self._active_music = summary.get("active_music", 0)
