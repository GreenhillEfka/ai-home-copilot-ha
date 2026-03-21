"""Habitus Zones v2 Entities für Home Assistant.

Provides HA entities (sensors, buttons, selects) for managing and visualising
Habitus Zones v2, plus the ``sort_entity_to_zone()`` function used by
zone_auto_setup.py to route individual HA entities into the correct
Habitus Zone using keyword matching + confidence scoring.
"""
from __future__ import annotations

import json
import logging
import re
import unicodedata
from typing import Any

import yaml
from homeassistant.components.button import ButtonEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.text import TextEntity
from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import CONF_HOST, CONF_PORT, DEFAULT_HOST, DEFAULT_PORT, DOMAIN
from .entity import CopilotBaseEntity
from .habitus_zones_store_v2 import (
    HabitusZoneV2,
    SIGNAL_HABITUS_ZONES_V2_UPDATED,
    SIGNAL_HABITUS_ZONE_STATE_CHANGED,
    async_get_zones_v2,
    async_set_zones_v2_from_raw,
    async_set_zone_state,
    async_persist_all_zone_states,
)

_LOGGER = logging.getLogger(__name__)

# ── sort_entity_to_zone() keyword tables ─────────────────────────────

# Maps normalized keyword → zone_id for entity-level routing.
# Derived from HABITUS_ZONE_TEMPLATES in zone_auto_setup.py but usable
# without importing that module (avoids circular imports).
_ENTITY_ZONE_KEYWORDS: dict[str, list[str]] = {
    "zone:wohnbereich": [
        "wohn", "wohnzimmer", "esszimmer", "ess", "gast",
        "living", "dining", "lounge", "loft", "entspannung",
    ],
    "zone:badbereich": [
        "bad", "badezimmer", "toilette", "wc", "dusche",
        "bath", "bathroom", "shower",
    ],
    "zone:kochbereich": [
        "koch", "küche", "kueche", "speis", "vorrat",
        "kitchen", "pantry",
    ],
    "zone:buerobereich": [
        "büro", "buero", "arbeit", "homeoffice", "office",
        "studio", "werkstatt",
    ],
    "zone:gangbereich": [
        "gang", "flur", "diele", "eingang", "korridor",
        "hall", "corridor", "entry", "vorraum", "vorzimmer",
    ],
    "zone:schlafbereich": [
        "schlaf", "schlafzimmer", "bedroom",
    ],
    "zone:zimmer_mira": [
        "mira", "zimmer mira", "miras zimmer", "kinderzimmer mira",
    ],
    "zone:zimmer_paul": [
        "paul", "zimmer paul", "zimmer pauli", "pauls zimmer",
        "kinderzimmer paul",
    ],
    "zone:aussenbereich": [
        "aussen", "außen", "garten", "garage", "carport",
        "outdoor", "garden", "hof", "parkplatz", "terrasse",
        "terrass", "balkon", "loggia", "veranda", "patio",
        "wintergarten",
    ],
    # Named child zones — entities with exact room names route here
    "zone:kinderzimmer": [
        "kinderzimmer",
    ],
    "zone:kellerbereich": [
        "keller",
    ],
    "zone:terrassenbereich": [
        "terrasse", "terrass", "balkon",
    ],
}

# Zones that are considered "certain" vs. "uncertain" for confidence tiers.
# High-confidence zones: strong keyword signal, unambiguous mapping.
_HIGH_CONFIDENCE_ZONES = frozenset({
    "zone:wohnbereich", "zone:badbereich", "zone:kochbereich",
    "zone:schlafbereich", "zone:buerobereich",
    "zone:gangbereich", "zone:aussenbereich",
    "zone:zimmer_mira", "zone:zimmer_paul",
})

# Virtual area patterns — entities from these areas are always "ungeordnet".
_VIRTUAL_AREA_PATTERNS = re.compile(
    r"^(energie|energy|netzwerk|network|kontrollraum|kalender|calendar|"
    r"kosten|cost|personen|person|serverraum|umwelt|environment|"
    r"medienkontrolle|free ?devices|haupthaus|pv.?anlage|move|viture|"
    r"fire ?tv|airplay|ai.?factory)$",
    re.IGNORECASE,
)

