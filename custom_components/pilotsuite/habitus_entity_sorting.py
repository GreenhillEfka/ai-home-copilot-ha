"""HA-Entity → Habitus-Zone Sortierung.

Nutzt Keyword-Matching auf entity_id + entity_name (case-insensitive),
um eine Home-Assistant-Entity automatisch in die passende Habitus-Zone
einzuordnen. Gibt (zone_id, confidence) zurück.

Confidence-Score:
  0.5  – exact token match in entity_id (token = by '.' or '_' delimited)
  0.3  – partial substring match in entity_id
  0.3  – exact match in entity_name (full string equality)
  0.1  – partial substring match in entity_name
  +domain fallback boost (0.15–0.30) when no keyword matches
  < 0.5 → zone:ungeordnet

Ref: PS-083 | Version: 1.0 | 2026-03-20
"""
from __future__ import annotations

import re
from typing import Any

# ------------------------------------------------------------------
# Zone-Mapping: Keywords → zone_id
# ------------------------------------------------------------------
# Reihenfolge: [entity_id_keywords, entity_name_keywords]
# Jedes Keyword-Tuple hat einen Confidence-Boost.
#
# Confidence-Logik:
#   base_confidence = 0.5
#   + 0.5  wenn exact match in entity_id  (entity_id enthält keyword als
#          Wortgrenze oder als alleinstehendes Fragment)
#   + 0.3  wenn partial match in entity_id (entity_id enthält keyword)
#   + 0.3  wenn exact match in entity_name
#   + 0.1  wenn partial match in entity_name
#   + 0.1  wenn domain-basiert erraten (z.B. climate.* ohne Zone-Keyword)
#   Cap: 1.0
#
# Domain-Anker: wenn kein Zone-Keyword trifft, aber die entity_domain
# einen starken Rückschluss erlaubt (z.B. climate → living mit +0.1)

ZONE_KEYWORD_MAP: list[tuple[str, list[str], list[str]]] = [
    # zone_id, entity_id_keywords, entity_name_keywords
    (
        "living",
        [
            # Exact/strong entity_id keywords
            "wohnen", "wohnzimmer", "livingroom", "living_room",
            "wohnraum", "couch", "sofa", "tv_wohn", "tv_wohnzimmer",
            "esstisch", "terrasse_innen",
        ],
        [
            "wohnen", "wohnzimmer", "living", "couch", "sofa",
            "wohnraum", "tv-wohnzimmer", "tv wohnzimmer", "fernseher",
            "esstisch", "wohnzimmerlampe", "wohnzimmerlicht",
        ],
    ),
    (
        "sleeping",
        [
            "schlafzimmer", "schlafen", "bedroom", "bed_room",
            "bett", "nachttisch", "nachttischlampe",
            "schlafz",
        ],
        [
            "schlafzimmer", "schlafen", "schlaf", "bedroom",
            "bett", "nachttisch", "nachttischlampe",
            "schlafzimmerlampe", "schlafzimmerlicht",
        ],
    ),
    (
        "kitchen",
        [
            "kueche", "küche", "kitchen", "kochen", "herd",
            "ofen", "kochfeld", "abzug", "geschirrspueler",
            "kuehlschrank", "kühlschrank", "spuele", "spüle",
            "esszimmer", "fruehstück", "frühstück",
        ],
        [
            "küche", "kueche", "kitchen", "kochen", "herd",
            "ofen", "kochfeld", "abzug", "geschirrspüler",
            "kühlschrank", "kuehlschrank", "spüle", "spuele",
            "esszimmer", "frühstück", "fruehstück",
            "küchenlicht", "kuechenlicht", "kochstelle",
        ],
    ),
    (
        "bathing",
        [
            "badezimmer", "bathroom", "bad", "dusche", "duschen",
            "wc", "toilette", "waschbecken", "badewanne",
            "handtuchheizung",
        ],
        [
            "badezimmer", "bathroom", "bad", "dusche", "duschen",
            "wc", "toilette", "waschbecken", "badewanne",
            "handtuchheizung", "badezimmerlampe", "badlicht",
            "duschlicht",
        ],
    ),
    (
        "transit",
        [
            "flur", "gang", "diele", "treppe", "staircase",
            "stairwell", "entrance", "haustuer", "haustür",
            "vorraum", "korridor", "durchgang",
        ],
        [
            "flur", "gang", "diele", "treppe", "staircase",
            "stairwell", "entrance", "haustür", "haustuer",
            "vorraum", "korridor", "durchgang",
            "flurlicht", "ganglicht", "treppenlicht",
        ],
    ),
    (
        "working",
        [
            "buero", "büro", "office", "arbeitszimmer", "arbeit",
            "computer", "schreibtisch", "desk", "homeoffice",
            "home_office", "werkbank",
        ],
        [
            "büro", "buero", "office", "arbeitszimmer", "arbeit",
            "computer", "schreibtisch", "desk", "homeoffice",
            "werkbank", "bürolicht", "buerolicht",
        ],
    ),
    (
        "outdoor",
        [
            "terrasse", "terrace", "garten", "garden", "balkon",
            "garage", "carport", "aussenbereich", "außenbereich",
            "outdoor", "pond", "teich", "pool", "markise",
            "haustor", "einfahrt", "tor",
        ],
        [
            "terrasse", "terrace", "garten", "garden", "balkon",
            "garage", "carport", "außenbereich", "aussenbereich",
            "outdoor", "teich", "pool", "markise",
            "haustor", "einfahrt", "tor",
            "gartenlicht", "terrassenlicht", "garagenlicht",
        ],
    ),
    (
        "utility",
        [
            "keller", "basement", "abstellraum", "speicher",
            "attic", "dachboden", "waschkeller", "technik",
            "utility_room", "heizungsraum",
        ],
        [
            "keller", "basement", "abstellraum", "speicher",
            "attic", "dachboden", "waschkeller", "technik",
            "utility", "heizungsraum",
            "kellerlicht", "kellerraum",
        ],
    ),
    (
        "multi",
        [
            "kinderzimmer", "kinder", "kids", "kidsroom",
            "spielzimmer", "playroom", "multifunktion",
            "mira", "paul", "gaestezimmer", "gästezimmer",
            "musikzimmer", "fitness", "fitnessraum",
        ],
        [
            "kinderzimmer", "kinder", "kids", "kidsroom",
            "spielzimmer", "playroom", "multifunktion",
            "mira", "paul", "gästezimmer", "gaestezimmer",
            "musikzimmer", "fitness", "fitnessraum",
        ],
    ),
]

