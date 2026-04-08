"""Praesenzmodul — Zone presence tracking.

Tracks per-zone presence: occupancy, person count, and identity.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .module import CopilotModule, ModuleContext
from ...const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PraesenzModule(CopilotModule):
    """Tracks zone presence for the Habitus system."""

    @property
    def name(self) -> str:
        return "praesenz_module"

    def __init__(self) -> None:
        self._hass: HomeAssistant | None = None
        self._entry_id: str | None = None
        self._zone_presence: dict[str, dict[str, Any]] = {}

    async def async_setup_entry(self, ctx: ModuleContext) -> None:
        """Set up presence tracking."""
        self._hass = ctx.hass
        self._entry_id = ctx.entry_id

        ctx.hass.data.setdefault(DOMAIN, {})
        ctx.hass.data[DOMAIN].setdefault(ctx.entry_id, {})
        ctx.hass.data[DOMAIN][ctx.entry_id]["praesenz_module"] = self

        _LOGGER.info("PraesenzModule: initialized")

    async def async_unload_entry(self, ctx: ModuleContext) -> bool:
        """Unload presence tracking."""
        entry_store = ctx.hass.data.get(DOMAIN, {}).get(ctx.entry_id, {})
        if isinstance(entry_store, dict):
            entry_store.pop("praesenz_module", None)
        self._hass = None
        self._entry_id = None
        return True

    def update_zone(self, zone_id: str, **kwargs: Any) -> None:
        """Update presence state for a zone.

        Accepted keys: is_occupied, person_count, persons, last_entered.
        """
        existing = self._zone_presence.get(zone_id, {})
        existing.update(kwargs)
        self._zone_presence[zone_id] = existing

    def get_zone(self, zone_id: str) -> dict[str, Any] | None:
        """Get presence state for a zone."""
        return self._zone_presence.get(zone_id)

    def get_persons_home(self) -> list[str]:
        """Return a deduplicated list of all persons currently present."""
        persons: set[str] = set()
        for zone_data in self._zone_presence.values():
            if zone_data.get("is_occupied") and zone_data.get("persons"):
                persons.update(zone_data["persons"])
        return sorted(persons)

    def get_summary(self) -> dict[str, Any]:
        """Return summary of all zone presence states."""
        occupied = sum(
            1 for z in self._zone_presence.values() if z.get("is_occupied")
        )
        total_persons = sum(
            z.get("person_count", 0) for z in self._zone_presence.values()
        )
        return {
            "total_zones": len(self._zone_presence),
            "zones_occupied": occupied,
            "total_persons": total_persons,
            "persons_home": self.get_persons_home(),
        }
