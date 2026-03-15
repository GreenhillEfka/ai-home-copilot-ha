"""PilotSuite — Smart Habitus Zone Auto-Setup.

Auto-creates Habitus Zones from HA areas with intelligent aggregation:
- Groups similar rooms into logical zones (e.g., Toilet + Bad → Badbereich)
- Auto-assigns entities with role + tag detection
- Feeds zone config into Core's modular logic

Called during async_setup_entry if no zones are configured yet.
"""
from __future__ import annotations

import logging
import unicodedata
import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry, device_registry, entity_registry

_LOGGER = logging.getLogger(__name__)

# ── Habitus Zone Templates ──────────────────────────────────────────
# German-language keyword matching — mirrors Core's ZoneMatcher templates.
# Each template groups multiple HA areas into a single logical zone.

HABITUS_ZONE_TEMPLATES: list[dict[str, Any]] = [
    {
        "zone_id": "wohnbereich",
        "name_de": "Wohnbereich",
        "keywords": [
            "wohn", "wohnzimmer", "esszimmer", "ess", "gast",
            "living", "dining", "lounge", "loft", "entspannung",
        ],
        "zone_type": "area",
        "icon": "mdi:sofa",
    },
    {
        "zone_id": "badbereich",
        "name_de": "Badbereich",
        "keywords": [
            "bad", "badezimmer", "toilette", "wc", "dusche",
            "bath", "bathroom", "shower",
        ],
        "zone_type": "area",
        "icon": "mdi:shower-head",
    },
    {
        "zone_id": "kochbereich",
        "name_de": "Kochbereich",
        "keywords": [
            "koch", "küche", "kueche", "speis", "vorrat",
            "kitchen", "pantry",
        ],
        "zone_type": "area",
        "icon": "mdi:stove",
    },
    {
        "zone_id": "buerobereich",
        "name_de": "Bürobereich",
        "keywords": [
            "büro", "buero", "arbeit", "homeoffice", "office",
            "studio", "werkstatt",
        ],
        "zone_type": "room",
        "icon": "mdi:desk",
    },
    {
        "zone_id": "gangbereich",
        "name_de": "Gangbereich",
        "keywords": [
            "gang", "flur", "diele", "eingang", "korridor",
            "hall", "corridor", "entry", "vorraum", "vorzimmer",
        ],
        "zone_type": "area",
        "icon": "mdi:door-open",
    },
    {
        "zone_id": "schlafbereich",
        "name_de": "Schlafbereich",
        "keywords": [
            "schlaf", "schlafzimmer", "bedroom",
        ],
        "zone_type": "room",
        "icon": "mdi:bed",
    },
    {
        "zone_id": "kinderzimmer",
        "name_de": "Kinderzimmer",
        "keywords": [
            "kind", "kinderzimmer", "kinder", "nursery",
            "spielzimmer", "jugend",
        ],
        "zone_type": "room",
        "icon": "mdi:baby-face-outline",
    },
    {
        "zone_id": "terrassenbereich",
        "name_de": "Terrassenbereich",
        "keywords": [
            "terrass", "balkon", "veranda", "patio", "loggia",
            "wintergarten",
        ],
        "zone_type": "outdoor",
        "icon": "mdi:flower",
    },
    {
        "zone_id": "aussenbereich",
        "name_de": "Außenbereich",
        "keywords": [
            "aussen", "außen", "garten", "garage", "carport",
            "outdoor", "garden", "hof", "parkplatz",
        ],
        "zone_type": "outdoor",
        "icon": "mdi:tree",
    },
    {
        "zone_id": "kellerbereich",
        "name_de": "Kellerbereich",
        "keywords": [
            "keller", "basement", "wasch", "heizraum", "technik",
            "hauswirtschaft", "lager", "abstellraum",
        ],
        "zone_type": "area",
        "icon": "mdi:stairs-down",
    },
]

# ── Entity Role Detection ───────────────────────────────────────────

_MOTION_HINTS = (
    "motion", "presence", "occupancy", "bewegung",
    "praesenz", "präsenz", "anwesenheit", "pir",
    "belegt", "besetzt",
)

