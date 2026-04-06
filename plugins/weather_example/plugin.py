"""Example plugin for PilotSuite demonstrating the plugin interface.

This plugin provides a simple weather capability.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..core.plugins.types import PluginHealth, PluginInterface, PluginState

_LOGGER = logging.getLogger(__name__)


class WeatherPlugin(PluginInterface):
    """Example weather plugin."""
    
    @property
    def name(self) -> str:
        """Plugin name."""
        return "weather_example"
    
    @property
    def version(self) -> str:
        """Plugin version."""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Plugin description."""
        return "Example weather plugin using wttr.in API"
    
    @property
    def provides(self) -> list[str]:
        """Capabilities provided."""
        return ["weather", "example"]
    
    async def async_init(self, hass: HomeAssistant) -> None:
        """Initialize plugin."""
        _LOGGER.info("Initializing weather plugin")
        self.hass = hass
        self.session = async_get_clientsession(hass)
        self._last_weather = None
        self._update_task = None
        self._state = PluginState.INITIALIZING
    
    async def async_start(self) -> None:
        """Start periodic weather updates."""
        _LOGGER.info("Starting weather plugin")
        self._update_task = asyncio.create_task(self._periodic_update())
        self._state = PluginState.READY
    
    async def async_stop(self) -> None:
        """Stop plugin."""
        _LOGGER.info("Stopping weather plugin")
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        self._state = PluginState.UNLOADED
    
    async def _periodic_update(self) -> None:
        """Periodic weather update task."""
        while True:
            try:
                await self._fetch_weather("Berlin")
                await asyncio.sleep(300)  # Update every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOGGER.error("Weather update error: %s", err)
                await asyncio.sleep(60)  # Retry in 1 minute
    
    async def _fetch_weather(self, location: str) -> dict[str, Any]:
        """Fetch weather data."""
        try:
            url = f"https://wttr.in/{location}?format=j1"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    self._last_weather = {
                        "location": location,
                        "temperature": data["current_condition"][0]["temp_C"],
                        "condition": data["current_condition"][0]["weatherDesc"][0]["value"],
                        "timestamp": datetime.now().isoformat(),
                    }
                    _LOGGER.debug("Weather updated: %s", self._last_weather)
                    return self._last_weather
                else:
                    _LOGGER.error("Weather API error: %s", response.status)
                    return None
        except Exception as err:
            _LOGGER.error("Failed to fetch weather: %s", err)
            return None
    
    async def async_health_check(self) -> PluginHealth:
        """Check plugin health."""
        if self._state == PluginState.READY and self._last_weather:
            age = datetime.now() - datetime.fromisoformat(self._last_weather["timestamp"])
            if age.total_seconds() < 600:  # Data less than 10 minutes old
                return PluginHealth(
                    state=PluginState.READY,
                    message="Weather data current",
                    last_check=datetime.now(),
                )
            else:
                return PluginHealth(
                    state=PluginState.DEGRADED,
                    message="Weather data stale",
                    last_check=datetime.now(),
                )
        else:
            return PluginHealth(
                state=self._state,
                message="Plugin not ready",
                last_check=datetime.now(),
            )
    
    def get_diagnostics(self) -> dict[str, Any]:
        """Return diagnostic information."""
        return {
            "name": self.name,
            "version": self.version,
            "state": self._state.name,
            "last_weather": self._last_weather,
            "update_task_active": self._update_task and not self._update_task.done(),
        }
    
    async def get_weather(self, location: str | None = None) -> dict[str, Any]:
        """Get current weather (public API)."""
        if location:
            return await self._fetch_weather(location)
        return self._last_weather


# Plugin entry point
Plugin = WeatherPlugin