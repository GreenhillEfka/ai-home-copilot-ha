"""Lichtmodul — Zone light state tracking.

Tracks per-zone light states: counts, brightness, and auto-mode status.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .module import CopilotModule, ModuleContext
from ...const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class LichtModule(CopilotModule):
    """Tracks zone light states for the Habitus system."""

    @property
    def name(self) -> str:
        return "licht_module"

    def __init__(self) -> None:
        self._hass: HomeAssistant | None = None
        self._entry_id: str | None = None
        self._zone_lights: dict[str, dict[str, Any]] = {}

    async def async_setup_entry(self, ctx: ModuleContext) -> None:
        """Set up light tracking."""
        self._hass = ctx.hass
        self._entry_id = ctx.entry_id

        ctx.hass.data.setdefault(DOMAIN, {})
        ctx.hass.data[DOMAIN].setdefault(ctx.entry_id, {})
        ctx.hass.data[DOMAIN][ctx.entry_id]["licht_module"] = self

        _LOGGER.info("LichtModule: initialized")

    async def async_unload_entry(self, ctx: ModuleContext) -> bool:
        """Unload light tracking."""
        entry_store = ctx.hass.data.get(DOMAIN, {}).get(ctx.entry_id, {})
        if isinstance(entry_store, dict):
            entry_store.pop("licht_module", None)
        self._hass = None
        self._entry_id = None
        return True

    def update_zone(
        self,
        zone_id: str,
        lights_on: int,
        lights_total: int,
        avg_brightness: float,
        auto_enabled: bool,
    ) -> None:
        """Update light state for a zone."""
        self._zone_lights[zone_id] = {
            "lights_on": lights_on,
            "lights_total": lights_total,
            "avg_brightness": avg_brightness,
            "auto_enabled": auto_enabled,
        }

    def get_zone(self, zone_id: str) -> dict[str, Any] | None:
        """Get light state for a zone."""
        return self._zone_lights.get(zone_id)

    def get_summary(self) -> dict[str, Any]:
        """Return summary of all zone light states."""
        total_on = sum(z["lights_on"] for z in self._zone_lights.values())
        return {
            "total_zones": len(self._zone_lights),
            "total_lights_on": total_on,
        }
