"""Shared base class for PilotSuite button entities."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.button import ButtonEntity
from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry

from .entity import CopilotBaseEntity

if TYPE_CHECKING:
    from .coordinator import CopilotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class CopilotButtonBase(CopilotBaseEntity, ButtonEntity):
    """Base class for PilotSuite buttons.

    Provides:
    - Common attribute defaults (``_attr_has_entity_name = False``)
    - Optional ``_entry`` storage when constructed with a ``ConfigEntry``
    - ``_notify()`` helper for persistent notifications
    - ``_call_service()`` helper for HA service calls + notification
    - ``_press_with_notification()`` error wrapper for ``async_press``
    """

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: CopilotDataUpdateCoordinator,
        entry: ConfigEntry | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry

    # -- Helpers -------------------------------------------------------------

    def _notify(
        self,
        message: str,
        *,
        title: str = "PilotSuite",
        notification_id: str | None = None,
    ) -> None:
        """Create a Home Assistant persistent notification."""
        persistent_notification.async_create(
            self.hass,
            message,
            title=title,
            notification_id=notification_id,
        )

    async def _call_service(
        self,
        service: str,
        data: dict[str, Any] | None = None,
        *,
        domain: str = "pilotsuite",
        blocking: bool = False,
    ) -> None:
        """Call a Home Assistant service."""
        await self.hass.services.async_call(
            domain, service, data or {}, blocking=blocking,
        )

    async def _press_with_notification(
        self,
        coro,
        *,
        title: str = "PilotSuite",
        notification_id: str | None = None,
        error_prefix: str = "Failed",
    ) -> Any:
        """Run *coro* and show a persistent notification on failure.

        Returns the coroutine result on success, None on failure.
        """
        try:
            return await coro
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("%s: %s", error_prefix, err)
            self._notify(
                f"{error_prefix}: {err}",
                title=title,
                notification_id=notification_id,
            )
            return None