# ------------------------------------------------------------------
# Domain → Zone Heuristik (Fallback, wenn kein Zone-Keyword greift)
# ------------------------------------------------------------------
# Wird verwendet, wenn entity_id / entity_name keine Zone-Keywords
# enthalten, aber die Domain einen Hinweis gibt.
# Wird NUR addiert, wenn nicht bereits zone_id durch Keyword gefunden.
# Key 'entity_domain' avoids shadowing Python built-in 'domain'.

DOMAIN_ZONE_FALLBACK: list[tuple[str, str, float]] = [
    # (entity_domain, default_zone, confidence_boost)
    # cover (Jalousien/Rollläden) → living (typisch im Wohnzimmer)
    ("cover", "living", 0.15),
    # scene → living (Szenen primär im Wohnbereich definiert)
    ("scene", "living", 0.15),
    # audio → living (Sonos/BluOS primär im Wohnbereich)
    ("audio", "living", 0.20),
    # lock → outdoor (Haustürschloss)
    ("lock", "outdoor", 0.30),
    # vacuum → utility (Staubsauger wird in UT gelagert)
    ("vacuum", "utility", 0.20),
    # humidifier → bathing
    ("humidifier", "bathing", 0.25),
    # dehumidifier → bathing
    ("dehumidifier", "bathing", 0.25),
    # sensor with airquality/asthma in id → transit
    # (picked up by keyword fallback already; domain-only: sensor → transit)
    ("sensor", "transit", 0.10),
    # plant → outdoor (Pflanzensensoren im Garten)
    ("plant", "outdoor", 0.25),
]

# ------------------------------------------------------------------
# Unsortiert-Marker
# ------------------------------------------------------------------
UNSORTED_ZONE: str = "ungeordnet"
CONFIDENCE_THRESHOLD: float = 0.5


# ------------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------------

