"""Update check buttons and version sensors for PilotSuite HA and Core."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiohttp

from homeassistant.components.button import ButtonEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import EntityCategory

from .entity import CopilotBaseEntity

if TYPE_CHECKING:
    from .coordinator import CopilotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

GITHUB_HA_RELEASES_URL = (
    "https://api.github.com/repos/GreenhillEfka/pilotsuite-styx-ha/releases/latest"
)
GITHUB_CORE_RELEASES_URL = (
    "https://api.github.com/repos/GreenhillEfka/pilotsuite-styx-core/releases/latest"
)


_CACHED_LOCAL_VERSION: str | None = None


def _read_local_version() -> str:
    """Read the local VERSION file from this integration package."""
    global _CACHED_LOCAL_VERSION
    if _CACHED_LOCAL_VERSION is not None:
        return _CACHED_LOCAL_VERSION
    version_file = Path(__file__).resolve().parent / "VERSION"
    try:
        _CACHED_LOCAL_VERSION = version_file.read_text(encoding="utf-8").strip()
    except Exception:  # noqa: BLE001
        _CACHED_LOCAL_VERSION = "unknown"
    return _CACHED_LOCAL_VERSION


async def _async_read_local_version(hass) -> str:
    """Read the local VERSION file without blocking the HA event loop."""
    return await hass.async_add_executor_job(_read_local_version)


def _compare_versions(local: str, remote: str) -> int:
    """Compare two semver-style version strings.

    Returns:
        -1 if local < remote (update available)
         0 if local == remote (up to date)
         1 if local > remote (local is ahead)
    """
    try:
        local_parts = [int(p) for p in local.split(".")]
        remote_parts = [int(p) for p in remote.split(".")]
    except (ValueError, AttributeError):
        return 0  # cannot compare, treat as equal

    for lp, rp in zip(local_parts, remote_parts):
        if lp < rp:
            return -1
        if lp > rp:
            return 1

    # If one has more parts, the longer one is "greater".
    if len(local_parts) < len(remote_parts):
        return -1
    if len(local_parts) > len(remote_parts):
        return 1
    return 0


async def _fetch_latest_release(hass, url: str) -> str | None:
    """Fetch the latest release tag from GitHub API. Returns version string or None."""
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            url,
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status != 200:
                _LOGGER.warning("GitHub API returned %s for %s", resp.status, url)
                return None
            data = await resp.json()
            tag = data.get("tag_name", "")
            # Strip leading 'v' if present.
            return tag.lstrip("v") if tag else None
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Failed to fetch latest release from %s: %s", url, err)
        return None


# ── Version Sensors ──────────────────────────────────────────────────


class PilotSuiteHAVersionSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing the current HA integration version and latest available."""

    _attr_name = "PilotSuite HA Version"
    _attr_unique_id = "pilotsuite_ha_version_check"
    _attr_icon = "mdi:package-variant"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._local_version = "unknown"
        self._latest_version: str | None = None
        self._last_check: str | None = None

    async def async_added_to_hass(self) -> None:
        """Load local version asynchronously to avoid blocking the event loop."""
        await super().async_added_to_hass()
        self._local_version = await _async_read_local_version(self.hass)
        self.async_write_ha_state()

    @property
    def native_value(self) -> str:
        return self._local_version

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {
            "local_version": self._local_version,
        }
        if self._latest_version is not None:
            attrs["latest_version"] = self._latest_version
            cmp = _compare_versions(self._local_version, self._latest_version)
            attrs["update_available"] = cmp < 0
        if self._last_check is not None:
            attrs["last_check"] = self._last_check
        return attrs

    def update_check_result(self, latest: str | None) -> None:
        """Update the sensor with the latest check result."""
        self._latest_version = latest
        self._last_check = datetime.now(timezone.utc).isoformat()
        self.async_write_ha_state()


class PilotSuiteCoreVersionSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing the current Core add-on version and latest available."""

    _attr_name = "PilotSuite Core Version"
    _attr_unique_id = "pilotsuite_core_version_check"
    _attr_icon = "mdi:package-variant-closed"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = False

    def __init__(self, coordinator: CopilotDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._local_version: str | None = None
        self._latest_version: str | None = None
        self._last_check: str | None = None

    @property
    def native_value(self) -> str | None:
        # Try to get Core version from coordinator data.
        if self.coordinator.data:
            ver = self.coordinator.data.get("core_version") or self.coordinator.data.get("version")
            if ver:
                self._local_version = str(ver)
        return self._local_version

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        if self._local_version:
            attrs["local_version"] = self._local_version
        if self._latest_version is not None:
            attrs["latest_version"] = self._latest_version
            if self._local_version:
                cmp = _compare_versions(self._local_version, self._latest_version)
                attrs["update_available"] = cmp < 0
        if self._last_check is not None:
            attrs["last_check"] = self._last_check
        return attrs

    def update_check_result(self, latest: str | None, local: str | None = None) -> None:
        """Update the sensor with the latest check result."""
        self._latest_version = latest
        if local:
            self._local_version = local
        self._last_check = datetime.now(timezone.utc).isoformat()
        self.async_write_ha_state()


# ── Update Check Buttons ─────────────────────────────────────────────


class CheckHAUpdateButton(CopilotBaseEntity, ButtonEntity):
    """Check for PilotSuite HA integration updates."""

    _attr_name = "PilotSuite check HA update"
    _attr_unique_id = "pilotsuite_check_ha_update"
    _attr_icon = "mdi:update"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: CopilotDataUpdateCoordinator,
        ha_version_sensor: PilotSuiteHAVersionSensor,
    ) -> None:
        super().__init__(coordinator)
        self._ha_version_sensor = ha_version_sensor

    async def async_press(self) -> None:
        """Check GitHub for latest HA integration release."""
        local = await _async_read_local_version(self.hass)
        latest = await _fetch_latest_release(self.hass, GITHUB_HA_RELEASES_URL)

        if latest is None:
            persistent_notification.async_create(
                self.hass,
                "Could not reach GitHub to check for HA integration updates. "
                "Check your network connection.",
                title="PilotSuite HA Update Check",
                notification_id="pilotsuite_ha_update_check",
            )
            self._ha_version_sensor.update_check_result(None)
            return

        cmp = _compare_versions(local, latest)
        if cmp < 0:
            msg = (
                f"**Update available!**\n\n"
                f"Installed: `{local}`\n"
                f"Latest: `{latest}`\n\n"
                f"Update via HACS or Supervisor."
            )
        elif cmp == 0:
            msg = f"PilotSuite HA integration is up to date (`{local}`)."
        else:
            msg = (
                f"Local version `{local}` is ahead of latest release `{latest}` "
                f"(dev/pre-release build)."
            )

        persistent_notification.async_create(
            self.hass,
            msg,
            title="PilotSuite HA Update Check",
            notification_id="pilotsuite_ha_update_check",
        )
        self._ha_version_sensor.update_check_result(latest)


class CheckCoreUpdateButton(CopilotBaseEntity, ButtonEntity):
    """Check for PilotSuite Core add-on updates."""

    _attr_name = "PilotSuite check Core update"
    _attr_unique_id = "pilotsuite_check_core_update"
    _attr_icon = "mdi:update"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: CopilotDataUpdateCoordinator,
        core_version_sensor: PilotSuiteCoreVersionSensor,
    ) -> None:
        super().__init__(coordinator)
        self._core_version_sensor = core_version_sensor

    async def async_press(self) -> None:
        """Check GitHub for latest Core add-on release."""
        # Try to get local Core version from coordinator or via API.
        local: str | None = None
        if self.coordinator.data:
            local = (
                self.coordinator.data.get("core_version")
                or self.coordinator.data.get("version")
            )
            if local:
                local = str(local)

        # Fallback: fetch from Core API /api/v1/health.
        if not local:
            health = await self._fetch("/api/v1/health", timeout_s=5.0)
            if health and isinstance(health, dict):
                local = str(health.get("version", ""))
            if not local:
                local = "unknown"

        latest = await _fetch_latest_release(self.hass, GITHUB_CORE_RELEASES_URL)

        if latest is None:
            persistent_notification.async_create(
                self.hass,
                "Could not reach GitHub to check for Core add-on updates. "
                "Check your network connection.",
                title="PilotSuite Core Update Check",
                notification_id="pilotsuite_core_update_check",
            )
            self._core_version_sensor.update_check_result(None, local)
            return

        if local == "unknown":
            msg = (
                f"Could not determine local Core version.\n"
                f"Latest release: `{latest}`\n\n"
                f"Make sure Core is running."
            )
        else:
            cmp = _compare_versions(local, latest)
            if cmp < 0:
                msg = (
                    f"**Update available!**\n\n"
                    f"Installed: `{local}`\n"
                    f"Latest: `{latest}`\n\n"
                    f"Update via Supervisor."
                )
            elif cmp == 0:
                msg = f"PilotSuite Core is up to date (`{local}`)."
            else:
                msg = (
                    f"Local Core version `{local}` is ahead of latest release `{latest}` "
                    f"(dev/pre-release build)."
                )

        persistent_notification.async_create(
            self.hass,
            msg,
            title="PilotSuite Core Update Check",
            notification_id="pilotsuite_core_update_check",
        )
        self._core_version_sensor.update_check_result(latest, local)