_DOMAIN_ROLE_MAP = {
    "light": "lights",
    "media_player": "media",
    "climate": "heating",
    "cover": "cover",
    "lock": "lock",
    "fan": "heating",
    "humidifier": "humidity",
    "vacuum": "other",
    "camera": "other",
}

_ENTITY_KEYWORD_ROLES = {
    "temperatur": "temperature",
    "temperature": "temperature",
    "humidity": "humidity",
    "feuchte": "humidity",
    "luftfeucht": "humidity",
    "co2": "co2",
    "pressure": "pressure",
    "druck": "pressure",
    "helligkeit": "brightness",
    "illuminance": "brightness",
    "lux": "brightness",
    "energy": "energy",
    "energie": "energy",
    "power": "power",
    "verbrauch": "power",
    "leistung": "power",
    "fenster": "window",
    "window": "window",
    "tuer": "door",
    "tür": "door",
    "door": "door",
}

# ── Tag Detection ───────────────────────────────────────────────────

ROLE_TAG_MAP = {
    "lights": "licht",
    "motion": "praesenz",
    "brightness": "licht",
    "media": "medien",
    "heating": "klima",
    "temperature": "klima",
    "humidity": "klima",
    "co2": "klima",
    "cover": "rollladen",
    "lock": "schloss",
    "door": "tuer",
    "window": "fenster",
    "energy": "energie",
    "power": "energie",
}


