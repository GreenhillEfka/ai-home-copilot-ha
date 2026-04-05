"""PilotSuite Styx Diagnostics — HA-193.

Sync mit Core API: /api/v1/cache/*, /api/v1/system/*
"""
from __future__ import annotations
import logging
from homeassistant.components.diagnostics import async_redact_data
from .const import DOMAIN, CONF_CORE_URL, VERSION

_LOGGER = logging.getLogger(__name__)

TO_REDACT = {"api_key", "token", "password"}

async def async_get_config_entry_diagnostics(hass, config_entry):
    """Return diagnostics for config entry."""
    return {
        "domain": DOMAIN,
        "version": VERSION,
        "config": async_redact_data(dict(config_entry.data), TO_REDACT),
        "core_url": config_entry.data.get(CONF_CORE_URL, "http://localhost:8909"),
    }

async def async_get_device_diagnostics(hass, config_entry, device):
    """Return diagnostics for device."""
    return {
        "device": device.name,
        "core_url": config_entry.data.get(CONF_CORE_URL),
    }