# Domain → preferred role (used for bonus scoring).
_DOMAIN_ROLE_BONUS: dict[str, str] = {
    "light": "lights",
    "climate": "heating",
    "cover": "cover",
    "lock": "lock",
    "media_player": "media",
    "fan": "heating",
    "humidifier": "humidity",
    "vacuum": "other",
    "camera": "other",
}


def _normalize(text: str) -> str:
    """Normalize text for keyword matching: lowercase, strip accents/diacritics."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return nfkd.encode("ascii", "ignore").decode("ascii").strip()


def _levenshtein(s1: str, s2: str) -> int:
    """Compute Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            curr_row.append(min(
                prev_row[j + 1] + 1,
                curr_row[j] + 1,
                prev_row[j] + (0 if c1 == c2 else 1),
            ))
        prev_row = curr_row
    return prev_row[-1]


def sort_entity_to_zone(
    entity_id: str,
    state: State | None = None,
    area_id: str | None = None,
    area_name: str | None = None,
) -> tuple[str, float, dict[str, Any]]:
    """Sort a single HA entity into a Habitus Zone using keyword matching + confidence.

    Examines ``entity_id``, ``state`` (optional), ``area_id`` (optional), and
    ``area_name`` (optional) to find the best matching zone.  Returns a
    three-tuple::

        (zone_id, confidence, extra)

    Where:
    - ``zone_id`` is one of the defined zone IDs (e.g. ``zone:wohnbereich``)
      or ``zone:ungeordnet`` if no confident match was found.
    - ``confidence`` is a float in 0.0–1.0 indicating match certainty.
    - ``extra`` is a dict with diagnostic details::

          {
            "matched_keyword": "...",    # keyword that triggered the match
            "match_type": "exact|substring|fuzzy|area|area_exact",
            "domain_hint": "...",         # domain that contributed a bonus
            "is_virtual_area": bool,
            "zone_name_de": "...",        # human-readable zone name
          }

    Confidence thresholds (internal):
    - ≥ 0.80 → high confidence → zone accepted as-is
    - 0.60–0.79 → medium confidence → zone accepted
    - < 0.60 → below threshold → routed to ``zone:ungeordnet``

    Match priority (first wins):
    1. Exact area name + area keywords  (confidence 0.95, area_exact)
    2. Exact entity_id keyword match   (confidence 0.90, exact)
    3. Substring keyword match         (confidence 0.75–0.85, substring)
    4. Fuzzy (Levenshtein ≤ 1) match   (confidence 0.65, fuzzy)
    5. Domain bonus: entity domain aligns with zone (0.05 bonus)

    Args:
        entity_id:  Home Assistant entity ID, e.g. ``light.wohnzimmer_decke``.
        state:      Optional State object; attributes (``friendly_name``,
                    ``device_class``) are used for matching.
        area_id:    Optional HA area ID the entity belongs to.
        area_name:  Optional human-readable area name.

    Returns:
        Tuple of (zone_id, confidence, extra dict).

    Example:
        >>> zone, conf, extra = sort_entity_to_zone(
        ...     "light.wohnzimmer_decke",
        ...     area_name="Wohnzimmer",
        ... )
        >>> zone
        'zone:wohnbereich'
        >>> conf
        0.95
    """
    extra: dict[str, Any] = {
        "matched_keyword": None,
        "match_type": None,
        "domain_hint": None,
        "is_virtual_area": False,
        "zone_name_de": None,
    }

    # ── 0. Virtual area guard ────────────────────────────────────────
    if area_name:
        area_norm = _normalize(area_name)
        if _VIRTUAL_AREA_PATTERNS.match(area_norm):
            extra["is_virtual_area"] = True
            return "zone:ungeordnet", 0.0, extra

    # ── Build match candidates ───────────────────────────────────────
    # Collect text fields to search (entity_id is always searched).
    entity_lower = entity_id.lower()
    friendly_name = ""
    device_class = ""

    if state is not None:
        friendly_name = _normalize(
            state.attributes.get("friendly_name", "")
        )
        device_class = str(state.attributes.get("device_class", "")).lower()

    # All text fields concatenated for substring search
    search_texts: list[tuple[str, str]] = [
        (_normalize(entity_id), "entity_id"),
    ]
    if friendly_name:
        search_texts.append((friendly_name, "friendly_name"))
    if area_name:
        search_texts.append((_normalize(area_name), "area_name"))

    # ── 1. Area-exact match (highest priority) ──────────────────────
    if area_name:
        area_norm = _normalize(area_name)
        for zone_id, keywords in _ENTITY_ZONE_KEYWORDS.items():
            for kw in keywords:
                kw_norm = _normalize(kw)
                if kw_norm == area_norm:
                    extra["matched_keyword"] = kw
                    extra["match_type"] = "area_exact"
                    extra["zone_name_de"] = _ZONE_ID_TO_NAME.get(zone_id, zone_id)
                    # Exact area keyword match: very high confidence
                    conf = 0.95
                    conf += _domain_bonus(entity_lower)
                    return zone_id, min(conf, 1.0), extra

    # ── 2. Exact keyword match in entity_id / friendly_name ──────────
    for search_text, source in search_texts:
        if not search_text:
            continue
        for zone_id, keywords in _ENTITY_ZONE_KEYWORDS.items():
            for kw in keywords:
                kw_norm = _normalize(kw)
                if kw_norm and kw_norm == search_text:
                    extra["matched_keyword"] = kw
                    extra["match_type"] = "exact"
                    extra["zone_name_de"] = _ZONE_ID_TO_NAME.get(zone_id, zone_id)
                    conf = 0.90
                    conf += _domain_bonus(entity_lower)
                    return zone_id, min(conf, 1.0), extra

    # ── 3. Substring keyword match ───────────────────────────────────
    best_sub: tuple[str, str, float] = ("", "", 0.0)  # (zone_id, keyword, conf)
    for search_text, source in search_texts:
        if not search_text:
            continue
        for zone_id, keywords in _ENTITY_ZONE_KEYWORDS.items():
            for kw in keywords:
                kw_norm = _normalize(kw)
                if not kw_norm:
                    continue
                # keyword is substring of search_text
                if kw_norm in search_text:
                    # length ratio bonus: longer keyword = more specific
                    length_ratio = len(kw_norm) / max(len(search_text), 1)
                    conf = 0.75 + min(length_ratio, 0.10)
                # search_text is substring of keyword
                elif search_text in kw_norm and len(search_text) >= 4:
                    conf = 0.80
                else:
                    continue

                if conf > best_sub[2]:
                    best_sub = (zone_id, kw, conf)

    if best_sub[2] >= 0.75:
        extra["matched_keyword"] = best_sub[1]
        extra["match_type"] = "substring"
        extra["zone_name_de"] = _ZONE_ID_TO_NAME.get(best_sub[0], best_sub[0])
        conf = best_sub[2] + _domain_bonus(entity_lower)
        return best_sub[0], min(conf, 1.0), extra

    # ── 4. Fuzzy (Levenshtein ≤ 1) match for keywords ≥ 4 chars ─────
    best_fuzzy: tuple[str, str, float] = ("", "", 0.0)
    for search_text, source in search_texts:
        if not search_text or len(search_text) < 3:
            continue
        for zone_id, keywords in _ENTITY_ZONE_KEYWORDS.items():
            for kw in keywords:
                kw_norm = _normalize(kw)
                if len(kw_norm) < 4:
                    continue
                dist = _levenshtein(kw_norm, search_text)
                if dist <= 1:
                    conf = 0.65
                    if conf > best_fuzzy[2]:
                        best_fuzzy = (zone_id, kw, conf)

    if best_fuzzy[2] >= 0.65:
        extra["matched_keyword"] = best_fuzzy[1]
        extra["match_type"] = "fuzzy"
        extra["zone_name_de"] = _ZONE_ID_TO_NAME.get(best_fuzzy[0], best_fuzzy[0])
        conf = best_fuzzy[2] + _domain_bonus(entity_lower)
        return best_fuzzy[0], min(conf, 1.0), extra

    # ── 5. No match → zone:ungeordnet ───────────────────────────────
    extra["match_type"] = "none"
    extra["zone_name_de"] = "Ungeordnet"
    return "zone:ungeordnet", 0.0, extra