def _normalize_text(text: str) -> str:
    """Normalize text for keyword matching (lowercase, strip accents)."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return nfkd.encode("ascii", "ignore").decode("ascii").strip()


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
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


# Virtual/system areas that should be excluded from zone auto-setup.
# These contain organizational entities, not physical room devices.
_VIRTUAL_AREA_HINTS = frozenset({
    "energie", "energy", "netzwerk", "network", "kontrollraum",
    "kalender", "calendar", "kosten", "cost", "personen", "person",
    "serverraum", "umwelt", "environment", "medienkontrolle",
    "free devices", "haupthaus", "pv-anlage", "move", "viture",
    "firetv", "airplay", "ai-factory",
})


def _is_virtual_area(area_name: str) -> bool:
    """Check if an area is a virtual/organizational area (not a physical room)."""
    normalized = _normalize_text(area_name)
    return any(hint in normalized for hint in _VIRTUAL_AREA_HINTS)


def _match_area_to_template(area_name: str) -> tuple[dict | None, float]:
    """Match an HA area name to a Habitus Zone template.

    Returns (template, confidence) or (None, 0.0) if no match.
    Uses exact/substring matching first, then fuzzy matching (Levenshtein ≤ 1)
    for typo tolerance (e.g., "Toilettte" → "toilette").
    """
    normalized = _normalize_text(area_name)
    best_template = None
    best_confidence = 0.0

    for template in HABITUS_ZONE_TEMPLATES:
        for keyword in template["keywords"]:
            kw_norm = _normalize_text(keyword)

            # Exact or substring match
            if kw_norm in normalized or normalized in kw_norm:
                confidence = 0.9 if kw_norm == normalized else 0.8
                length_bonus = min(len(kw_norm) / max(len(normalized), 1), 0.1)
                confidence = min(confidence + length_bonus, 1.0)

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_template = template
                continue

            # Fuzzy match: Levenshtein distance ≤ 1 for keywords ≥ 4 chars
            if len(kw_norm) >= 4 and _levenshtein_distance(kw_norm, normalized) <= 1:
                confidence = 0.7  # lower confidence for fuzzy match
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_template = template

    return best_template, best_confidence


def detect_entity_role(
    entity_id: str,
    device_class: str | None = None,
    friendly_name: str | None = None,
) -> str:
    """Detect entity role from domain, device_class, and entity name."""
    domain = entity_id.split(".")[0] if "." in entity_id else ""

    # 1. Check motion candidates (highest priority)
    name_lower = (friendly_name or entity_id).lower()
    entity_lower = entity_id.lower()
    if domain in ("binary_sensor", "sensor"):
        if device_class and device_class.lower() in ("motion", "presence", "occupancy"):
            return "motion"
        if any(hint in entity_lower or hint in name_lower for hint in _MOTION_HINTS):
            return "motion"

    # 2. Domain mapping takes priority over keyword matching
    #    (prevents lock.haustuer from matching "tuer" → door)
    if domain in _DOMAIN_ROLE_MAP:
        return _DOMAIN_ROLE_MAP[domain]

    # 3. Check entity ID keywords for sensor/binary_sensor disambiguation
    for keyword, role in _ENTITY_KEYWORD_ROLES.items():
        if keyword in entity_lower:
            return role

    # 4. Generic sensor classification
    if domain == "sensor":
        if device_class:
            dc = device_class.lower()
            if dc in ("temperature",):
                return "temperature"
            if dc in ("humidity",):
                return "humidity"
            if dc in ("illuminance",):
                return "brightness"
            if dc in ("power", "current", "voltage"):
                return "power"
            if dc in ("energy",):
                return "energy"
            if dc in ("pressure",):
                return "pressure"
        return "other"

    if domain == "binary_sensor":
        if device_class:
            dc = device_class.lower()
            if dc in ("door",):
                return "door"
            if dc in ("window",):
                return "window"
            if dc in ("lock",):
                return "lock"
        return "other"

    return "other"


def detect_entity_tags(entity_id: str, role: str) -> list[str]:
    """Detect entity tags from role and entity name."""
    tags = []

    # Primary tag from role
    primary_tag = ROLE_TAG_MAP.get(role)
    if primary_tag:
        tags.append(primary_tag)

    # Additional tags from entity name patterns
    entity_lower = entity_id.lower()
    if "sicherheit" in entity_lower or "alarm" in entity_lower:
        tags.append("sicherheit")
    if "styx" in entity_lower or "pilotsuite" in entity_lower:
        tags.append("styx")

    return list(dict.fromkeys(tags))  # deduplicate preserving order


def aggregate_areas_to_habitus_zones(
    areas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Group HA areas into logical Habitus Zones using template matching.

    Args:
        areas: List of dicts with "area_id", "name", optional "icon"

    Returns:
        List of aggregated zone dicts with:
        - zone_id, name_de, zone_type, icon
        - area_ids: list of HA area IDs in this zone
        - area_names: list of HA area names
        - confidence: match confidence (0.0-1.0)
    """
    # Track which template maps to which areas
    template_areas: dict[str, list[dict]] = {}  # template zone_id → [area_dicts]
    template_map: dict[str, dict] = {}  # template zone_id → template
    unmatched: list[dict] = []

    for area in areas:
        area_name = area.get("name", "")

        # Skip virtual/organizational areas (Energie, Netzwerk, etc.)
        if _is_virtual_area(area_name):
            continue

        template, confidence = _match_area_to_template(area_name)

        if template and confidence >= 0.6:
            tid = template["zone_id"]
            if tid not in template_areas:
                template_areas[tid] = []
                template_map[tid] = template
            template_areas[tid].append({**area, "_confidence": confidence})
        else:
            unmatched.append(area)

    # Build aggregated zones
    result: list[dict[str, Any]] = []

    for tid, matched_areas in template_areas.items():
        template = template_map[tid]
        area_ids = [a["area_id"] for a in matched_areas]
        area_names = [a["name"] for a in matched_areas]
        avg_confidence = sum(a["_confidence"] for a in matched_areas) / len(matched_areas)

        result.append({
            "zone_id": f"zone:{tid}",
            "name_de": template["name_de"],
            "zone_type": template["zone_type"],
            "icon": template["icon"],
            "area_ids": area_ids,
            "area_names": area_names,
            "confidence": round(avg_confidence, 2),
            "aggregated": len(area_ids) > 1,
        })

    # Unmatched areas become standalone zones
    for area in unmatched:
        area_name = area.get("name", "Unbekannt")
        slug = re.sub(
            r"[^a-z0-9]+", "_",
            _normalize_text(area_name),
        ).strip("_") or "zone"
        result.append({
            "zone_id": f"zone:{slug}",
            "name_de": area_name,
            "zone_type": "room",
            "icon": area.get("icon") or "mdi:home-outline",
            "area_ids": [area["area_id"]],
            "area_names": [area_name],
            "confidence": 0.5,
            "aggregated": False,
        })

    # Sort: aggregated zones first (more important), then by name
    result.sort(key=lambda z: (-len(z["area_ids"]), z["name_de"]))
    return result


