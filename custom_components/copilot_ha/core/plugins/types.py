"""Plugin types and interfaces for PilotSuite.

Defines the contract between the plugin system and external modules.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .manifest import PluginManifest


class PluginState(Enum):
    """Lifecycle states of a plugin."""
    UNLOADED = auto()
    LOADING = auto()
    LOADED = auto()
    INITIALIZING = auto()
    READY = auto()
    ERROR = auto()
    UNLOADING = auto()


class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass


class PluginLoadError(PluginError):
    """Raised when plugin loading fails."""
    pass


class PluginInitError(PluginError):
    """Raised when plugin initialization fails."""
    pass


class PluginDependencyError(PluginError):
    """Raised when plugin dependencies are missing."""
    pass


@dataclass
class PluginHealth:
    """Health status of a plugin."""
    state: PluginState
    last_check: datetime = field(default_factory=datetime.now)
    message: str = ""
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "state": self.state.name,
            "last_check": self.last_check.isoformat(),
            "message": self.message,
            "errors": self.errors,
        }


class PluginInterface(ABC):
    """Base interface for all PilotSuite plugins.
    
    External plugins must implement this interface to be loaded
    and managed by the PluginLoader.
    
    Example:
        class MyPlugin(PluginInterface):
            @property
            def name(self) -> str:
                return "my_plugin"
            
            async def async_init(self, hass: HomeAssistant) -> None:
                # Setup code here
                pass
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier (snake_case)."""
        pass

    @property
    def version(self) -> str:
        """Plugin version in semver format."""
        return "0.1.0"

    @property
    def dependencies(self) -> list[str]:
        """List of required plugin names."""
        return []

    @property
    def provides(self) -> list[str]:
        """List of capabilities this plugin provides."""
        return []

    @abstractmethod
    async def async_init(self, hass: HomeAssistant) -> None:
        """Initialize the plugin.
        
        Called after loading and before the plugin is considered ready.
        Should set up any async resources, register services, etc.
        """
        pass

    async def async_start(self) -> None:
        """Start the plugin (optional).
        
        Called after all plugins are initialized.
        """
        pass

    async def async_stop(self) -> None:
        """Stop the plugin (optional).
        
        Called during shutdown or reload.
        Should clean up resources gracefully.
        """
        pass

    async def async_health_check(self) -> PluginHealth:
        """Return current health status (optional)."""
        return PluginHealth(state=PluginState.READY)

    def get_diagnostics(self) -> dict[str, Any]:
        """Return diagnostic information (optional)."""
        return {
            "name": self.name,
            "version": self.version,
            "state": "ready",
        }


@dataclass
class LoadedPlugin:
    """Wrapper for a loaded plugin instance."""
    manifest: PluginManifest
    instance: PluginInterface
    health: PluginHealth = field(default_factory=lambda: PluginHealth(PluginState.UNLOADED))
    load_time: datetime | None = None
    source_path: Path | None = None

    @property
    def state(self) -> PluginState:
        """Current plugin state."""
        return self.health.state

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "manifest": self.manifest.to_dict(),
            "health": self.health.to_dict(),
            "load_time": self.load_time.isoformat() if self.load_time else None,
            "source_path": str(self.source_path) if self.source_path else None,
        }