def _domain_bonus(entity_id: str) -> float:
    """Return a small confidence bonus if entity domain matches a known zone keyword."""
    domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
    role = _DOMAIN_ROLE_BONUS.get(domain)
    if role:
        return 0.05
    return 0.0


# Human-readable names for zone IDs (used in extra dict)
_ZONE_ID_TO_NAME: dict[str, str] = {
    "zone:wohnbereich": "Wohnbereich",
    "zone:badbereich": "Badbereich",
    "zone:kochbereich": "Kochbereich",
    "zone:buerobereich": "Bürobereich",
    "zone:gangbereich": "Gangbereich",
    "zone:schlafbereich": "Schlafbereich",
    "zone:zimmer_mira": "Zimmer Mira",
    "zone:zimmer_paul": "Zimmer Paul",
    "zone:aussenbereich": "Außenbereich",
    "zone:kinderzimmer": "Kinderzimmer",
    "zone:kellerbereich": "Kellerbereich",
    "zone:terrassenbereich": "Terrassenbereich",
    "zone:ungeordnet": "Ungeordnet",
}


# ── HA Entity classes (HabitusZonesV2JsonText, sensors, buttons…) ──

class HabitusZonesV2JsonText(CopilotBaseEntity, TextEntity):
    """Bulk editor for Zones v2 - YAML/JSON."""

    _attr_entity_registry_enabled_default = False
    _attr_has_entity_name = False
    _attr_name = "PilotSuite habitus zones v2 (bulk editor)"
    _attr_unique_id = "copilot_ha_habitus_zones_v2_json"
    _attr_icon = "mdi:layers-outline"
    _attr_mode = "text"  # multiline
    _attr_native_max = 65535

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._value: str = "[]"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await self._reload_value()

    async def _reload_value(self) -> None:
        zones = await async_get_zones_v2(self.hass, self._entry.entry_id)
        raw = []
        for z in zones:
            item: dict[str, Any] = {
                "id": z.zone_id,
                "name": z.name,
                "zone_type": z.zone_type,
                "entity_ids": list(z.entity_ids),
            }
            if isinstance(z.entities, dict) and z.entities:
                item["entities"] = {k: list(v) for k, v in z.entities.items()}
            if z.parent_zone_id:
                item["parent"] = z.parent_zone_id
            if z.child_zone_ids:
                item["child_zones"] = list(z.child_zone_ids)
            if z.floor:
                item["floor"] = z.floor
            if z.current_state != "idle":
                item["current_state"] = z.current_state
            if z.priority:
                item["priority"] = z.priority
            if z.tags:
                item["tags"] = list(z.tags)
            if z.metadata:
                item["metadata"] = z.metadata
            raw.append(item)

        self._value = yaml.safe_dump(raw, allow_unicode=True, sort_keys=False)
        self.async_write_ha_state()

    @property
    def native_value(self) -> str | None:
        return self._value

    async def async_set_value(self, value: str) -> None:
        value = (value or "").strip()
        if not value:
            value = "[]"

        try:
            try:
                raw = json.loads(value)
            except Exception:
                raw = yaml.safe_load(value)

            zones = await async_set_zones_v2_from_raw(
                self.hass, self._entry.entry_id, raw
            )
        except Exception as err:
            persistent_notification.async_create(
                self.hass,
                f"Invalid Habitus zones v2 YAML/JSON: {err}",
                title="PilotSuite Habitus zones v2",
                notification_id="copilot_ha_habitus_zones_v2",
            )
            return

        persistent_notification.async_create(
            self.hass,
            f"Saved {len(zones)} Habitus zones v2.",
            title="PilotSuite Habitus zones v2",
            notification_id="copilot_ha_habitus_zones_v2",
        )
        await self._reload_value()


