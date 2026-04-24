"""Habitus-Zonen Sensor for Home Assistant (v6.5.0).

Consumes GET /api/v1/habitus/zones from Core and exposes
the canonical zone/habitus overview as an HA sensor.
"""

from __future__ import annotations

import logging
from typing import Any

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_SECONDS = 30

_ZONE_ICON_MAP = {
    "living": "mdi:sofa",
    "bath": "mdi:shower",
    "kitchen": "mdi:silverware-fork-knife",
    "bedroom": "mdi:bed",
    "office": "mdi:desk",
    "corridor": "mdi:walk",
    "child": "mdi:baby-face-outline",
    "terrace": "mdi:grill-outline",
    "outdoor": "mdi:tree-outline",
    "guest": "mdi:account-group",
}


class HabitusZoneSensor(CopilotBaseEntity):
    """Sensor showing Habitus-Zonen overview from Core."""

    _attr_icon = "mdi:home-floor-1"
    _attr_name = "PilotSuite Habitus-Zonen"
    _attr_unique_id = "pilotsuite_habitus_zones"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._zone_data: dict[str, Any] = {}

    @property
    def state(self) -> str:
        total = self._zone_data.get("total_zones", 0)
        zones = self._zone_data.get("zones", [])
        if total == 0:
            return "Keine Zonen"
        # Zones with explicit active=True count as active;
        # zones with no explicit flag are active if priority > 0
        active = sum(
            1 for z in zones
            if z.get("active") is True or (z.get("active") is not False and z.get("priority", 0) > 0)
        )
        return f"{active}/{total} aktiv"

    @property
    def icon(self) -> str:
        zones = self._zone_data.get("zones", [])
        for z in zones:
            zone_type = z.get("zone_type", "")
            icon = _ZONE_ICON_MAP.get(zone_type)
            if icon:
                return icon
        return "mdi:home-floor-1"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        zones = self._zone_data.get("zones", [])
        zone_list = []
        for z in zones:
            entry: dict[str, Any] = {
                "id": z.get("id", ""),
                "zone_type": z.get("zone_type", ""),
                "name": z.get("name_de") or z.get("name_en", ""),
                "name_de": z.get("name_de", ""),
                "name_en": z.get("name_en", ""),
                "description": z.get("description", ""),
                "priority": z.get("priority", 0),
                "icon": z.get("icon", ""),
                "module_overrides": z.get("module_overrides", {}),
            }
            if "metrics" in z:
                entry["metrics"] = z["metrics"]
            zone_list.append(entry)

        return {
            "total_zones": self._zone_data.get("total_zones", 0),
            "zones": zone_list,
        }

    async def async_update(self) -> None:
        # Fetch from the canonical Core habitus/zones endpoint
        # Core returns {status, total_zones, zones: [...]} with optional metrics
        data = await self._fetch("/api/v1/habitus/zones?include_metrics=true")
        if data:
            self._zone_data = data
        else:
            _LOGGER.debug("HabitusZoneSensor: no data from /api/v1/habitus/zones")
