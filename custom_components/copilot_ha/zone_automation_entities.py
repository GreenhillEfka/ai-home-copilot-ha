"""PilotSuite — Per-Zone Automation Control Entities.

Creates HA number (slider), switch, and select entities so users can
directly control zone automation settings from any Lovelace dashboard.

Values are read from coordinator data (zone automation dashboard) and
written via Core REST API calls.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.components.select import SelectEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback

from .entity import CopilotBaseEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

AUTOMATION_MODES = ["off", "learning", "autonomy"]
AUTOMATION_MODE_LABELS = {
    "off": "Aus",
    "learning": "Lernend",
    "autonomy": "Autonomie",
}


def _get_zone_data(coordinator, zone_id: str) -> dict[str, Any]:
    """Extract zone data from coordinator's last zone_automation poll.

    Handles 'zone:' prefix mismatch: HA entities use 'zone:wohnbereich'
    while Core returns 'wohnbereich'.
    """
    data = coordinator.data or {}
    clean_id = zone_id.removeprefix("zone:")
    za = data.get("zone_automation", {})
    zones_list = za.get("zones", [])
    if not zones_list and za:
        _LOGGER.debug(
            "zone_automation has keys %s but no zones for %s",
            list(za.keys()), clean_id,
        )
    for zone in zones_list:
        core_id = zone.get("zone_id", "")
        if core_id == zone_id or core_id == clean_id:
            return zone
    if zones_list:
        available_ids = [z.get("zone_id", "?") for z in zones_list]
        _LOGGER.warning(
            "Zone %r (clean: %r) not found in %d zones: %s",
            zone_id, clean_id, len(zones_list), available_ids,
        )
    return {}


# ── Zone Automation Mode Select ─────────────────────────────────────


class ZoneAutomationModeSelect(CopilotBaseEntity, SelectEntity):
    """Select for overall zone automation mode (off/learning/autonomy)."""

    _attr_has_entity_name = False
    _attr_options = AUTOMATION_MODES
    _attr_icon = "mdi:robot"

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._attr_unique_id = f"copilot_ha_zone_{zone_id}_automation_mode"
        self._attr_name = f"PilotSuite {zone_name} Automationsmodus"
        self._attr_current_option = "off"

    @callback
    def _handle_coordinator_update(self) -> None:
        zd = _get_zone_data(self.coordinator, self._zone_id)
        mode = zd.get("config", {}).get("automation_mode", "off")
        if mode in AUTOMATION_MODES:
            self._attr_current_option = mode
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    async def async_select_option(self, option: str) -> None:
        if option not in AUTOMATION_MODES:
            return
        await self.coordinator.async_set_zone_automation_mode(self._zone_id, option)
        self._attr_current_option = option
        self.async_write_ha_state()


# ── Zone Light/Music Switches ───────────────────────────────────────


class _ZoneAutoSwitch(CopilotBaseEntity, SwitchEntity):
    """Base for zone automation toggle switches."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator,
        zone_id: str,
        zone_name: str,
        *,
        target: str,
        key: str,
        name_suffix: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._target = target
        self._config_key = key
        self._attr_unique_id = f"copilot_ha_zone_{zone_id}_{target}_{key}"
        self._attr_name = f"PilotSuite {zone_name} {name_suffix}"
        self._attr_icon = icon
        self._attr_is_on = False

    @callback
    def _handle_coordinator_update(self) -> None:
        zd = _get_zone_data(self.coordinator, self._zone_id)
        config = zd.get("config", {}).get(self._target, {})
        self._attr_is_on = bool(config.get(self._config_key, False))
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_zone_config(
            self._zone_id, {self._target: {self._config_key: True}}
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_zone_config(
            self._zone_id, {self._target: {self._config_key: False}}
        )
        self._attr_is_on = False
        self.async_write_ha_state()


class ZoneLightAutoSwitch(_ZoneAutoSwitch):
    """Toggle: automatic light control for a zone."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="light", key="enabled",
            name_suffix="Licht Automatik",
            icon="mdi:lightbulb-auto",
        )


class ZoneMusicAutoSwitch(_ZoneAutoSwitch):
    """Toggle: automatic music control for a zone."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="music", key="enabled",
            name_suffix="Musik Automatik",
            icon="mdi:music-circle",
        )