class HabitusZonesV2CountSensor(CopilotBaseEntity, SensorEntity):
    """Count of configured zones v2."""

    _attr_has_entity_name = False
    _attr_name = "PilotSuite habitus zones count"
    _attr_unique_id = "copilot_ha_habitus_zones_count"
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._count: int = 0
        self._unsub: Any = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsub = async_dispatcher_connect(
            self.hass, SIGNAL_HABITUS_ZONES_V2_UPDATED, self._on_update
        )
        await self._refresh()

    async def async_will_remove_from_hass(self) -> None:
        if callable(self._unsub):
            self._unsub()
        self._unsub = None
        await super().async_will_remove_from_hass()

    async def _refresh(self) -> None:
        zones = await async_get_zones_v2(self.hass, self._entry.entry_id)
        self._count = len(zones)
        self.async_write_ha_state()

    def _on_update(self, entry_id: str) -> None:
        if entry_id != self._entry.entry_id:
            return
        self.hass.loop.call_soon_threadsafe(
            lambda: self.hass.async_create_task(self._refresh())
        )

    @property
    def native_value(self) -> int | None:
        return self._count


class HabitusZonesSensor(CopilotBaseEntity, SensorEntity):
    """Main habitus zones sensor for Lovelace ha-copilot-habitus-card."""

    _attr_has_entity_name = False
    _attr_name = "PilotSuite Habitus Zones"
    _attr_unique_id = "copilot_ha_habitus_zones"
    _attr_icon = "mdi:layers-outline"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._unsub: Any = None
        self._unsub_state: Any = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsub = async_dispatcher_connect(
            self.hass, SIGNAL_HABITUS_ZONES_V2_UPDATED, self._on_update
        )
        self._unsub_state = async_dispatcher_connect(
            self.hass, SIGNAL_HABITUS_ZONE_STATE_CHANGED, self._on_state_change
        )
        await self._refresh()

    async def async_will_remove_from_hass(self) -> None:
        if callable(self._unsub):
            self._unsub()
        if callable(self._unsub_state):
            self._unsub_state()
        self._unsub = None
        self._unsub_state = None
        await super().async_will_remove_from_hass()

    async def _refresh(self) -> None:
        zones = await async_get_zones_v2(self.hass, self._entry.entry_id)
        active_zones = [z for z in zones if z.current_state == "active"]

        zone_list = []
        for z in zones:
            zone_entry: dict[str, Any] = {
                "id": z.zone_id,
                "name": z.name,
                "active": z.current_state == "active",
                "type": z.zone_type,
                "entity_count": len(z.entity_ids),
                "description": f"{z.zone_type.capitalize()} — {len(z.entity_ids)} entities",
            }
            if z.floor:
                zone_entry["floor"] = z.floor
            if z.priority:
                zone_entry["priority"] = z.priority
            if z.tags:
                zone_entry["tags"] = list(z.tags)
            zone_entry["settings"] = {
                "ambience": (z.metadata or {}).get("ambience", "Normal"),
                "activity": (
                    z.metadata or {}
                ).get("activity", "Idle" if z.current_state == "idle" else "Active"),
                "optimization": (z.metadata or {}).get("optimization", "Balanced"),
            }
            if z.metadata and z.metadata.get("mood"):
                zone_entry["mood"] = z.metadata["mood"]
            zone_list.append(zone_entry)

        entry_data = self._entry.data if self._entry else {}
        core_host = entry_data.get(CONF_HOST, DEFAULT_HOST)
        core_port = entry_data.get(CONF_PORT, DEFAULT_PORT)
        core_base = f"http://{core_host}:{core_port}"

        # Extract zone_modules from zone_automation for styx-zone-card module display
        zone_auto = self.coordinator.data.get("zone_automation", {}) if self.coordinator else {}
        zones_auto_list = zone_auto.get("zones", [])
        zone_modules: dict[str, dict[str, Any]] = {}
        for zdata in zones_auto_list:
            zid = zdata.get("zone_id", "")
            config = zdata.get("config", {})
            mode = config.get("automation_mode", "off")
            mod_configs: dict[str, Any] = {}
            for mk in ("light", "music", "climate", "cover", "security"):
                if mk in config and isinstance(config[mk], dict):
                    mod_configs[mk] = config[mk]
            if mod_configs or mode != "off":
                zone_modules[zid] = {"automation_mode": mode, "modules": mod_configs}

        self._attr_native_value = f"{len(active_zones)}/{len(zones)} active"
        self._attr_extra_state_attributes = {
            "zones": zone_list,
            "behaviors": [],
            "zones_total": len(zones),
            "zones_active": len(active_zones),
            "core_base": core_base,
            "zone_modules": zone_modules,
        }
        self.async_write_ha_state()

    def _on_update(self, entry_id: str) -> None:
        if entry_id != self._entry.entry_id:
            return
        self.hass.loop.call_soon_threadsafe(
            lambda: self.hass.async_create_task(self._refresh())
        )

    def _on_state_change(self, data: dict) -> None:
        if data.get("entry_id") != self._entry.entry_id:
            return
        self.hass.loop.call_soon_threadsafe(
            lambda: self.hass.async_create_task(self._refresh())
        )


