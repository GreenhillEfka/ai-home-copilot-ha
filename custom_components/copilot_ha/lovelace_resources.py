"""Lovelace card resource auto-registration for PilotSuite.

Registers the PilotSuite custom cards JavaScript from the Core Add-on
as a Lovelace resource so they appear in the card picker.

The JS file is served by the Core Add-on at:
  http://{host}:{port}/api/v1/cards/pilotsuite-cards.js
"""

from __future__ import annotations

import logging
from collections.abc import Mapping

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .connection_config import resolve_core_connection
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARD_JS_PATH = "/api/v1/cards/pilotsuite-cards.js"

# Local cards served from custom_components/copilot_ha/www/
LOCAL_CARD_FILES = [
    "styx-chat-card.js",
    "styx-suggestions-card.js",
    "styx-error-card.js",
    "styx-household-card.js",
    "styx-mood-card.js",
    "styx-brain-card.js",
    "styx-habitus-card.js",
    "styx-zone-card.js",
]


async def async_register_card_resources(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Register PilotSuite Lovelace card resources (Core + local)."""
    host, port, _token = resolve_core_connection(entry)

    try:
        # Use the Lovelace resources API if available
        lovelace = hass.data.get("lovelace")
        if lovelace is None:
            _LOGGER.debug("Lovelace not initialized yet, skipping card registration")
            return

        # HA versions expose lovelace either as dict-like data or LovelaceData object.
        resources = None
        if isinstance(lovelace, Mapping):
            resources = lovelace.get("resources")
        else:
            resources = getattr(lovelace, "resources", None)

        if resources is None:
            _LOGGER.info(
                "Lovelace resources API not available. "
                "Add PilotSuite cards manually in Settings > Dashboards > Resources."
            )
            return

        existing = await resources.async_get_items()
        existing_urls = set()
        for item in existing:
            if isinstance(item, Mapping):
                existing_urls.add(item.get("url") or "")

        registered = 0

        # Register Core-served card bundle
        if host:
            card_url = f"http://{host}:{port}{CARD_JS_PATH}"
            if not any(CARD_JS_PATH in u for u in existing_urls):
                await resources.async_create_item({"res_type": "module", "url": card_url})
                _LOGGER.info("Registered Core card bundle: %s", card_url)
                registered += 1

        # Register local card files from www/ directory
        for filename in LOCAL_CARD_FILES:
            local_url = f"/hacsfiles/{DOMAIN}/{filename}"
            alt_url = f"/local/community/{DOMAIN}/{filename}"
            if not any(filename in u for u in existing_urls):
                await resources.async_create_item({"res_type": "module", "url": local_url})
                registered += 1

        if registered:
            _LOGGER.info("Registered %d PilotSuite Lovelace card resources", registered)
        else:
            _LOGGER.debug("All PilotSuite card resources already registered")

    except Exception as err:
        _LOGGER.warning(
            "Could not auto-register Lovelace cards: %s",
            err,
        )
