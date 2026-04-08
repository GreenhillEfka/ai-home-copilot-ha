"""Neuron Feed Control Entities — per-tag switches + summary sensor.

Creates:
- switch.pilotsuite_neuron_feed_<tag_id> per entity tag
- sensor.pilotsuite_neuron_feed_summary with include/exclude counts
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback

from .const import DOMAIN
from .entity import CopilotBaseEntity
from .entity_tags_store import async_get_entity_tags
from .neuron_feed_store import (
    async_get_neuron_feed_state,
    async_get_neuron_feed_states,
    async_set_neuron_feed_state,
)

_LOGGER = logging.getLogger(__name__)


class NeuronFeedTagSwitch(CopilotBaseEntity, SwitchEntity):
    """Switch to enable/disable feeding entities with this tag to the neuron system."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:neuron"

    def __init__(
        self,
        coordinator,
        tag_id: str,
        tag_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._tag_id = tag_id
        self._tag_name = tag_name
        self._attr_unique_id = f"copilot_ha_neuron_feed_{tag_id}"
        self._attr_name = f"PilotSuite Neuron Feed: {tag_name}"
        self._attr_is_on = True  # default: all tags feed to neurons

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "tag_id": self._tag_id,
            "tag_name": self._tag_name,
            "integration": DOMAIN,
        }

    async def async_added_to_hass(self) -> None:
        """Load persisted state on startup."""
        await super().async_added_to_hass()
        enabled = await async_get_neuron_feed_state(self.hass, self._tag_id)
        self._attr_is_on = enabled
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable neuron feed for this tag."""
        await async_set_neuron_feed_state(self.hass, self._tag_id, True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable neuron feed for this tag."""
        await async_set_neuron_feed_state(self.hass, self._tag_id, False)
        self._attr_is_on = False
        self.async_write_ha_state()


class NeuronFeedSummarySensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing how many entities are included/excluded from neuron feed."""

    _attr_has_entity_name = False
    _attr_unique_id = "copilot_ha_neuron_feed_summary"
    _attr_name = "PilotSuite Neuron Feed Summary"
    _attr_icon = "mdi:brain"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._included = 0
        self._excluded = 0
        self._total_tags = 0
        self._enabled_tags = 0

    @property
    def native_value(self) -> str:
        return f"{self._included} aktiv / {self._excluded} ausgeschlossen"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "included_entities": self._included,
            "excluded_entities": self._excluded,
            "total_tags": self._total_tags,
            "enabled_tags": self._enabled_tags,
            "integration": DOMAIN,
        }

    async def async_update(self) -> None:
        """Recalculate included/excluded entity counts."""
        try:
            tags = await async_get_entity_tags(self.hass)
            feed_states = await async_get_neuron_feed_states(self.hass)

            self._total_tags = len(tags)
            self._enabled_tags = 0
            included_entities: set[str] = set()
            excluded_entities: set[str] = set()

            # Collect entity-to-tags mapping
            entity_tags_map: dict[str, list[str]] = {}
            for tag_id, tag in tags.items():
                is_enabled = feed_states.get(tag_id, True)
                if is_enabled:
                    self._enabled_tags += 1
                for eid in tag.entity_ids:
                    entity_tags_map.setdefault(eid, []).append(tag_id)

            # Determine if each entity is included or excluded
            for eid, tag_ids in entity_tags_map.items():
                any_enabled = any(feed_states.get(tid, True) for tid in tag_ids)
                if any_enabled:
                    included_entities.add(eid)
                else:
                    excluded_entities.add(eid)

            self._included = len(included_entities)
            self._excluded = len(excluded_entities)

        except Exception:  # noqa: BLE001
            _LOGGER.debug("Failed to update neuron feed summary")


async def async_create_neuron_feed_entities(
    coordinator,
) -> dict[str, list]:
    """Create neuron feed switch + sensor entities.

    Returns dict with "switch" and "sensor" lists for platform registration.
    """
    hass = coordinator.hass
    tags = await async_get_entity_tags(hass)

    switches: list[NeuronFeedTagSwitch] = []
    for tag_id, tag in tags.items():
        switches.append(
            NeuronFeedTagSwitch(
                coordinator=coordinator,
                tag_id=tag_id,
                tag_name=tag.name,
            )
        )

    summary = NeuronFeedSummarySensor(coordinator)

    return {
        "switch": switches,
        "sensor": [summary],
    }