class HabitusZonesV2ValidateButton(CopilotBaseEntity, ButtonEntity):
    """Validate zones v2 configuration."""

    _attr_has_entity_name = False
    _attr_name = "PilotSuite validate habitus zones v2"
    _attr_unique_id = "copilot_ha_validate_habitus_zones_v2"
    _attr_icon = "mdi:check-decagram"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry

    async def async_press(self) -> None:
        zones = await async_get_zones_v2(self.hass, self._entry.entry_id)

        missing: list[str] = []
        total = 0
        zones_missing_motion: list[str] = []
        zones_missing_light: list[str] = []

        def domain(eid: str) -> str:
            return eid.split(".", 1)[0] if "." in eid else ""

        def is_light(eid: str) -> bool:
            return domain(eid) == "light"

        def is_motion_or_presence(eid: str) -> bool:
            dom = domain(eid)
            if dom not in ("binary_sensor", "sensor"):
                return False
            st = self.hass.states.get(eid)
            device_class = st.attributes.get("device_class") if st else None
            if device_class in ("motion", "presence", "occupancy"):
                return True
            eid_l = eid.lower()
            return any(k in eid_l for k in ("motion", "presence", "occupancy"))

        for z in zones:
            has_motion = False
            has_light = False
            for eid in z.entity_ids:
                total += 1
                st = self.hass.states.get(eid)
                if st is None:
                    missing.append(f"{z.zone_id}: {eid}")
                    continue
                has_light = has_light or is_light(eid)
                has_motion = has_motion or is_motion_or_presence(eid)

            if not has_motion:
                zones_missing_motion.append(z.zone_id)
            if not has_light:
                zones_missing_light.append(z.zone_id)

        msg = [f"Zones v2: {len(zones)}", f"Entities referenced: {total}"]

        if zones_missing_motion or zones_missing_light:
            msg.append("")
            msg.append("Requirements (minimum signals):")
            msg.append("- motion/presence: REQUIRED")
            msg.append("- light: REQUIRED")
            if zones_missing_motion:
                msg.append(f"Missing motion/presence in: {', '.join(zones_missing_motion)}")
            if zones_missing_light:
                msg.append(f"Missing light in: {', '.join(zones_missing_light)}")

        if missing:
            msg.append("")
            msg.append(f"Missing entities: {len(missing)}")
            msg.extend(f"- {m}" for m in missing[:50])
            if len(missing) > 50:
                msg.append("- … (truncated)")
        else:
            msg.append("All referenced entities exist (by current state lookup).")

        persistent_notification.async_create(
            self.hass,
            "\n".join(msg),
            title="PilotSuite Habitus zones v2 validation",
            notification_id="habitus_zones_v2_validation",
        )


