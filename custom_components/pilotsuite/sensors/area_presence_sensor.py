"""Area Presence Aggregation Sensor — Multi-Source Pattern (v1.0.0).

Provides `binary_sensor.area_presence_{zone}` with Magic-Areas / Auto-Areas
behaviour:

  Sources (evaluated in priority order):
    1. mmWave / Presence radar  (device_class: presence)
    2. Motion PIR               (device_class: motion)
    3. BLE / device_tracker     (state: home, source_type: bluetooth)
    4. Person zone assignment    (person.home, source: ha)

  Aggregation rule — ANY-ON:
    Zone is occupied if ANY source reports presence.

  Timeout-Reset:
    Each source has an individual timeout. When the last "on" event
    expires, the source drops out. Zone goes OFF only when ALL sources
    have expired (or are absent).

  Hold-Switch:
    Manual override that freezes the reported state regardless of
    sensor input. Remembers the held value for restore.

  Sync contract:
    Tries to sync with Core's /api/v1/zone-automation/dashboard first.
    Falls back to direct HA state evaluation when Core is unreachable.

  Entity naming:  binary_sensor.area_presence_{zone_id}
  Icon:           mdi:motion-sensor  (occupied) / mdi:motion-sensor-off (empty)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from ..const import DOMAIN
from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)

# ── Source Priority ─────────────────────────────────────────────────
# Lower number = higher priority (checked first for hold-restore)
SOURCE_PRIORITY = (
    "mmwave",      # 0 — highest confidence
    "motion",      # 1
    "ble",         # 2
    "person",      # 3 — fallback / passive
)

# Valid hold-switch values
HOLD_STATES = ("auto", "force_on", "force_off")

# Timeout defaults per source type (seconds)
DEFAULT_TIMEOUTS: dict[str, int] = {
    "mmwave": 60,
    "motion": 120,
    "ble": 180,
    "person": 300,
}


# ── Data Structures ─────────────────────────────────────────────────

@dataclass
class PresenceSourceState:
    """Snapshot of a single presence source for one zone."""
    active: bool = False
    last_on: Optional[datetime] = None
    confidence: float = 0.0
    source_name: str = ""


@dataclass
class AggregatedZonePresence:
    """Result of multi-source aggregation for one zone."""
    zone_id: str
    occupied: bool = False
    confidence: float = 0.0
    primary_source: Optional[str] = None
    hold_state: str = "auto"
    held_value: Optional[bool] = None
    sources: dict[str, PresenceSourceState] = field(default_factory=dict)
    last_update: Optional[datetime] = None

    @property
    def is_on(self) -> bool:
        if self.hold_state == "force_on":
            return True
        if self.hold_state == "force_off":
            return False
        return self.occupied


# ── Area Presence Sensor ─────────────────────────────────────────────

class AreaPresenceSensor(CopilotBaseEntity, BinarySensorEntity):
    """Binary sensor: ON when ANY presence source in the zone is active.

    Implements the multi-source aggregation pattern with:
    - ANY-ON rule across mmWave / motion / BLE / person sources
    - Per-source timeout tracking (timeout-reset)
    - Manual hold-switch override (hold-state)
    - HA-native fallback when Core API is unreachable

    Zone entities are auto-discovered from the Habitus zone configuration.
    """

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        zone_id: str,
        zone_name: str,
        mmwave_entities: list[str] | None = None,
        motion_entities: list[str] | None = None,
        ble_entities: list[str] | None = None,
        person_entities: list[str] | None = None,
        timeouts: dict[str, int] | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._attr_name = f"Praesenz {zone_name}"
        self._attr_unique_id = f"area_presence_{zone_id}"

        # Entity lists per source type
        self._mmwave_entities: list[str] = mmwave_entities or []
        self._motion_entities: list[str] = motion_entities or []
        self._ble_entities: list[str] = ble_entities or []
        self._person_entities: list[str] = person_entities or []

        # Timeouts per source type
        self._timeouts: dict[str, int] = {**DEFAULT_TIMEOUTS}
        if timeouts:
            self._timeouts.update(timeouts)

        # Aggregated state
        self._agg = AggregatedZonePresence(zone_id=zone_id)
        self._hold_state: str = "auto"
        self._held_value: Optional[bool] = None
        self._last_core_update: Optional[datetime] = None
        self._last_presence_persist: Optional[datetime] = None
        self._unsub: Optional[Any] = None

        # Throttle: persist presence to Core at most every 30 s
        self._PRESENCE_PERSIST_INTERVAL_S = 30

    # ── Properties ──────────────────────────────────────────────────

    @property
    def is_on(self) -> bool | None:
        return self._agg.is_on

    @property
    def icon(self) -> str:
        if self._hold_state != "auto":
            return "mdi:lock"
        return "mdi:motion-sensor" if self._agg.occupied else "mdi:motion-sensor-off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        source_detail: dict[str, Any] = {}
        for key, src in self._agg.sources.items():
            source_detail[key] = {
                "active": src.active,
                "last_on": src.last_on.isoformat() if src.last_on else None,
                "confidence": src.confidence,
            }

        return {
            "zone_id": self._zone_id,
            "zone_name": self._zone_name,
            "hold_state": self._hold_state,
            "held_value": self._held_value,
            "primary_source": self._agg.primary_source,
            "confidence": self._agg.confidence,
            "sources": source_detail,
            "last_core_sync": (
                self._last_core_update.isoformat()
                if self._last_core_update else None
            ),
            # Config
            "timeouts_s": self._timeouts,
            "mmwave_entities": self._mmwave_entities,
            "motion_entities": self._motion_entities,
            "ble_entities": self._ble_entities,
            "person_entities": self._person_entities,
        }

    # ── Lifecycle ───────────────────────────────────────────────────

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsub = async_dispatcher_connect(
            self.hass,
            f"{DOMAIN}_area_presence_refresh_{self._zone_id}",
            self._on_zone_update_request,
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
        await super().async_will_remove_from_hass()

    # ── Update ──────────────────────────────────────────────────────

    async def async_update(self) -> None:
        # Try Core API sync first
        core_ok = await self._sync_from_core()

        # HA-native fallback — Core unreachable, HA's aggregated state is
        # authoritative. Persist it to Core Neurons so Core stays in sync.
        if not core_ok:
            await self._evaluate_ha_native()
            await self._persist_presence_to_core()

        self.async_write_ha_state()

    async def _sync_from_core(self) -> bool:
        """Fetch presence from Core Zone Automation API.

        Returns True if successful, False if Core is unreachable.
        """
        try:
            data = await self._fetch("/api/v1/zone-automation/dashboard")
            if not data:
                return False

            zones = data.get("zones", [])
            for zone in zones:
                if zone.get("zone_id") == self._zone_id:
                    state = zone.get("state", {})
                    occupied = state.get("occupied", False)
                    confidence = state.get("confidence", 0.0)
                    primary = state.get("primary_source")

                    # Restore hold if coming back online
                    if self._hold_state != "auto":
                        # Keep hold, just note that Core agrees
                        self._agg.occupied = occupied
                        self._agg.confidence = confidence
                        self._agg.primary_source = primary
                    else:
                        self._agg.occupied = occupied
                        self._agg.confidence = confidence
                        self._agg.primary_source = primary

                    self._last_core_update = datetime.now(timezone.utc)

                    # Re-evaluate all HA sources to keep attribute data fresh
                    await self._evaluate_ha_native()
                    return True

            return False

        except Exception as err:
            _LOGGER.debug(
                "Core sync failed for zone %s (%s), falling back to HA native",
                self._zone_id, err,
            )
            return False

    async def _evaluate_ha_native(self) -> None:
        """Direct HA state evaluation — the true any-on rule.

        Scans all relevant entity states and applies:
          1. Per-source active check + timeout tracking
          2. ANY-ON aggregation
          3. Primary-source selection (highest-priority active source)
        """
        now = datetime.now(timezone.utc)
        hass = self.hass

        # Track which sources are currently active
        active_sources: list[tuple[str, float]] = []  # (source_type, confidence)

        # ── 1. mmWave / presence sensors ───────────────────────────
        for entity_id in self._mmwave_entities:
            src = await self._evaluate_source(
                hass, entity_id, "mmwave", now,
                active_states=("on", "home", "detected", "true", "1"),
            )
            if src.active:
                active_sources.append(("mmwave", src.confidence))

        # ── 2. Motion / PIR sensors ─────────────────────────────────
        for entity_id in self._motion_entities:
            src = await self._evaluate_source(
                hass, entity_id, "motion", now,
                active_states=("on", "detected", "motion", "open"),
            )
            if src.active:
                active_sources.append(("motion", src.confidence))

        # ── 3. BLE / device_tracker (bluetooth) ──────────────────────
        for entity_id in self._ble_entities:
            src = await self._evaluate_source_ble(hass, entity_id, "ble", now)
            if src.active:
                active_sources.append(("ble", src.confidence))

        # ── 4. Person zone assignment ────────────────────────────────
        for entity_id in self._person_entities:
            src = await self._evaluate_source_person(hass, entity_id, "person", now)
            if src.active:
                active_sources.append(("person", src.confidence))

        # ── ANY-ON: occupied if any source active ───────────────────
        self._agg.occupied = len(active_sources) > 0

        # Primary source = highest-priority active source
        if active_sources:
            # Sort by priority
            active_sources.sort(
                key=lambda x: SOURCE_PRIORITY.index(x[0])
                if x[0] in SOURCE_PRIORITY else 999
            )
            self._agg.primary_source = active_sources[0][0]
            self._agg.confidence = active_sources[0][1]
        else:
            self._agg.primary_source = None
            self._agg.confidence = 0.0

        self._agg.last_update = now

    async def _evaluate_source(
        self,
        hass: HomeAssistant,
        entity_id: str,
        source_type: str,
        now: datetime,
        active_states: tuple[str, ...],
    ) -> PresenceSourceState:
        """Evaluate a single entity as a presence source."""
        timeout_s = self._timeouts.get(source_type, 120)
        state = hass.states.get(entity_id)

        if state is None or state.state in ("unavailable", "unknown"):
            return PresenceSourceState()

        state_val = str(state.state).lower()
        is_active = state_val in active_states

        # Extract last_changed
        last_on: Optional[datetime] = None
        if hasattr(state, "last_changed") and state.last_changed:
            lc = state.last_changed
            if isinstance(lc, str):
                try:
                    lc = datetime.fromisoformat(lc.replace("Z", "+00:00"))
                except Exception:
                    lc = None
            if lc:
                last_on = lc.astimezone(timezone.utc) if lc.tzinfo is None else lc

        # Confidence from attributes (if available)
        confidence = 0.5
        attrs = dict(state.attributes)
        if "confidence" in attrs:
            confidence = float(attrs["confidence"]) / 100.0
        elif "presence_confidence" in attrs:
            confidence = float(attrs["presence_confidence"]) / 100.0
        elif "target_count" in attrs:
            confidence = min(1.0, 0.5 + int(attrs["target_count"]) * 0.2)
        elif is_active:
            confidence = 1.0

        # Timeout check
        if is_active:
            if last_on:
                elapsed = (now - last_on).total_seconds()
                if elapsed > timeout_s:
                    is_active = False
                    confidence = 0.0

        src_state = PresenceSourceState(
            active=is_active,
            last_on=last_on,
            confidence=confidence,
            source_name=entity_id,
        )
        self._agg.sources[source_type] = src_state
        return src_state

    async def _evaluate_source_ble(
        self,
        hass: HomeAssistant,
        entity_id: str,
        source_type: str,
        now: datetime,
    ) -> PresenceSourceState:
        """Evaluate a device_tracker entity (BLE presence)."""
        timeout_s = self._timeouts.get(source_type, 180)
        state = hass.states.get(entity_id)

        if state is None:
            return PresenceSourceState()

        # Check if BLE-based tracker
        source = getattr(state, "context", None)
        is_ble = False
        if source and hasattr(source, "source_type"):
            is_ble = str(getattr(source, "source_type", "")).lower() == "bluetooth"
        # Also check attributes for source_type
        attrs = dict(state.attributes)
        if not is_ble:
            is_ble = str(attrs.get("source_type", "")).lower() == "bluetooth"

        is_home = str(state.state).lower() == "home"

        if not (is_home and is_ble):
            return PresenceSourceState()

        # Check last_updated as proxy for last seen
        last_on: Optional[datetime] = None
        if hasattr(state, "last_updated") and state.last_updated:
            lu = state.last_updated
            if isinstance(lu, str):
                try:
                    lu = datetime.fromisoformat(lu.replace("Z", "+00:00"))
                except Exception:
                    lu = None
            if lu:
                last_on = lu.astimezone(timezone.utc) if lu.tzinfo is None else lu

        # Timeout check
        active = True
        if last_on:
            elapsed = (now - last_on).total_seconds()
            if elapsed > timeout_s:
                active = False

        return PresenceSourceState(
            active=active,
            last_on=last_on,
            confidence=0.8 if active else 0.0,
            source_name=entity_id,
        )

    async def _evaluate_source_person(
        self,
        hass: HomeAssistant,
        entity_id: str,
        source_type: str,
        now: datetime,
    ) -> PresenceSourceState:
        """Evaluate a person entity as presence source."""
        timeout_s = self._timeouts.get(source_type, 300)
        state = hass.states.get(entity_id)

        if state is None:
            return PresenceSourceState()

        is_home = str(state.state).lower() == "home"
        if not is_home:
            return PresenceSourceState()

        last_on: Optional[datetime] = None
        if hasattr(state, "last_updated") and state.last_updated:
            lu = state.last_updated
            if isinstance(lu, str):
                try:
                    lu = datetime.fromisoformat(lu.replace("Z", "+00:00"))
                except Exception:
                    lu = None
            if lu:
                last_on = lu.astimezone(timezone.utc) if lu.tzinfo is None else lu

        # Timeout check (person is sticky — generous timeout)
        active = True
        if last_on:
            elapsed = (now - last_on).total_seconds()
            if elapsed > timeout_s:
                active = False

        return PresenceSourceState(
            active=active,
            last_on=last_on,
            confidence=0.9 if active else 0.0,
            source_name=entity_id,
        )

    # ── Hold-Switch API ─────────────────────────────────────────────

    async def async_set_hold(self, hold: str) -> bool:
        """Set the hold-switch state.

        Args:
            hold: One of "auto", "force_on", "force_off"

        Returns True if the hold state was changed.
        """
        if hold not in HOLD_STATES:
            _LOGGER.warning(
                "Invalid hold state '%s' for zone %s. Valid: %s",
                hold, self._zone_id, HOLD_STATES,
            )
            return False

        old_hold = self._hold_state
        self._hold_state = hold

        if hold == "auto":
            self._held_value = None
            _LOGGER.info(
                "Zone %s: hold released, reverting to auto (current=%s)",
                self._zone_id, self._agg.occupied,
            )
        elif hold == "force_on":
            self._held_value = True
            _LOGGER.info("Zone %s: hold → FORCE ON", self._zone_id)
        else:  # force_off
            self._held_value = False
            _LOGGER.info("Zone %s: hold → FORCE OFF", self._zone_id)

        # Persist to Core if available
        await self._persist_hold_to_core(hold)
        self.async_write_ha_state()
        return True

    async def _persist_hold_to_core(self, hold: str) -> None:
        """Send hold state change to Core API."""
        if not self.coordinator or not hasattr(self.coordinator, "api"):
            return
        try:
            await self.coordinator.api.async_set_zone_presence_hold(
                self._zone_id, hold
            )
        except Exception as err:
            _LOGGER.debug(
                "Could not persist hold state to Core for zone %s: %s",
                self._zone_id, err,
            )

    async def _persist_presence_to_core(self) -> None:
        """Send aggregated presence state to Core Neurons API (throttled, ≤30 s)."""
        if not self.coordinator or not hasattr(self.coordinator, "api"):
            return

        now = datetime.now(timezone.utc)
        if self._last_presence_persist:
            elapsed = (now - self._last_presence_persist).total_seconds()
            if elapsed < self._PRESENCE_PERSIST_INTERVAL_S:
                return

        try:
            await self.coordinator.api.async_set_zone_presence_state(
                zone_id=self._zone_id,
                occupied=self._agg.occupied,
                primary_source=self._agg.primary_source,
                confidence=self._agg.confidence,
                hold_state=self._hold_state,
            )
            self._last_presence_persist = now
        except Exception as err:
            _LOGGER.debug(
                "Could not persist presence to Core for zone %s: %s",
                self._zone_id, err,
            )

    # ── Internal Events ─────────────────────────────────────────────

    def _on_zone_update_request(self) -> None:
        """Handle a manual refresh request via dispatcher."""
        self.hass.async_create_task(self.async_update())
