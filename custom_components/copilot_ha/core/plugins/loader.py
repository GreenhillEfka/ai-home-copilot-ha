"""Plugin loader and registry for PilotSuite.

Handles dynamic loading, dependency resolution, and lifecycle management.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .manifest import PluginManifest, validate_plugin_structure
from .types import LoadedPlugin, PluginError, PluginInitError, PluginInterface, PluginLoadError, PluginState

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing loaded plugins."""
    
    def __init__(self) -> None:
        """Initialize registry."""
        self._plugins: dict[str, LoadedPlugin] = {}
        self._capabilities: dict[str, list[str]] = {}  # capability -> plugin names
        self._lock = asyncio.Lock()
    
    async def register(self, plugin: LoadedPlugin) -> None:
        """Register a loaded plugin."""
        async with self._lock:
            self._plugins[plugin.manifest.name] = plugin
            
            # Register capabilities
            for capability in plugin.manifest.metadata.provides:
                if capability not in self._capabilities:
                    self._capabilities[capability] = []
                self._capabilities[capability].append(plugin.manifest.name)
            
            _LOGGER.info("Registered plugin: %s v%s", plugin.manifest.name, plugin.manifest.version)
    
    async def unregister(self, name: str) -> None:
        """Unregister a plugin."""
        async with self._lock:
            if name not in self._plugins:
                return
            
            plugin = self._plugins.pop(name)
            
            # Unregister capabilities
            for capability in plugin.manifest.metadata.provides:
                if capability in self._capabilities:
                    self._capabilities[capability].remove(name)
                    if not self._capabilities[capability]:
                        del self._capabilities[capability]
            
            _LOGGER.info("Unregistered plugin: %s", name)
    
    def get(self, name: str) -> LoadedPlugin | None:
        """Get plugin by name."""
        return self._plugins.get(name)
    
    def all(self) -> dict[str, LoadedPlugin]:
        """Get all plugins."""
        return dict(self._plugins)
    
    def find_by_capability(self, capability: str) -> list[LoadedPlugin]:
        """Find plugins providing a specific capability."""
        plugin_names = self._capabilities.get(capability, [])
        return [self._plugins[name] for name in plugin_names if name in self._plugins]
    
    async def get_diagnostics(self) -> dict[str, dict[str, any]]:
        """Get diagnostics for all plugins."""
        async with self._lock:
            return {name: plugin.to_dict() for name, plugin in self._plugins.items()}