class HabitusZonesV2StatesSensor(CopilotBaseEntity, SensorEntity):
    """Aggregated zone states - v2."""

    _attr_has_entity_name = False
    _attr_name = "PilotSuite habitus zones v2 states"
    _attr_unique_id = "copilot_ha_habitus_zones_v2_states"
    _attr_icon = "mdi:state-machine"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._unsub: Any = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsub = async_dispatcher_connect(
            self.hass, SIGNAL_HABITUS_ZONES_V2_UPDATED, self._on_update
        )
        await self._refresh()

    async def async_will_remove_from_hass(self) -> None:
        if callable(self._unsub):
            self._unsub()
        self._unsub = None
        await super().async_will_remove_from_hass()

    async def _refresh(self) -> None:
        zones = await async_get_zones_v2(self.hass, self._entry.entry_id)

        states: dict[str, int] = {
            "idle": 0, "active": 0, "transitioning": 0, "disabled": 0, "error": 0,
        }
        for z in zones:
            states[z.current_state] = states.get(z.current_state, 0) + 1

        active_states = {k: v for k, v in states.items() if k in ("active", "transitioning")}
        most_common = (
            max(active_states, key=active_states.get)
            if active_states else "idle"
        )

        self._attr_native_value = most_common
        self._attr_extra_state_attributes = {
            "zones_total": len(zones),
            "zones_by_state": states,
            "active_zones": [z.name for z in zones if z.current_state == "active"],
            "error_zones": [z.name for z in zones if z.current_state == "error"],
        }
        self.async_write_ha_state()

    def _on_update(self, entry_id: str) -> None:
        if entry_id != self._entry.entry_id:
            return
        self.hass.loop.call_soon_threadsafe(
            lambda: self.hass.async_create_task(self._refresh())
        )


