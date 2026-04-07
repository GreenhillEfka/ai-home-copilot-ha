"""Bewegungsmodul — Zone motion state tracking.

Tracks per-zone motion sensor data: active sensors, last motion, and recency.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .module import CopilotModule, ModuleContext
from ...const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class BewegungModule(CopilotModule):
    """Tracks zone motion states for the Habitus system."""

    @property
    def name(self) -> str:
        return "bewegung_module"

    def __init__(self) -> None:
        self._hass: HomeAssistant | None = None
        self._entry_id: str | None = None
        self._zone_motion: dict[str, dict[str, Any]] = {}

    async def async_setup_entry(self, ctx: ModuleContext) -> None:
        """Set up motion tracking."""
        self._hass = ctx.hass
        self._entry_id = ctx.entry_id

        ctx.hass.data.setdefault(DOMAIN, {})
        ctx.hass.data[DOMAIN].setdefault(ctx.entry_id, {})
        ctx.hass.data[DOMAIN][ctx.entry_id]["bewegung_module"] = self

        _LOGGER.info("BewegungModule: initialized")

    async def async_unload_entry(self, ctx: ModuleContext) -> bool:
        """Unload motion tracking."""
        entry_store = ctx.hass.data.get(DOMAIN, {}).get(ctx.entry_id, {})
        if isinstance(entry_store, dict):
            entry_store.pop("bewegung_module", None)
        self._hass = None
        self._entry_id = None
        return True

    def update_zone(self, zone_id: str, **kwargs: Any) -> None:
        """Update motion state for a zone.

        Accepted keys: sensors_active, sensors_total,
        last_motion, has_recent_motion.
        """
        existing = self._zone_motion.get(zone_id, {})
        existing.update(kwargs)
        self._zone_motion[zone_id] = existing

    def get_zone(self, zone_id: str) -> dict[str, Any] | None:
        """Get motion state for a zone."""
        return self._zone_motion.get(zone_id)

    def get_summary(self) -> dict[str, Any]:
        """Return summary of all zone motion states."""
        zones_with_motion = sum(
            1 for z in self._zone_motion.values() if z.get("has_recent_motion")
        )
        return {
            "total_zones": len(self._zone_motion),
            "zones_with_recent_motion": zones_with_motion,
        }