class ZoneMusicFollowSwitch(_ZoneAutoSwitch):
    """Toggle: music follows user between zones."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="music", key="follow_mode",
            name_suffix="Musik Follow",
            icon="mdi:walk",
        )


# ── Zone Number Sliders ─────────────────────────────────────────────


class _ZoneConfigNumber(CopilotBaseEntity, NumberEntity):
    """Base for zone automation config number sliders."""

    _attr_has_entity_name = False
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator,
        zone_id: str,
        zone_name: str,
        *,
        target: str,
        key: str,
        name_suffix: str,
        icon: str,
        min_value: float,
        max_value: float,
        step: float = 1.0,
        unit: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._target = target
        self._config_key = key
        self._attr_unique_id = f"copilot_ha_zone_{zone_id}_{target}_{key}"
        self._attr_name = f"PilotSuite {zone_name} {name_suffix}"
        self._attr_icon = icon
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        if unit:
            self._attr_native_unit_of_measurement = unit

    @callback
    def _handle_coordinator_update(self) -> None:
        zd = _get_zone_data(self.coordinator, self._zone_id)
        config = zd.get("config", {}).get(self._target, {})
        val = config.get(self._config_key)
        if val is not None:
            try:
                self._attr_native_value = float(val)
            except (TypeError, ValueError):
                pass
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_zone_config(
            self._zone_id, {self._target: {self._config_key: value}}
        )
        self._attr_native_value = value
        self.async_write_ha_state()


class ZoneBrightnessTargetNumber(_ZoneConfigNumber):
    """Slider: target brightness level for a zone (0-100%)."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="light", key="brightness_target_pct",
            name_suffix="Ziel-Helligkeit",
            icon="mdi:brightness-7",
            min_value=0, max_value=100, step=5, unit="%",
        )


class ZonePresenceDelayNumber(_ZoneConfigNumber):
    """Slider: seconds of presence before lights turn on (0-120s)."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="light", key="presence_delay_s",
            name_suffix="Einschaltverzögerung",
            icon="mdi:timer-outline",
            min_value=0, max_value=120, step=5, unit="s",
        )


class ZoneAbsenceDelayNumber(_ZoneConfigNumber):
    """Slider: seconds after last presence before lights off (0-600s)."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="light", key="absence_delay_s",
            name_suffix="Abschaltverzögerung",
            icon="mdi:timer-off-outline",
            min_value=0, max_value=600, step=10, unit="s",
        )


class ZoneMusicVolumeNumber(_ZoneConfigNumber):
    """Slider: default music volume for a zone (0-100%)."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="music", key="default_volume_pct",
            name_suffix="Musiklautstärke",
            icon="mdi:volume-medium",
            min_value=0, max_value=100, step=5, unit="%",
        )


class ZoneBrightnessMinNumber(_ZoneConfigNumber):
    """Slider: minimum brightness when on (0-100%)."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="light", key="brightness_min_pct",
            name_suffix="Min. Helligkeit",
            icon="mdi:brightness-4",
            min_value=0, max_value=100, step=5, unit="%",
        )


class ZoneDampeningBandNumber(_ZoneConfigNumber):
    """Slider: hysteresis dead-band to prevent flicker (0-50%)."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="light", key="dampening_band_pct",
            name_suffix="Dämpfungsband",
            icon="mdi:sine-wave",
            min_value=0, max_value=50, step=5, unit="%",
        )


class ZoneLuxIndoorTargetNumber(_ZoneConfigNumber):
    """Slider: target indoor illuminance (0-2000 lx)."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="light", key="lux_indoor_target",
            name_suffix="Soll-Lux Innen",
            icon="mdi:brightness-5",
            min_value=0, max_value=2000, step=50, unit="lx",
        )


class ZoneColorTempNumber(_ZoneConfigNumber):
    """Slider: color temperature (2200-6500 K)."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="light", key="color_temp_k",
            name_suffix="Farbtemperatur",
            icon="mdi:thermometer-lines",
            min_value=2200, max_value=6500, step=100, unit="K",
        )


class ZoneMusicPresenceDelayNumber(_ZoneConfigNumber):
    """Slider: seconds of presence before music starts (0-120s)."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="music", key="presence_delay_s",
            name_suffix="Musik Einschaltverzögerung",
            icon="mdi:timer-music-outline",
            min_value=0, max_value=120, step=5, unit="s",
        )