class HabitusZonesV2HealthSensor(CopilotBaseEntity, SensorEntity):
    """Health status for zones v2."""

    _attr_has_entity_name = False
    _attr_name = "PilotSuite habitus zones v2 health"
    _attr_unique_id = "copilot_ha_habitus_zones_v2_health"
    _attr_icon = "mdi:heart-pulse"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._unsub: Any = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsub = async_dispatcher_connect(
            self.hass, SIGNAL_HABITUS_ZONES_V2_UPDATED, self._on_update
        )
        await self._refresh()

    async def async_will_remove_from_hass(self) -> None:
        if callable(self._unsub):
            self._unsub()
        self._unsub = None
        await super().async_will_remove_from_hass()

    async def _refresh(self) -> None:
        zones = await async_get_zones_v2(self.hass, self._entry.entry_id)

        total = len(zones)
        error_count = sum(1 for z in zones if z.current_state == "error")
        disabled_count = sum(1 for z in zones if z.current_state == "disabled")

        if total == 0:
            health = "unknown"
        elif error_count > 0:
            health = "critical"
        elif disabled_count > total / 2:
            health = "degraded"
        else:
            health = "healthy"

        self._attr_native_value = health
        self._attr_extra_state_attributes = {
            "total_zones": total,
            "error_count": error_count,
            "disabled_count": disabled_count,
            "healthy_count": total - error_count - disabled_count,
        }
        self.async_write_ha_state()

    def _on_update(self, entry_id: str) -> None:
        if entry_id != self._entry.entry_id:
            return
        self.hass.loop.call_soon_threadsafe(
            lambda: self.hass.async_create_task(self._refresh())
        )


class HabitusZonesV2GlobalStateSelect(CopilotBaseEntity, SelectEntity):
    """Global zone mode selector - v2."""

    _attr_has_entity_name = False
    _attr_name = "PilotSuite zones v2 global state"
    _attr_unique_id = "copilot_ha_habitus_zones_v2_global_state"
    _attr_icon = "mdi:cog-transfer"
    _attr_options = ["auto", "manual", "disabled"]
    _attr_current_option = "auto"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option

        zones = await async_get_zones_v2(self.hass, self._entry.entry_id)

        target_state = "idle"
        if option == "disabled":
            target_state = "disabled"

        for zone in zones:
            await async_set_zone_state(
                self.hass,
                self._entry.entry_id,
                zone.zone_id,
                target_state,
                fire_event=True,
            )

        self.async_write_ha_state()


class HabitusZonesV2SyncGraphButton(CopilotBaseEntity, ButtonEntity):
    """Sync zones to Brain Graph - v2."""

    _attr_has_entity_name = False
    _attr_name = "PilotSuite sync zones v2 to brain graph"
    _attr_unique_id = "copilot_ha_habitus_zones_v2_sync_graph"
    _attr_icon = "mdi:graph-outline"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry

    async def async_press(self) -> None:
        zones = await async_get_zones_v2(self.hass, self._entry.entry_id)

        results: list[dict] = []

        try:
            from .brain_graph_sync import sync_service
            for zone in zones:
                result = await sync_service.sync_zone_to_graph(zone)
                results.append({
                    "zone_id": zone.zone_id,
                    "success": result.success,
                    "nodes_created": result.nodes_created,
                    "edges_created": result.edges_created,
                })
        except ImportError:
            results = [{"error": "brain_graph_sync not available", "zones": len(zones)}]
        except Exception as e:
            results = [{"error": str(e), "zones": len(zones)}]

        success_count = sum(1 for r in results if r.get("success"))

        persistent_notification.async_create(
            self.hass,
            f"Brain Graph Sync:\n- Zones processed: {len(zones)}\n"
            f"- Success: {success_count}\n- Failed: {len(zones) - success_count}",
            title="PilotSuite Zones v2 → Brain Graph Sync",
            notification_id="habitus_zones_v2_graph_sync",
        )


