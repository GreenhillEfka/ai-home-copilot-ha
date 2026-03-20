"""Habitus Module Schema — ZONE_MODULE_SCHEMA and helpers.

Defines the mandatory and optional modules for each habitus zone.
"""
from __future__ import annotations

from typing import Final

# ── Constants ──────────────────────────────────────────────────────────────────

MODULE_LIGHT: Final = "light"
MODULE_AUDIO: Final = "audio"
MODULE_CLIMATE: Final = "climate"
MODULE_COVER: Final = "cover"
MODULE_ENERGY: Final = "energy"
MODULE_SCENE: Final = "scene"
MODULE_SECURITY: Final = "security"

ALL_MODULES: Final = frozenset({
    MODULE_LIGHT, MODULE_AUDIO, MODULE_CLIMATE,
    MODULE_COVER, MODULE_ENERGY, MODULE_SCENE, MODULE_SECURITY,
})

# ── Zone → Allowed Modules ────────────────────────────────────────────────────

ZONE_MODULE_SCHEMA: dict[str, list[str]] = {
    # Wohnbereich: Vollversorgung
    "living": [
        MODULE_LIGHT, MODULE_AUDIO, MODULE_CLIMATE,
        MODULE_COVER, MODULE_ENERGY, MODULE_SCENE,
    ],
    # Schlafbereich: Licht + Klima (Ruhe)
    "sleeping": [MODULE_LIGHT, MODULE_CLIMATE],
    # Kochbereich: Licht + Klima + Energie
    "cooking": [MODULE_LIGHT, MODULE_CLIMATE, MODULE_ENERGY],
    # Badbereich: Licht + Klima
    "bathing": [MODULE_LIGHT, MODULE_CLIMATE],
    # Gangbereich: Nur Licht (Durchgangszone)
    "transit": [MODULE_LIGHT],
    # Bürobereich: Licht + Klima + Energie
    "working": [MODULE_LIGHT, MODULE_CLIMATE, MODULE_ENERGY],
    # Außenbereich: Licht + Kamera/Security
    "outdoor": [MODULE_LIGHT, MODULE_SECURITY],
    # Kellerbereich: Nur Licht
    "storage": [MODULE_LIGHT],
    # Kinderzimmer: Licht + Klima
    "child": [MODULE_LIGHT, MODULE_CLIMATE],
}

# ── Display Names ──────────────────────────────────────────────────────────────

ZONE_DISPLAY_NAMES: dict[str, str] = {
    "living": "Wohnbereich",
    "sleeping": "Schlafbereich",
    "cooking": "Kochbereich",
    "bathing": "Badbereich",
    "transit": "Gangbereich",
    "working": "Bürobereich",
    "outdoor": "Außenbereich",
    "storage": "Kellerbereich",
    "child": "Kinderzimmer",
}

MODULE_DESCRIPTIONS: dict[str, str] = {
    MODULE_LIGHT: "Lichtsteuerung (Schalter, Dimmer, Farbe)",
    MODULE_AUDIO: "Musik / Multiroom-Audio",
    MODULE_CLIMATE: "Heizung / Klima",
    MODULE_COVER: "Jalousien / Rollläden",
    MODULE_ENERGY: "Energieverbrauch / Smartmeter",
    MODULE_SCENE: "Szenen / Automatisierungen",
    MODULE_SECURITY: "Kamera / Alarmanlage",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_zone_modules(zone_type: str) -> list[str]:
    """Return allowed module types for a zone type."""
    return list(ZONE_MODULE_SCHEMA.get(zone_type, []))


def is_module_allowed(zone_type: str, module: str) -> bool:
    """Check if a module is allowed in a zone type."""
    return module in ZONE_MODULE_SCHEMA.get(zone_type, [])


def all_zones() -> list[str]:
    """Return all known zone type keys."""
    return list(ZONE_MODULE_SCHEMA.keys())


def all_modules() -> frozenset[str]:
    """Return all known module type keys."""
    return ALL_MODULES
