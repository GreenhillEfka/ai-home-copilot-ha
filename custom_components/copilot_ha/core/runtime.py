"""PilotSuite — Core runtime with tiered lazy module loading (Phase 7 Production Readiness)."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ..const import DOMAIN, DATA_CORE, DATA_RUNTIME
from .module import CopilotModule, ModuleContext
from .registry import ModuleRegistry

_LOGGER = logging.getLogger(__name__)

# ── Module loading tiers (Production Readiness) ─────────────────────────
# TIER_EAGER: load during HA startup — core user-facing functionality
TIER_EAGER = frozenset({
    "legacy",
    "brain_graph_sync",
    "habitus_miner",
    "frontend_module",
})
# TIER_DEFERRED: load in background after HA startup — side systems, analytics
TIER_DEFERRED_BACKGROUND = frozenset({
    "performance_scaling",
    "events_forwarder",
    "knowledge_graph_sync",
    "ml_context",
})
# TIER_DEFERRED_ON_DEMAND: load only when first accessed
TIER_DEFERRED_ON_DEMAND = frozenset({
    "camera_context",
    "frigate_bridge",
    "quick_search",
    "voice_context",
    "weather_context",
    "network",
    "media_zones",
    "mood",
    "mood_context",
    "energy_context",
    "home_alerts",
    "calendar_module",
    "waste_reminder",
    "birthday_reminder",
    "entity_tags",
    "person_tracking",
    "scene_module",
    "homekit_bridge",
    "unifi_module",
    "history_backfill",
    "dev_surface",
    "ops_runbook",
    "candidate_poller",
    "licht_module",
    "helligkeit_module",
    "heiz_module",
    "bewegung_module",
    "praesenz_module",
    "frontend_module",
    "character_module",
})

_DEFERRED_LOAD_DELAY_S = 5.0  # seconds to wait after HA startup before loading deferred modules


class CopilotRuntime:
    """Runtime container that owns the module registry."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.registry = ModuleRegistry()
        self._live_modules: dict[str, dict[str, CopilotModule]] = {}
        self._deferred_modules: set[str] = set()  # track which modules are deferred (not yet loaded)

    @classmethod
    def get(cls, hass: HomeAssistant) -> "CopilotRuntime":
        hass.data.setdefault(DOMAIN, {})
        core = hass.data[DOMAIN].setdefault(DATA_CORE, {})
        runtime = core.get(DATA_RUNTIME)
        if isinstance(runtime, CopilotRuntime):
            return runtime

        runtime = CopilotRuntime(hass)
        core[DATA_RUNTIME] = runtime
        return runtime

    async def async_setup_entry(self, entry: ConfigEntry, modules: Iterable[str]) -> None:
        """Set up modules in tiers: eager first, deferred background, on-demand on access.

        TIER_EAGER        → load immediately
        TIER_DEFERRED     → load in background after _DEFERRED_LOAD_DELAY_S
        TIER_DEFERRED_ON_DEMAND → load only when first accessed
        """
        ctx = ModuleContext(hass=self.hass, entry=entry)
        modules_list = list(modules)
        eager = [m for m in modules_list if m in TIER_EAGER]
        deferred = [m for m in modules_list if m in TIER_DEFERRED_BACKGROUND]
        on_demand = [m for m in modules_list if m in TIER_DEFERRED_ON_DEMAND]
        unknown = [m for m in modules_list if m not in TIER_EAGER | TIER_DEFERRED_BACKGROUND | TIER_DEFERRED_ON_DEMAND]
        # Treat unknown modules as eager to preserve compatibility with older configurations
        eager.extend(unknown)

        _LOGGER.info(
            "PilotSuite module tiers — eager:%d deferred:%d on_demand:%d unknown:%d",
            len(eager), len(deferred), len(on_demand), len(unknown),
        )

        entry_modules: dict[str, CopilotModule] = {}

        # ── Tier 1: Eager (immediate) ───────────────────────────────────
        for name in eager:
            try:
                mod = self.registry.create(name)
                await mod.async_setup_entry(ctx)
                entry_modules[name] = mod
            except Exception:
                _LOGGER.exception("Eager module %s failed to set up", name)
                continue

        # ── Tier 2: Deferred background (loaded 5s after HA startup) ────
        self._deferred_modules = set(deferred)

        async def _load_deferred_modules() -> None:
            """Load deferred modules after HA is fully up."""
            await asyncio.sleep(_DEFERRED_LOAD_DELAY_S)
            _LOGGER.info("Loading %d deferred background modules", len(deferred))
            for name in deferred:
                if name in self._live_modules.get(entry.entry_id, {}):
                    continue  # already loaded (e.g. via on-demand path)
                try:
                    mod = self.registry.create(name)
                    await mod.async_setup_entry(ctx)
                    if entry.entry_id not in self._live_modules:
                        self._live_modules[entry.entry_id] = {}
                    self._live_modules[entry.entry_id][name] = mod
                    self._deferred_modules.discard(name)
                    _LOGGER.debug("Deferred module %s loaded", name)
                except Exception:
                    _LOGGER.exception("Deferred module %s failed — skipping", name)
                    self._deferred_modules.discard(name)

        # Fire and forget — don't block setup
        create_task = getattr(self.hass, "async_create_task", None)
        if callable(create_task):
            create_task(_load_deferred_modules())
        else:
            asyncio.create_task(_load_deferred_modules())

        self._live_modules[entry.entry_id] = entry_modules

    async def async_load_module(self, entry: ConfigEntry, name: str) -> CopilotModule | None:
        """Load a TIER_DEFERRED_ON_DEMAND module on first access (blocking).

        Safe to call multiple times — returns existing module if already loaded.
        """
        live = self._live_modules.get(entry.entry_id, {})
        if name in live:
            return live[name]
        if name not in TIER_DEFERRED_ON_DEMAND:
            _LOGGER.warning("async_load_module called for non on-demand module: %s", name)
            return None

        ctx = ModuleContext(hass=self.hass, entry=entry)
        try:
            mod = self.registry.create(name)
            await mod.async_setup_entry(ctx)
            if entry.entry_id not in self._live_modules:
                self._live_modules[entry.entry_id] = {}
            self._live_modules[entry.entry_id][name] = mod
            self._deferred_modules.discard(name)
            _LOGGER.debug("On-demand module %s loaded", name)
            return mod
        except Exception:
            _LOGGER.exception("On-demand module %s failed to load", name)
            return None

    @property
    def deferred_module_count(self) -> int:
        """Number of deferred modules not yet loaded."""
        return len(self._deferred_modules)

    async def async_unload_entry(self, entry: ConfigEntry, modules: Iterable[str]) -> bool:
        """Unload all modules for a config entry.

        Always attempts to unload every module even if earlier ones fail.
        """
        ctx = ModuleContext(hass=self.hass, entry=entry)
        entry_modules = self._live_modules.pop(entry.entry_id, {})
        unload_ok = True
        for name in reversed(list(modules)):
            mod = entry_modules.get(name)
            if mod is None:
                _LOGGER.debug("Module %s was not loaded — skip unload", name)
                continue
            try:
                result = await mod.async_unload_entry(ctx)
                if not isinstance(result, bool):
                    _LOGGER.warning(
                        "Module %s returned non-bool unload result %r; coercing to bool",
                        name,
                        result,
                    )
                unload_ok = bool(result) and unload_ok
            except Exception:
                _LOGGER.exception("Module %s failed to unload", name)
                unload_ok = False
        return unload_ok
