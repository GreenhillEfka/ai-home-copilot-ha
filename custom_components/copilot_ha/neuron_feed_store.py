"""Neuron Feed Store — persistent storage for per-tag neuron feed toggles.

Controls whether entities associated with a given tag are forwarded
to the Core neuron system. State persisted via HA Storage API.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

NEURON_FEED_STORE_KEY = f"{DOMAIN}.neuron_feed"
NEURON_FEED_STORE_VERSION = 1


def _store(hass: HomeAssistant) -> Store:
    """Get or create the neuron feed store."""
    global_data = hass.data.setdefault(DOMAIN, {}).setdefault("_global", {})
    st = global_data.get("neuron_feed_store")
    if st is None:
        st = Store(hass, NEURON_FEED_STORE_VERSION, NEURON_FEED_STORE_KEY)
        global_data["neuron_feed_store"] = st
    return st


async def async_get_neuron_feed_states(hass: HomeAssistant) -> dict[str, bool]:
    """Load neuron feed enabled/disabled states per tag_id.

    Returns dict mapping tag_id -> is_enabled (default True).
    """
    store = _store(hass)
    raw = await store.async_load()
    if not raw or not isinstance(raw, dict):
        return {}
    return {
        str(k): bool(v)
        for k, v in (raw.get("feeds") or {}).items()
    }


async def async_set_neuron_feed_state(
    hass: HomeAssistant,
    tag_id: str,
    enabled: bool,
) -> None:
    """Set the neuron feed state for a single tag."""
    store = _store(hass)
    raw = await store.async_load() or {}
    feeds = raw.setdefault("feeds", {})
    feeds[tag_id] = enabled
    await store.async_save(raw)
    _LOGGER.debug("Neuron feed for tag '%s' set to %s", tag_id, enabled)


async def async_get_neuron_feed_state(
    hass: HomeAssistant,
    tag_id: str,
) -> bool:
    """Get the neuron feed state for a single tag. Default: True (enabled)."""
    states = await async_get_neuron_feed_states(hass)
    return states.get(tag_id, True)


async def async_is_entity_neuron_fed(
    hass: HomeAssistant,
    entity_id: str,
) -> bool:
    """Check if an entity should be forwarded to the neuron system.

    An entity is excluded if ALL of its tags have neuron feed disabled.
    An entity with no tags is always included (default allow).
    """
    from .entity_tags_store import async_get_entity_tags

    tags = await async_get_entity_tags(hass)
    feed_states = await async_get_neuron_feed_states(hass)

    # Find which tags this entity belongs to
    entity_tags: list[str] = []
    for tag_id, tag in tags.items():
        if entity_id in tag.entity_ids:
            entity_tags.append(tag_id)

    # No tags -> always forward
    if not entity_tags:
        return True

    # If ANY tag has feed enabled (or not explicitly disabled), allow
    for tag_id in entity_tags:
        if feed_states.get(tag_id, True):
            return True

    return False
