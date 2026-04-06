"""Plugin manifest schema and validation for PilotSuite.

Defines the plugin.json format and metadata structures.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Core plugin metadata from plugin.json."""
    name: str
    version: str
    description: str
    author: str
    
    # Optional fields
    min_pilotsuite_version: str | None = None
    dependencies: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    icon: str | None = None
    
    # Entry points
    entry_module: str = "plugin"
    entry_class: str = "Plugin"
    
    # Permissions
    requires: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginMetadata":
        """Create metadata from dictionary."""
        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            min_pilotsuite_version=data.get("min_pilotsuite_version"),
            dependencies=data.get("dependencies", []),
            conflicts=data.get("conflicts", []),
            provides=data.get("provides", []),
            tags=data.get("tags", []),
            icon=data.get("icon"),
            entry_module=data.get("entry_module", "plugin"),
            entry_class=data.get("entry_class", "Plugin"),
            requires=data.get("requires", []),
            permissions=data.get("permissions", []),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "min_pilotsuite_version": self.min_pilotsuite_version,
            "dependencies": self.dependencies,
            "conflicts": self.conflicts,
            "provides": self.provides,
            "tags": self.tags,
            "icon": self.icon,
            "entry_module": self.entry_module,
            "entry_class": self.entry_class,
            "requires": self.requires,
            "permissions": self.permissions,
        }


@dataclass
class PluginManifest:
    """Full plugin manifest including path information."""
    metadata: PluginMetadata
    source_dir: Path
    
    @property
    def name(self) -> str:
        """Plugin name."""
        return self.metadata.name
    
    @property
    def version(self) -> str:
        """Plugin version."""
        return self.metadata.version
    
    @property
    def entry_point(self) -> str:
        """Full entry point path."""
        return f"{self.metadata.entry_module}:{self.metadata.entry_class}"
    
    @classmethod
    def from_directory(cls, path: Path) -> "PluginManifest | None":
        """Load manifest from plugin directory.
        
        Looks for plugin.json in the given directory.
        Returns None if no valid manifest found.
        """
        manifest_path = path / "plugin.json"
        if not manifest_path.exists():
            _LOGGER.debug("No plugin.json found in %s", path)
            return None
        
        try:
            with open(manifest_path, encoding="utf-8") as f:
                data = json.load(f)
            
            metadata = PluginMetadata.from_dict(data)
            
            # Validate required fields
            if not metadata.name or not metadata.version:
                _LOGGER.warning("Invalid plugin.json in %s: missing name or version", path)
                return None
            
            return cls(metadata=metadata, source_dir=path)
            
        except json.JSONDecodeError as err:
            _LOGGER.error("Invalid JSON in %s: %s", manifest_path, err)
            return None
        except Exception as err:
            _LOGGER.error("Failed to load manifest from %s: %s", path, err)
            return None
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            **self.metadata.to_dict(),
            "source_dir": str(self.source_dir),
            "entry_point": self.entry_point,
        }


def validate_plugin_structure(manifest: PluginManifest) -> list[str]:
    """Validate plugin directory structure.
    
    Returns list of validation errors (empty if valid).
    """
    errors = []
    
    # Check main module exists
    entry_file = manifest.source_dir / f"{manifest.metadata.entry_module}.py"
    entry_init = manifest.source_dir / manifest.metadata.entry_module / "__init__.py"
    
    if not entry_file.exists() and not entry_init.exists():
        errors.append(f"Entry module '{manifest.metadata.entry_module}' not found")
    
    # Check for __init__.py in package
    if (manifest.source_dir / manifest.metadata.entry_module).is_dir():
        if not (manifest.source_dir / manifest.metadata.entry_module / "__init__.py").exists():
            errors.append(f"Package '{manifest.metadata.entry_module}' missing __init__.py")
    
    return errors