class HabitusZonesV2ReloadButton(CopilotBaseEntity, ButtonEntity):
    """Reload zones v2 from storage - v2."""

    _attr_has_entity_name = False
    _attr_name = "PilotSuite reload zones v2"
    _attr_unique_id = "copilot_ha_habitus_zones_v2_reload"
    _attr_icon = "mdi:reload"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry

    async def async_press(self) -> None:
        from homeassistant.helpers.dispatcher import async_dispatcher_send

        async_dispatcher_send(
            self.hass,
            SIGNAL_HABITUS_ZONES_V2_UPDATED,
            self._entry.entry_id,
        )

        persistent_notification.async_create(
            self.hass,
            "Habitus Zones v2 reloaded successfully.",
            title="PilotSuite Zones v2",
            notification_id="habitus_zones_v2_reload",
        )


# Registry for entity creation
ENTITIES_V2 = [
    HabitusZonesV2JsonText,
    HabitusZonesV2CountSensor,
    HabitusZonesV2ValidateButton,
    HabitusZonesV2StatesSensor,
    HabitusZonesV2HealthSensor,
    HabitusZonesV2GlobalStateSelect,
    HabitusZonesV2SyncGraphButton,
    HabitusZonesV2ReloadButton,
    HabitusZonesV2ModulesSensor,  # Per-zone module configs (light, music, climate, cover, security)
]




# ---------------------------------------------------------------------------
# Habitus Zones v2 Modules Sensor
# Surfaces per-zone module configs (light, music, climate, cover, security)
# from Core's zone_automation data as HA attributes.
# Feeds styx-zone-card.js show_module_states=true
# ---------------------------------------------------------------------------

class HabitusZonesV2ModulesSensor(CopilotBaseEntity, SensorEntity):
    """Per-zone module configuration from Core zone_automation.

    Reads module configs per zone from coordinator.data["zone_automation"]
    and surfaces as attributes. Feeds styx-zone-card.js module state display.

    native_value: number of zones with active modules
    attributes.zone_modules: {zone_id: {light: {auto, brightness}, music: {auto, volume}, ...}}
    """

    _attr_has_entity_name = False
    _attr_name = "PilotSuite habitus zones v2 modules"
    _attr_unique_id = "copilot_ha_habitus_zones_v2_modules"
    _attr_icon = "mdi:playlist-settings"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry = entry
        self._unsub: Any = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsub = async_dispatcher_connect(
            self.hass, SIGNAL_HABITUS_ZONES_V2_UPDATED, self._on_update
        )
        await self._refresh()

    async def async_will_remove_from_hass(self) -> None:
        if callable(self._unsub):
            self._unsub()
        self._unsub = None
        await super().async_will_remove_from_hass()

    async def _refresh(self) -> None:
        zone_auto = self.coordinator.data.get("zone_automation", {})
        zones_list = zone_auto.get("zones", [])

        zone_modules: dict[str, dict[str, Any]] = {}
        active_count = 0

        for zone_data in zones_list:
            zid = zone_data.get("zone_id", "")
            config = zone_data.get("config", {})
            mode = config.get("automation_mode", "off")

            module_configs: dict[str, Any] = {}
            for module_key in ("light", "music", "climate", "cover", "security"):
                if module_key in config:
                    cfg = config[module_key]
                    if isinstance(cfg, dict):
                        module_configs[module_key] = cfg
                        # Count as active if auto mode or has non-default values
                        if mode != "off":
                            active_count += 1

            if module_configs or mode != "off":
                zone_modules[zid] = {
                    "automation_mode": mode,
                    "modules": module_configs,
                }

        self._attr_native_value = str(active_count)
        self._attr_extra_state_attributes = {
            "zone_modules": zone_modules,
            "zones_with_modules": len(zone_modules),
        }
        self.async_write_ha_state()

    @callback
    def _on_update(self, entry_id: str) -> None:
        if entry_id != self._entry.entry_id:
            return
        self.hass.loop.call_soon_threadsafe(
            lambda: self.hass.async_create_task(self._refresh())
        )
