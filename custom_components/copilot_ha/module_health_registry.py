"""Module Registry Expansion — Dynamic module loading with health integration (PS-146).

Extends ModuleRegistry to:
- Auto-register health modules
- Lazy-load zone health tracking
- Module dependency resolution
- Health-aware module activation
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from homeassistant.core import HomeAssistant

from .core.registry import ModuleRegistry

_LOGGER = logging.getLogger(__name__)

DOMAIN = "copilot_ha"


class HealthModuleRegistry(ModuleRegistry):
    """Extended ModuleRegistry with health integration."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        super().__init__()
        self.hass = hass
        self.entry_id = entry_id
        self._health_enabled = False
        self._health_modules: dict[str, Any] = {}

    def register_health_module(self, name: str, factory: Callable[[], Any]) -> None:
        """Register a health-aware module."""
        if not self._health_enabled:
            _LOGGER.debug("Health tracking disabled, skipping module %s", name)
            return
        
        super().register(name, factory)
        _LOGGER.info("Health module %s registered", name)

    def enable_health_tracking(self, enabled: bool = True) -> None:
        """Enable/disable health tracking for modules."""
        self._health_enabled = enabled
        
        if enabled:
            _LOGGER.info("Health tracking enabled for entry %s", self.entry_id)
        else:
            _LOGGER.info("Health tracking disabled for entry %s", self.entry_id)

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of all registered modules."""
        status = {
            "entry_id": self.entry_id,
            "health_enabled": self._health_enabled,
            "modules": {},
        }
        
        for name in self.names():
            try:
                module = self.create(name)
                if hasattr(module, "get_health"):
                    status["modules"][name] = module.get_health()
                else:
                    status["modules"][name] = {"status": "active"}
            except Exception as err:  # noqa: BLE001
                status["modules"][name] = {"status": "error", "error": str(err)}
        
        return status

    def activate_health_aware_modules(self) -> list[str]:
        """Activate all health-aware modules."""
        activated = []
        
        for name in self.names():
            try:
                module = self.create(name)
                if hasattr(module, "async_setup_entry"):
                    # HA module with setup
                    if hasattr(module, "async_health_init"):
                        module.async_health_init(self.hass, self.entry_id)
                    activated.append(name)
                    _LOGGER.debug("Health-aware module %s activated", name)
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Failed to activate module %s: %s", name, err)
        
        return activated

    def get_module_dependencies(self, module_name: str) -> list[str]:
        """Get dependencies for a module."""
        module = self.create(module_name)
        if hasattr(module, "dependencies"):
            return module.dependencies
        return []

    def resolve_module_graph(self) -> dict[str, list[str]]:
        """Resolve module dependency graph."""
        graph = {}
        
        for name in self.names():
            graph[name] = self.get_module_dependencies(name)
        
        return graph


async def async_setup_health_module_registry(
    hass: HomeAssistant,
    entry_id: str,
) -> HealthModuleRegistry:
    """Set up health module registry for a config entry."""
    from .habitus_zones_store_v2 import async_get_zones_v2
    
    zones = await async_get_zones_v2(hass, entry_id)
    if not zones:
        _LOGGER.debug("No zones found, skipping health module registry")
        return HealthModuleRegistry(hass, entry_id)
    
    registry = HealthModuleRegistry(hass, entry_id)
    registry.enable_health_tracking(True)
    
    # Auto-register health modules
    registry.register_health_module("zone_health_sensor", lambda: None)
    registry.register_health_module("zone_health_card", lambda: None)
    registry.register_health_module("zone_health_service", lambda: None)
    registry.register_health_module("zone_health_automation", lambda: None)
    
    _LOGGER.info("Health module registry set up for %d zones", len(zones))
    
    return registry


async def async_get_module_health_status(
    hass: HomeAssistant,
    entry_id: str,
) -> dict[str, Any]:
    """Get health status of all modules for an entry."""
    if DOMAIN not in hass.data or f"module_registry_{entry_id}" not in hass.data[DOMAIN]:
        return {"error": "Module registry not found"}
    
    registry = hass.data[DOMAIN][f"module_registry_{entry_id}"]
    return registry.get_health_status()