class PluginLoader:
    """Dynamic plugin loader for PilotSuite."""
    
    def __init__(self, plugin_dir: Path, hass: HomeAssistant) -> None:
        """Initialize loader.
        
        Args:
            plugin_dir: Directory containing plugin subdirectories
            hass: HomeAssistant instance
        """
        self.plugin_dir = plugin_dir
        self.hass = hass
        self.registry = PluginRegistry()
        self._loaded_modules: dict[str, importlib.types.ModuleType] = {}
    
    async def discover_plugins(self) -> list[PluginManifest]:
        """Discover available plugins in the plugin directory.
        
        Returns list of valid plugin manifests.
        """
        if not self.plugin_dir.exists():
            _LOGGER.info("Plugin directory does not exist: %s", self.plugin_dir)
            return []
        
        manifests = []
        
        for item in self.plugin_dir.iterdir():
            if not item.is_dir():
                continue
            
            manifest = PluginManifest.from_directory(item)
            if manifest is None:
                continue
            
            # Validate structure
            errors = validate_plugin_structure(manifest)
            if errors:
                _LOGGER.warning("Plugin %s validation errors: %s", item.name, errors)
                continue
            
            manifests.append(manifest)
            _LOGGER.debug("Discovered plugin: %s v%s", manifest.name, manifest.version)
        
        _LOGGER.info("Discovered %d plugins", len(manifests))
        return manifests
    
    async def load_plugin(self, manifest: PluginManifest) -> LoadedPlugin | None:
        """Load a single plugin.
        
        Args:
            manifest: Plugin manifest to load
            
        Returns:
            LoadedPlugin instance or None if loading failed
        """
        try:
            _LOGGER.info("Loading plugin: %s v%s", manifest.name, manifest.version)
            
            # Import the module
            module = await self._import_plugin_module(manifest)
            if not module:
                return None
            
            # Get the plugin class
            plugin_class = getattr(module, manifest.metadata.entry_class)
            if not plugin_class:
                _LOGGER.error("Plugin class '%s' not found in %s", manifest.metadata.entry_class, manifest.name)
                return None
            
            # Instantiate plugin
            plugin_instance = plugin_class()
            if not isinstance(plugin_instance, PluginInterface):
                _LOGGER.error("Plugin %s does not implement PluginInterface", manifest.name)
                return None
            
            # Create loaded plugin wrapper
            loaded_plugin = LoadedPlugin(
                manifest=manifest,
                instance=plugin_instance,
                load_time=datetime.now(),
                source_path=manifest.source_dir,
            )
            
            # Initialize plugin
            loaded_plugin.health = PluginState.INITIALIZING
            try:
                await plugin_instance.async_init(self.hass)
                loaded_plugin.health = PluginState.READY
                _LOGGER.info("Plugin %s initialized successfully", manifest.name)
            except Exception as err:
                loaded_plugin.health = PluginState.ERROR
                _LOGGER.error("Failed to initialize plugin %s: %s", manifest.name, err)
                raise PluginInitError(f"Failed to initialize {manifest.name}: {err}") from err
            
            # Register plugin
            await self.registry.register(loaded_plugin)
            
            return loaded_plugin
            
        except Exception as err:
            _LOGGER.error("Failed to load plugin %s: %s", manifest.name, err)
            return None
    
    async def _import_plugin_module(self, manifest: PluginManifest) -> importlib.types.ModuleType | None:
        """Import plugin module using dynamic import."""
        try:
            # Add plugin directory to sys.path temporarily
            plugin_path = str(manifest.source_dir)
            if plugin_path not in sys.path:
                sys.path.insert(0, plugin_path)
            
            # Import the module
            module_name = f"plugin_{manifest.name}"  # Prefix to avoid conflicts
            spec = importlib.util.spec_from_file_location(
                module_name,
                manifest.source_dir / f"{manifest.metadata.entry_module}.py"
            )
            
            if spec is None or spec.loader is None:
                _LOGGER.error("Failed to create module spec for %s", manifest.name)
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            self._loaded_modules[manifest.name] = module
            return module
            
        except Exception as err:
            _LOGGER.error("Failed to import plugin module %s: %s", manifest.name, err)
            return None
    
    async def load_all_plugins(self) -> int:
        """Load all discovered plugins.
        
        Returns number of successfully loaded plugins.
        """
        manifests = await self.discover_plugins()
        loaded_count = 0
        
        for manifest in manifests:
            # Check dependencies
            if not await self._check_dependencies(manifest):
                _LOGGER.warning("Skipping %s due to missing dependencies", manifest.name)
                continue
            
            # Load plugin
            loaded_plugin = await self.load_plugin(manifest)
            if loaded_plugin:
                loaded_count += 1
        
        return loaded_count
    
    async def _check_dependencies(self, manifest: PluginManifest) -> bool:
        """Check if all plugin dependencies are satisfied."""
        for dep in manifest.metadata.dependencies:
            if not self.registry.get(dep):
                _LOGGER.warning("Plugin %s depends on %s which is not loaded", manifest.name, dep)
                return False
        return True
    
    async def unload_plugin(self, name: str) -> bool:
        """Unload a plugin.
        
        Args:
            name: Plugin name to unload
            
        Returns:
            True if successful, False otherwise
        """
        try:
            plugin = self.registry.get(name)
            if not plugin:
                _LOGGER.warning("Plugin %s not found", name)
                return False
            
            _LOGGER.info("Unloading plugin: %s", name)
            
            # Stop plugin
            plugin.health = PluginState.UNLOADING
            try:
                await plugin.instance.async_stop()
            except Exception as err:
                _LOGGER.warning("Error stopping plugin %s: %s", name, err)
            
            # Unregister from registry
            await self.registry.unregister(name)
            
            # Remove from sys.modules if loaded
            module_name = f"plugin_{name}"
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            if name in self._loaded_modules:
                del self._loaded_modules[name]
            
            _LOGGER.info("Plugin %s unloaded successfully", name)
            return True
            
        except Exception as err:
            _LOGGER.error("Failed to unload plugin %s: %s", name, err)
            return False
    
    async def reload_plugin(self, name: str) -> bool:
        """Reload a plugin.
        
        Args:
            name: Plugin name to reload
            
        Returns:
            True if successful, False otherwise
        """
        plugin = self.registry.get(name)
        if not plugin:
            _LOGGER.warning("Plugin %s not found", name)
            return False
        
        # Unload first
        if not await self.unload_plugin(name):
            return False
        
        # Reload manifest
        manifest = PluginManifest.from_directory(plugin.manifest.source_dir)
        if not manifest:
            _LOGGER.error("Failed to reload manifest for %s", name)
            return False
        
        # Load again
        loaded_plugin = await self.load_plugin(manifest)
        return loaded_plugin is not None
    
    async def stop_all(self) -> None:
        """Stop all loaded plugins."""
        plugins = list(self.registry.all().keys())
        
        for name in plugins:
            await self.unload_plugin(name)
        
        _LOGGER.info("All plugins stopped")