async def async_auto_create_habitus_zones(
    hass: HomeAssistant,
    entry_id: str,
) -> int:
    """Auto-create Habitus Zones from HA areas with smart aggregation.

    Called during async_setup_entry if no zones are configured yet.
    Returns the number of zones created.
    """
    from .habitus_zones_store_v2 import HabitusZoneV2, async_get_zones_v2, async_set_zones_v2
    from .config_zones_flow import create_zone_tag, tag_zone_entities

    # Check if zones already exist
    existing = await async_get_zones_v2(hass, entry_id)
    if existing:
        _LOGGER.debug("Habitus zones already configured (%d zones), skipping auto-setup", len(existing))
        return 0

    # Get all HA areas
    ar = area_registry.async_get(hass)
    ent_reg = entity_registry.async_get(hass)
    dev_reg = device_registry.async_get(hass)

    areas = [
        {"area_id": area.id, "name": area.name, "icon": area.icon}
        for area in ar.areas.values()
        if area.name  # skip unnamed areas
    ]

    if not areas:
        _LOGGER.info("No HA areas found, skipping zone auto-setup")
        return 0

    # Smart aggregation: group areas into logical zones
    aggregated = aggregate_areas_to_habitus_zones(areas)
    _LOGGER.info(
        "Zone auto-setup: %d HA areas → %d Habitus Zones (aggregated)",
        len(areas), len(aggregated),
    )

    # For each aggregated zone, collect and classify entities
    zones: list[HabitusZoneV2] = []

    for zone_info in aggregated:
        zone_id = zone_info["zone_id"]
        zone_name = zone_info["name_de"]
        area_ids = zone_info["area_ids"]

        # Collect all entities from all areas in this zone
        role_entities: dict[str, list[str]] = {}
        all_entity_ids: list[str] = []
        seen: set[str] = set()

        for area_id in area_ids:
            for entity_id, reg_entry in ent_reg.entities.items():
                if reg_entry.disabled_by is not None:
                    continue

                # Check if entity belongs to this area
                ent_area = reg_entry.area_id
                if not ent_area and reg_entry.device_id:
                    device = dev_reg.async_get(reg_entry.device_id)
                    if device:
                        ent_area = device.area_id

                if ent_area != area_id:
                    continue
                if entity_id in seen:
                    continue
                seen.add(entity_id)

                # Detect role
                state = hass.states.get(entity_id)
                device_class = None
                friendly_name = None
                if state:
                    device_class = state.attributes.get("device_class")
                    friendly_name = state.attributes.get("friendly_name")
                if not device_class:
                    device_class = getattr(reg_entry, "device_class", None)

                role = detect_entity_role(entity_id, device_class, friendly_name)

                if role not in role_entities:
                    role_entities[role] = []
                role_entities[role].append(entity_id)
                all_entity_ids.append(entity_id)

        if not all_entity_ids:
            _LOGGER.debug("Zone %s has no entities, skipping", zone_name)
            continue

        # Sort entities within each role
        for role_list in role_entities.values():
            role_list.sort()

        zone = HabitusZoneV2(
            zone_id=zone_id,
            name=zone_name,
            zone_type=zone_info["zone_type"],
            entity_ids=tuple(all_entity_ids),
            entities=role_entities or None,
            metadata={
                "ha_area_ids": area_ids,
                "ha_area_names": zone_info["area_names"],
                "auto_created": True,
                "aggregated": zone_info["aggregated"],
                "confidence": zone_info["confidence"],
            },
        )
        zones.append(zone)

        _LOGGER.info(
            "Zone auto-setup: %s ← %s (%d entities, %d roles)",
            zone_name,
            " + ".join(zone_info["area_names"]),
            len(all_entity_ids),
            len(role_entities),
        )

    if not zones:
        _LOGGER.info("No zones with entities found, skipping auto-setup")
        return 0

    # Persist zones
    await async_set_zones_v2(hass, entry_id, zones, validate=False)

    # Auto-create tags and tag entities
    for zone in zones:
        try:
            await create_zone_tag(hass, zone.zone_id, zone.name)
            await tag_zone_entities(hass, zone.zone_id, list(zone.entity_ids))
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Could not auto-tag entities for zone %s", zone.name)

    _LOGGER.info(
        "Zone auto-setup complete: %d zones created from %d HA areas",
        len(zones), len(areas),
    )
    return len(zones)
