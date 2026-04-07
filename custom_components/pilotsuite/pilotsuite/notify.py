"""PilotSuite Styx Notification Service — HA-188.

Sync mit Core API: /api/v1/notifications/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.notify import BaseNotificationService
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_get_service(hass, config, config_entry):
    """Get notification service."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    return PilotSuiteNotificationService(core_url)

class PilotSuiteNotificationService(BaseNotificationService):
    """Notification service for PilotSuite Core."""
    
    def __init__(self, core_url: str):
        self._core_url = core_url
    
    def send_message(self, message, **kwargs):
        """Send notification via Core API."""
        title = kwargs.get("title", "PilotSuite")
        data = {
            "id": f"notify_{title}",
            "title": title,
            "message": message,
        }
        try:
            requests.post(f"{self._core_url}/api/v1/notifications/send", json=data, timeout=5)
        except Exception as e:
            _LOGGER.warning(f"Failed to send notification: {e}")