class ZoneMusicAbsencePauseNumber(_ZoneConfigNumber):
    """Slider: seconds after absence before music pauses (0-600s)."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="music", key="absence_pause_s",
            name_suffix="Musik Pausenverzögerung",
            icon="mdi:timer-music",
            min_value=0, max_value=600, step=10, unit="s",
        )


class ZoneMusicFadeDurationNumber(_ZoneConfigNumber):
    """Slider: cross-fade duration between zones (0-30s)."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="music", key="fade_duration_s",
            name_suffix="Überblendung",
            icon="mdi:swap-horizontal",
            min_value=0, max_value=30, step=1, unit="s",
        )


class ZoneLuxOutdoorCompensationSwitch(_ZoneAutoSwitch):
    """Toggle: outdoor lux compensation for indoor brightness."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="light", key="lux_outdoor_compensation",
            name_suffix="Außenlicht-Kompensation",
            icon="mdi:weather-sunny",
        )


class ZoneColorTempAutoSwitch(_ZoneAutoSwitch):
    """Toggle: circadian color temperature adjustment."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="light", key="color_temp_auto",
            name_suffix="Farbtemperatur Auto",
            icon="mdi:theme-light-dark",
        )


class ZoneMusicAutoPlaySwitch(_ZoneAutoSwitch):
    """Toggle: auto-play music on zone entry."""

    def __init__(self, coordinator, zone_id: str, zone_name: str) -> None:
        super().__init__(
            coordinator, zone_id, zone_name,
            target="music", key="presence_auto_play",
            name_suffix="Musik Auto-Play",
            icon="mdi:music-note-plus",
        )


# ── Factory Function ────────────────────────────────────────────────


def create_zone_automation_entities(coordinator, zones: list[dict]) -> dict[str, list]:
    """Create all per-zone automation control entities.

    Returns a dict with keys "number", "select", "switch" mapping to
    lists of entity instances for the corresponding HA platforms.
    """
    numbers: list[NumberEntity] = []
    selects: list[SelectEntity] = []
    switches: list[SwitchEntity] = []

    for zone in zones:
        zone_id = zone.get("zone_id", "")
        zone_name = zone.get("name", zone_id)
        if not zone_id:
            continue
        # Strip 'zone:' prefix for Core API compatibility
        zone_id = zone_id.removeprefix("zone:")

        # Automation mode select
        selects.append(ZoneAutomationModeSelect(coordinator, zone_id, zone_name))

        # Light automation controls
        switches.append(ZoneLightAutoSwitch(coordinator, zone_id, zone_name))
        numbers.append(ZoneBrightnessTargetNumber(coordinator, zone_id, zone_name))
        numbers.append(ZoneBrightnessMinNumber(coordinator, zone_id, zone_name))
        numbers.append(ZonePresenceDelayNumber(coordinator, zone_id, zone_name))
        numbers.append(ZoneAbsenceDelayNumber(coordinator, zone_id, zone_name))
        numbers.append(ZoneDampeningBandNumber(coordinator, zone_id, zone_name))
        numbers.append(ZoneLuxIndoorTargetNumber(coordinator, zone_id, zone_name))
        numbers.append(ZoneColorTempNumber(coordinator, zone_id, zone_name))
        switches.append(ZoneLuxOutdoorCompensationSwitch(coordinator, zone_id, zone_name))
        switches.append(ZoneColorTempAutoSwitch(coordinator, zone_id, zone_name))

        # Music automation controls
        switches.append(ZoneMusicAutoSwitch(coordinator, zone_id, zone_name))
        switches.append(ZoneMusicFollowSwitch(coordinator, zone_id, zone_name))
        switches.append(ZoneMusicAutoPlaySwitch(coordinator, zone_id, zone_name))
        numbers.append(ZoneMusicVolumeNumber(coordinator, zone_id, zone_name))
        numbers.append(ZoneMusicPresenceDelayNumber(coordinator, zone_id, zone_name))
        numbers.append(ZoneMusicAbsencePauseNumber(coordinator, zone_id, zone_name))
        numbers.append(ZoneMusicFadeDurationNumber(coordinator, zone_id, zone_name))

    return {"number": numbers, "select": selects, "switch": switches}
