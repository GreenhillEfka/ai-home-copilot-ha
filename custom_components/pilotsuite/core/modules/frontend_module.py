"""PilotSuite Frontend Module — Dashboard lifecycle management.

Owns:
- Dashboard refresh service (pilotsuite.refresh_dashboard)
- View toggle state persistence (which views are enabled/disabled)
- Auto-rebuild when Habitus zones change (debounced)
- SIGNAL_FRONTEND_MODULE_READY for lazy entity creation in switch/button platforms
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send, async_dispatcher_connect
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store

from ...const import (
    DOMAIN,
    FRONTEND_VIEW_STORE_KEY,
    FRONTEND_VIEW_STORE_VERSION,
    SIGNAL_DASHBOARD_REFRESHED,
    SIGNAL_FRONTEND_MODULE_READY,
)
from ..module import CopilotModule, ModuleContext

_LOGGER = logging.getLogger(__name__)

# All 10 dashboard view paths — must match dashboard_wiring.py
DASHBOARD_VIEW_PATHS = (
    "styx", "haushalt", "zonen", "automation",
    "energie", "musik", "ki", "chat",
    "netzwerk", "system",
)


class FrontendModule:
    """CopilotModule for dashboard/frontend lifecycle management."""

    @property
    def name(self) -> str:
        return "frontend_module"

    async def async_setup_entry(self, ctx: ModuleContext) -> None:
        self._hass = ctx.hass
        self._entry = ctx.entry
        self._entry_id = ctx.entry_id
        self._rebuild_lock = asyncio.Lock()
        self._pending_refresh_cancel: Any = None
        self._unsub_zones_listener: Any = None

        # Load persisted view toggle states (default: all enabled)
        self._store = Store(ctx.hass, FRONTEND_VIEW_STORE_VERSION, FRONTEND_VIEW_STORE_KEY)
        stored = await self._store.async_load()
        if isinstance(stored, dict) and "views" in stored:
            self._view_states: dict[str, bool] = stored["views"]
        else:
            self._view_states = {v: True for v in DASHBOARD_VIEW_PATHS}

        # Register in entry data
        entry_store = ctx.hass.data.get(DOMAIN, {}).get(ctx.entry_id)
        if isinstance(entry_store, dict):
            entry_store["frontend_module"] = self

        # Register refresh_dashboard service
        if not ctx.hass.services.has_service(DOMAIN, "refresh_dashboard"):
            ctx.hass.services.async_register(
                DOMAIN,
                "refresh_dashboard",
                self._handle_refresh_dashboard,
            )

        # Auto-rebuild on zone changes
        try:
            from ...habitus_zones_store_v2 import SIGNAL_HABITUS_ZONES_V2_UPDATED

            @callback
            def _on_zones_updated(updated_entry_id: str) -> None:
                if str(updated_entry_id) != self._entry_id:
                    return
                self._schedule_debounced_rebuild("habitus_zones_updated")

            self._unsub_zones_listener = async_dispatcher_connect(
                ctx.hass,
                SIGNAL_HABITUS_ZONES_V2_UPDATED,
                _on_zones_updated,
            )
        except Exception:
            _LOGGER.debug("Could not subscribe to zones signal")

        # Signal that module is ready (for lazy entity creation in switch/button)
        async_dispatcher_send(ctx.hass, SIGNAL_FRONTEND_MODULE_READY, ctx.entry_id)
        _LOGGER.info("FrontendModule ready — 8 view toggles, refresh service registered")

    async def async_unload_entry(self, ctx: ModuleContext) -> bool:
        # Cancel pending refresh
        if callable(self._pending_refresh_cancel):
            self._pending_refresh_cancel()
            self._pending_refresh_cancel = None

        # Unsubscribe from zone signal
        if callable(self._unsub_zones_listener):
            self._unsub_zones_listener()
            self._unsub_zones_listener = None

        # Remove service
        if ctx.hass.services.has_service(DOMAIN, "refresh_dashboard"):
            ctx.hass.services.async_remove(DOMAIN, "refresh_dashboard")

        # Remove from entry data
        entry_store = ctx.hass.data.get(DOMAIN, {}).get(ctx.entry_id)
        if isinstance(entry_store, dict):
            entry_store.pop("frontend_module", None)

        return True

    # ── Public API ──

    def get_view_states(self) -> dict[str, bool]:
        """Return current view toggle states (sync-safe)."""
        return dict(self._view_states)

    async def async_set_view_enabled(self, view_path: str, enabled: bool) -> None:
        """Toggle a dashboard view and trigger rebuild."""
        if view_path not in self._view_states:
            return
        if self._view_states[view_path] == enabled:
            return
        self._view_states[view_path] = enabled
        await self._store.async_save({"views": self._view_states})
        self._schedule_debounced_rebuild(f"view_toggle_{view_path}")

    async def async_rebuild_dashboard(self, reason: str = "manual") -> None:
        """Rebuild the storage-mode dashboard with current view states."""
        async with self._rebuild_lock:
            try:
                from ...dashboard_wiring import (
                    _build_storage_dashboard_config,
                    _STORAGE_DASHBOARD_URL_PATH,
                )

                hass = self._hass

                # Gather PilotSuite entities
                ps_entities = sorted(
                    eid
                    for eid in hass.states.async_entity_ids()
                    if "pilotsuite" in eid or "copilot" in eid
                )

                # Build config with enabled views filter
                enabled = {v for v, on in self._view_states.items() if on}
                config = _build_storage_dashboard_config(ps_entities, enabled_views=enabled)

                # Write to storage
                dashboard_id = _STORAGE_DASHBOARD_URL_PATH.replace("-", "_")
                store = Store(hass, 1, f"lovelace.{dashboard_id}")
                await store.async_save({"config": config})

                # Also regenerate YAML dashboards
                try:
                    from ...habitus_dashboard import async_generate_habitus_zones_dashboard
                    from ...pilotsuite_dashboard import async_generate_pilotsuite_dashboard
                    await async_generate_pilotsuite_dashboard(hass, self._entry, notify=False)
                    await async_generate_habitus_zones_dashboard(hass, self._entry_id, notify=False)
                except Exception:
                    _LOGGER.debug("YAML dashboard regeneration skipped")

                # Fire event for automations
                hass.bus.async_fire(
                    SIGNAL_DASHBOARD_REFRESHED,
                    {"reason": reason, "views_enabled": list(enabled)},
                )
                _LOGGER.info("Dashboard rebuilt (%s), %d views enabled", reason, len(enabled))

            except Exception:
                _LOGGER.exception("Failed to rebuild dashboard (%s)", reason)

    # ── Private ──

    @callback
    def _schedule_debounced_rebuild(self, reason: str) -> None:
        """Debounce rapid rebuild triggers to a single execution."""
        if callable(self._pending_refresh_cancel):
            self._pending_refresh_cancel()

        @callback
        def _run_refresh(_now) -> None:
            self._pending_refresh_cancel = None
            self._hass.async_create_task(self.async_rebuild_dashboard(reason))

        self._pending_refresh_cancel = async_call_later(self._hass, 2.0, _run_refresh)

    async def _handle_refresh_dashboard(self, call: ServiceCall) -> None:
        """Handle pilotsuite.refresh_dashboard service call."""
        await self.async_rebuild_dashboard("service_call")
