"""Plugin System for PilotSuite.

Dynamically loads modules from /plugins directory at runtime.
Provides hot-reload capability and plugin isolation.
"""

from __future__ import annotations

from .loader import PluginLoader, PluginRegistry
from .manifest import PluginManifest, PluginMetadata
from .types import PluginInterface, PluginState, PluginError

__all__ = [
    "PluginLoader",
    "PluginRegistry", 
    "PluginManifest",
    "PluginMetadata",
    "PluginInterface",
    "PluginState",
    "PluginError",
]