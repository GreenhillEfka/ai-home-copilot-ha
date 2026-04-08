from __future__ import annotations

import logging
from collections.abc import Iterable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ..const import DOMAIN, DATA_CORE, DATA_RUNTIME
from .module import CopilotModule, ModuleContext
from .registry import ModuleRegistry

_LOGGER = logging.getLogger(__name__)


class CopilotRuntime:
    """Runtime container that owns the module registry.

    For now we always run the legacy module to keep behavior unchanged.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.registry = ModuleRegistry()
        self._live_modules: dict[str, dict[str, CopilotModule]] = {}

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
        """Set up modules for a config entry with rollback on critical failure.

        Modules are set up in order.  If a module fails, previously
        set-up modules are rolled back (unloaded) so the entry is not
        left in a partially-initialised state.
        """
        ctx = ModuleContext(hass=self.hass, entry=entry)
        entry_modules: dict[str, CopilotModule] = {}
        failed: list[str] = []

        for name in modules:
            try:
                mod = self.registry.create(name)
                await mod.async_setup_entry(ctx)
                entry_modules[name] = mod
            except Exception:
                _LOGGER.exception("Module %s failed to set up", name)
                failed.append(name)

        if failed:
            _LOGGER.warning(
                "Modules failed to set up: %s — rolling back %d loaded modules",
                ", ".join(failed),
                len(entry_modules),
            )
            # Roll back already-loaded modules so we don't leave partial state
            for rollback_name in reversed(list(entry_modules)):
                try:
                    await entry_modules[rollback_name].async_unload_entry(ctx)
                except Exception:
                    _LOGGER.exception("Rollback of module %s also failed", rollback_name)

            # Retry only the modules that succeeded (graceful degradation)
            entry_modules_retry: dict[str, CopilotModule] = {}
            for name in modules:
                if name in failed:
                    _LOGGER.info("Skipping failed module %s", name)
                    continue
                try:
                    mod = self.registry.create(name)
                    await mod.async_setup_entry(ctx)
                    entry_modules_retry[name] = mod
                except Exception:
                    _LOGGER.exception("Module %s failed on retry — skipping", name)
            self._live_modules[entry.entry_id] = entry_modules_retry
        else:
            self._live_modules[entry.entry_id] = entry_modules

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
