"""HACS Gate Integration for Home Assistant — HA-180."""
from __future__ import annotations
import logging
import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)
CORE_API_BASE = "http://localhost:8909/api/v1"

async def check_hacs_gate(hass: HomeAssistant) -> dict:
    """Query Core HACS gate before showing update."""
    session = async_get_clientsession(hass)
    try:
        async with async_timeout.timeout(5):
            async with session.get(f"{CORE_API_BASE}/hacs/gate") as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        _LOGGER.warning(f"HACS gate check failed: {e}")
    return {"ok": False, "can_proceed": False, "error": "Gate check failed"}

async def get_hacs_discovery(hass: HomeAssistant) -> dict:
    """Get HACS discovery metadata from Core."""
    session = async_get_clientsession(hass)
    try:
        async with async_timeout.timeout(5):
            async with session.get(f"{CORE_API_BASE}/hacs/discovery") as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        _LOGGER.warning(f"HACS discovery failed: {e}")
    return {}
