"""Dashboard Widget Plugin Registry.

Defines the plugin interface and hosts the widget registry.
Widgets register via WIDGET_REGISTRY.register().
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class WidgetPlugin:
    """A registered dashboard widget."""
    name: str
    blueprint_bp: Any = None          # Flask Blueprint
    socketio_register: Callable[[Any], None] | None = None  # register_socketio_events(sio)
    broadcast_fn: Callable[[], None] | None = None          # optional broadcast_updates()
    static_assets: tuple[str, str] | None = None  # (folder, url_prefix)
    depends_on: list[str] = field(default_factory=list)       # other widget names


class WidgetRegistry:
    """Central widget plugin registry."""

    def __init__(self) -> None:
        self._widgets: dict[str, WidgetPlugin] = {}

    def register(self, plugin: WidgetPlugin) -> None:
        if plugin.name in self._widgets:
            raise ValueError(f"Widget '{plugin.name}' already registered")
        self._widgets[plugin.name] = plugin

    def get(self, name: str) -> WidgetPlugin | None:
        return self._widgets.get(name)

    def all(self) -> list[WidgetPlugin]:
        return list(self._widgets.values())

    def names(self) -> list[str]:
        return list(self._widgets.keys())

    def by_bp(self, blueprint_bp: Any) -> WidgetPlugin | None:
        for w in self._widgets.values():
            if w.blueprint_bp is blueprint_bp:
                return w
        return None


# Singleton registry
WIDGET_REGISTRY = WidgetRegistry()


def widget_plugin(
    name: str,
    depends_on: list[str] | None = None,
    static_assets: tuple[str, str] | None = None,
):
    """Decorator to register a widget plugin class or factory."""
    def decorator(cls_or_fn: Any) -> Any:
        plugin = WidgetPlugin(
            name=name,
            depends_on=depends_on or [],
            static_assets=static_assets,
        )
        WIDGET_REGISTRY.register(plugin)
        return cls_or_fn
    return decorator


# ── Auto-discovery ──────────────────────────────────────────────────────────────

_WIDGET_DIR = os.path.dirname(__file__)


def discover_widgets() -> list[str]:
    """Import all widgets in this directory to trigger @widget_plugin registration."""
    discovered = []
    for filename in os.listdir(_WIDGET_DIR):
        if filename.startswith("_") or filename.startswith("."):
            continue
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            try:
                __import__(f"widgets.{module_name}")
                discovered.append(module_name)
            except Exception:
                pass
    return discovered
