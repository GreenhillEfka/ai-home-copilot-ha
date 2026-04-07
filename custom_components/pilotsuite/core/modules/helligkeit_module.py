"""Helligkeitsmodul — Zone brightness tracking.

Tracks per-zone brightness readings: indoor/outdoor lux, light need, and deficit.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .module import CopilotModule, ModuleContext
from ...const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class HelligkeitModule(CopilotModule):
    """Tracks zone brightness readings for the Habitus system."""

    @property
    def name(self) -> str:
        return "helligkeit_module"

    def __init__(self) -> None:
        self._hass: HomeAssistant | None = None
        self._entry_id: str | None = None
        self._zone_brightness: dict[str, dict[str, Any]] = {}

    async def async_setup_entry(self, ctx: ModuleContext) -> None:
        """Set up brightness tracking."""
        self._hass = ctx.hass
        self._entry_id = ctx.entry_id

        ctx.hass.data.setdefault(DOMAIN, {})
        ctx.hass.data[DOMAIN].setdefault(ctx.entry_id, {})
        ctx.hass.data[DOMAIN][ctx.entry_id]["helligkeit_module"] = self

        _LOGGER.info("HelligkeitModule: initialized")

    async def async_unload_entry(self, ctx: ModuleContext) -> bool:
        """Unload brightness tracking."""
        entry_store = ctx.hass.data.get(DOMAIN, {}).get(ctx.entry_id, {})
        if isinstance(entry_store, dict):
            entry_store.pop("helligkeit_module", None)
        self._hass = None
        self._entry_id = None
        return True

    def update_zone(
        self,
        zone_id: str,
        avg_indoor_lux: float,
        avg_outdoor_lux: float,
        needs_light: bool,
        deficit_pct: float,
    ) -> None:
        """Update brightness readings for a zone."""
        self._zone_brightness[zone_id] = {
            "avg_indoor_lux": avg_indoor_lux,
            "avg_outdoor_lux": avg_outdoor_lux,
            "needs_light": needs_light,
            "deficit_pct": deficit_pct,
        }

    def get_zone(self, zone_id: str) -> dict[str, Any] | None:
        """Get brightness readings for a zone."""
        return self._zone_brightness.get(zone_id)

    def get_summary(self) -> dict[str, Any]:
        """Return summary of all zone brightness states."""
        zones_needing_light = sum(
            1 for z in self._zone_brightness.values() if z["needs_light"]
        )
        return {
            "total_zones": len(self._zone_brightness),
            "zones_needing_light": zones_needing_light,
        }
