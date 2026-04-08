"""Heizmodul — Zone climate state tracking.

Tracks per-zone climate data: temperature, humidity, heating status, and comfort.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .module import CopilotModule, ModuleContext
from ...const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class HeizModule(CopilotModule):
    """Tracks zone climate states for the Habitus system."""

    @property
    def name(self) -> str:
        return "heiz_module"

    def __init__(self) -> None:
        self._hass: HomeAssistant | None = None
        self._entry_id: str | None = None
        self._zone_climate: dict[str, dict[str, Any]] = {}

    async def async_setup_entry(self, ctx: ModuleContext) -> None:
        """Set up climate tracking."""
        self._hass = ctx.hass
        self._entry_id = ctx.entry_id

        ctx.hass.data.setdefault(DOMAIN, {})
        ctx.hass.data[DOMAIN].setdefault(ctx.entry_id, {})
        ctx.hass.data[DOMAIN][ctx.entry_id]["heiz_module"] = self

        _LOGGER.info("HeizModule: initialized")

    async def async_unload_entry(self, ctx: ModuleContext) -> bool:
        """Unload climate tracking."""
        entry_store = ctx.hass.data.get(DOMAIN, {}).get(ctx.entry_id, {})
        if isinstance(entry_store, dict):
            entry_store.pop("heiz_module", None)
        self._hass = None
        self._entry_id = None
        return True

    def update_zone(self, zone_id: str, **kwargs: Any) -> None:
        """Update climate state for a zone.

        Accepted keys: current_temp, target_temp, humidity,
        is_heating, eco_mode, comfort_index.
        """
        existing = self._zone_climate.get(zone_id, {})
        existing.update(kwargs)
        self._zone_climate[zone_id] = existing

    def get_zone(self, zone_id: str) -> dict[str, Any] | None:
        """Get climate state for a zone."""
        return self._zone_climate.get(zone_id)

    def get_summary(self) -> dict[str, Any]:
        """Return summary of all zone climate states."""
        zones_heating = sum(
            1 for z in self._zone_climate.values() if z.get("is_heating")
        )
        zones_eco = sum(
            1 for z in self._zone_climate.values() if z.get("eco_mode")
        )
        return {
            "total_zones": len(self._zone_climate),
            "zones_heating": zones_heating,
            "zones_eco_mode": zones_eco,
        }