def _extract_domain(entity_id: str) -> str:
    """Extrahiere die Domain aus einer entity_id (z.B. 'light.wohnzimmer_decke' → 'light')."""
    if not entity_id or "." not in entity_id:
        return ""
    return entity_id.split(".", 1)[0].lower()


def _is_token_match(keyword: str, text: str) -> bool:
    """Prüfe ob keyword irgendwo als vollständiges Token in text vorkommt.

    Token = durch '.' oder '_' begrenzter Teilstring.
    Z.B. 'schlafzimmer' ist Token in 'schlafzimmer_decke' und
    'schlafzimmer' ist Token in 'light.schlafzimmer'.
    """
    parts = re.split(r'[._]', text)
    return keyword in parts


def _keyword_score(
    entity_id_lower: str,
    entity_name_lower: str,
    id_keywords: list[str],
    name_keywords: list[str],
) -> float:
    """Berechne Keyword-basierten Confidence-Score (0.0 – 1.0).

    +0.5 exact token match in entity_id  (keyword ist token-begrenzt)
    +0.3 partial match in entity_id     (substring anywhere)
    +0.3 exact match in entity_name     (name ist genau das keyword)
    +0.1 partial match in entity_name   (substring in name)
    """
    score = 0.0

    # --- entity_id checks (stärker, da strukturierter) ---
    for kw in id_keywords:
        if _is_token_match(kw, entity_id_lower):
            score = max(score, 0.5)
            break

    if score < 0.5:
        for kw in id_keywords:
            if kw in entity_id_lower:
                score = max(score, 0.3)
                break

    # --- entity_name checks (weniger Gewicht, da freier Text) ---
    for kw in name_keywords:
        if kw == entity_name_lower.strip():
            score = max(score, 0.3)
            break

    if score < 0.3:
        for kw in name_keywords:
            if kw in entity_name_lower:
                score = max(score, 0.1)
                break

    return score


# ------------------------------------------------------------------
# Hauptfunktion
# ------------------------------------------------------------------

def sort_entity_to_zone(
    entity_id: str,
    entity_name: str,
    entity_state: Any = None,
) -> tuple[str, float]:
    """Sortiere eine HA-Entity in die passende Habitus-Zone.

    Args:
        entity_id:   Home-Assistant entity_id (z.B. "light.wohnzimmer_decke")
        entity_name: Friendly name der Entity (z.B. "Wohnzimmer Decke")
        entity_state: Aktueller State (z.B. "on", 21.5) – wird nicht
                     für die Sortierung verwendet, ist aber reserviert
                     für spätere Logik.

    Returns:
        tuple[str, float]: (zone_id, confidence)
        - zone_id = "ungeordnet" wenn confidence < 0.5
        - confidence ∈ [0.0, 1.0]

    Examples:
        >>> sort_entity_to_zone("light.wohnzimmer_decke", "Wohnzimmer Decke")
        ('living', 0.8)

        >>> sort_entity_to_zone("sensor.unknown_temp", "Temperature Sensor")
        ('ungeordnet', 0.1)
    """
    if not entity_id:
        return (UNSORTED_ZONE, 0.0)

    entity_id_lower = entity_id.lower()
    entity_name_lower = entity_name.lower() if entity_name else ""

    best_zone: str | None = None
    best_score: float = 0.0

    # --- 1. Keyword-Matching ---
    for zone_id, id_keywords, name_keywords in ZONE_KEYWORD_MAP:
        kw_score = _keyword_score(entity_id_lower, entity_name_lower, id_keywords, name_keywords)
        if kw_score > best_score:
            best_score = kw_score
            best_zone = zone_id

    # --- 2. Domain-Fallback (nur wenn kein Keyword-Treffer) ---
    if best_zone is None or best_score < 0.5:
        entity_domain = _extract_domain(entity_id_lower)
        for fallback_domain, fallback_zone, boost in DOMAIN_ZONE_FALLBACK:
            if entity_domain == fallback_domain:
                # Nur verwenden wenn noch kein besseres Ergebnis da ist
                if best_score < boost:
                    best_score = boost
                    best_zone = fallback_zone
                break

    # --- 3. Confidence-Schwelle ---
    if best_score < CONFIDENCE_THRESHOLD or best_zone is None:
        return (UNSORTED_ZONE, round(best_score, 2))

    return (best_zone, round(best_score, 2))
