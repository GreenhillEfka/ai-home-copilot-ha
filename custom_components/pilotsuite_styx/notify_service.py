"""PilotSuite Styx Notify Service — HA-232.

Sync mit Core API: /api/v1/notify/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.notify import BaseNotificationService
from homeassistant.core import HomeAssistant
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_get_service(
    hass: HomeAssistant,
    config_entry,
    config: dict,
) -> BaseNotificationService:
    """Get notify service."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    return CoreNotifyService(core_url)

class CoreNotifyService(BaseNotificationService):
    """Notification service for Core."""
    def __init__(self, core_url: str):
        self._core_url = core_url
    
    def send_message(self, message="", **kwargs):
        """Send notification."""
        requests.post(f"{self._core_url}/api/v1/notify/send", json={"message": message}, timeout=5)
