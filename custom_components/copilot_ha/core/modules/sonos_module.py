"""Sonos Module — Zone-basierte Sonos-Steuerung via node-sonos-http-api.

Provides:
- Zone-to-Sonos-room mapping
- Playback control (play/pause/volume/favorites)
- Musikwolke (multi-room grouping)
- TTS (say) functionality
- Media Follow integration

Requires: node-sonos-http-api running on port 5005
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry, entity_registry

from ...const import DOMAIN
from ..module import ModuleContext

_LOGGER = logging.getLogger(__name__)


@dataclass
class SonosZoneConfig:
    """Configuration for a Sonos zone."""
    zone_id: str
    sonos_room: str | None = None
    favorite: str | None = None
    volume_pct: int = 30
    follow_enabled: bool = True


@dataclass
class SonosModuleState:
    """Current state of the Sonos module."""
    connected: bool = False
    zones: dict[str, SonosZoneConfig] = field(default_factory=dict)
    active_playback: dict[str, dict[str, Any]] = field(default_factory=dict)
    musikwolke_active: bool = False
    musikwolke_zones: list[str] = field(default_factory=list)


class SonosModule:
    """Sonos integration module for zone-based control."""

    name = "sonos"

    def __init__(self) -> None:
        self._hass: HomeAssistant | None = None
        self._entry: ConfigEntry | None = None
        self._state = SonosModuleState()
        self._zone_speaker_map: dict[str, str] = {}
        self._zone_favorites: dict[str, str] = {}

    @property
    def state(self) -> SonosModuleState:
        """Current module state."""
        return self._state

    @property
    def zone_speaker_map(self) -> dict[str, str]:
        """Get zone-to-speaker mapping."""
        return dict(self._zone_speaker_map)

    async def async_setup_entry(self, ctx: ModuleContext) -> None:
        """Set up Sonos module."""
        self._hass = ctx.hass
        self._entry = ctx.entry

        # Load configuration
        data = {**ctx.entry.data, **ctx.entry.options}
        self._load_zone_mappings(data)

        # Check Sonos API connectivity
        await self._check_connectivity()

        # Store module reference
        domain_data = ctx.hass.data.setdefault(DOMAIN, {})
        entry_data = domain_data.setdefault(ctx.entry.entry_id, {})
        entry_data["sonos_module"] = self

        _LOGGER.info("Sonos module initialized: %d zone mappings", len(self._zone_speaker_map))

    async def async_unload_entry(self, ctx: ModuleContext) -> bool:
        """Unload Sonos module."""
        domain_data = ctx.hass.data.get(DOMAIN, {})
        entry_data = domain_data.get(ctx.entry.entry_id, {})
        entry_data.pop("sonos_module", None)

        _LOGGER.debug("Sonos module unloaded")
        return True

    def _load_zone_mappings(self, data: dict[str, Any]) -> None:
        """Load zone-to-speaker mappings from config."""
        # From media_context_v2 zone_map if available
        zone_map = data.get("zone_map", {})
        for zone_id, config in zone_map.items():
            if isinstance(config, dict):
                # Extract Sonos room from config
                sonos_room = config.get("sonos_room") or config.get("speaker")
                if sonos_room:
                    self._zone_speaker_map[zone_id] = sonos_room
                    self._zone_favorites[zone_id] = config.get("favorite", "")

        # Also check for explicit sonos_zone_mappings
        explicit_mappings = data.get("sonos_zone_mappings", {})
        for zone_id, room in explicit_mappings.items():
            if zone_id not in self._zone_speaker_map:
                self._zone_speaker_map[zone_id] = room

    async def _check_connectivity(self) -> None:
        """Check if node-sonos-http-api is reachable."""
        try:
            # Use HA's http integration to check port 5005
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://127.0.0.1:5005/zones", timeout=5) as resp:
                    if resp.status == 200:
                        self._state.connected = True
                        _LOGGER.info("Sonos HTTP API connected")
                    else:
                        self._state.connected = False
                        _LOGGER.warning("Sonos HTTP API returned %d", resp.status)
        except Exception as err:
            self._state.connected = False
            _LOGGER.warning("Sonos HTTP API not reachable: %s", err)

    def set_zone_speaker(self, zone_id: str, sonos_room: str) -> None:
        """Set zone-to-speaker mapping."""
        self._zone_speaker_map[zone_id] = sonos_room
        _LOGGER.debug("Mapped zone '%s' → Sonos '%s'", zone_id, sonos_room)

    def remove_zone_speaker(self, zone_id: str) -> None:
        """Remove zone-to-speaker mapping."""
        self._zone_speaker_map.pop(zone_id, None)
        _LOGGER.debug("Removed mapping for zone '%s'", zone_id)

    def get_sonos_room(self, zone_id: str) -> str | None:
        """Get Sonos room name for a zone."""
        return self._zone_speaker_map.get(zone_id)

    def get_zone_for_room(self, room: str) -> str | None:
        """Find zone ID for a Sonos room."""
        for zone_id, room_name in self._zone_speaker_map.items():
            if room_name.lower() == room.lower():
                return zone_id
        return None

    def get_all_zones(self) -> list[str]:
        """Get all configured zone IDs."""
        return list(self._zone_speaker_map.keys())

    def get_all_rooms(self) -> list[str]:
        """Get all configured Sonos rooms."""
        return list(self._zone_speaker_map.values())

    def to_dict(self) -> dict[str, Any]:
        """Export module state as dict."""
        return {
            "connected": self._state.connected,
            "zone_count": len(self._zone_speaker_map),
            "zone_speaker_map": dict(self._zone_speaker_map),
            "zone_favorites": dict(self._zone_favorites),
            "musikwolke_active": self._state.musikwolke_active,
            "musikwolke_zones": list(self._state.musikwolke_zones),
        }


async def async_get_sonos_module(hass: HomeAssistant, entry_id: str) -> SonosModule | None:
    """Get Sonos module instance from hass.data."""
    domain_data = hass.data.get(DOMAIN, {})
    entry_data = domain_data.get(entry_id, {})
    return entry_data.get("sonos_module")
