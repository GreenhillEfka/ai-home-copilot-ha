"""Standalone entity→zone sorting — no HA dependencies."""

from __future__ import annotations

import unicodedata


_ZONE_KEYWORDS: dict[str, list[str]] = {
    "zone:wohnbereich": [
        "wohn", "wohnbereich", "wohnzimmer", "esszimmer", "essbereich",
        "living", "lounge", "sitzecke", "sittingroom", "tv",
    ],
    "zone:badbereich": [
        "bad", "badezimmer", "bader", "toilette", "wc", "dusche",
        "dusch", "bathroom", "bath",
    ],
    "zone:kochbereich": [
        "koch", "küche", "kueche", "kitchen", "kochen", "essküche",
    ],
    "zone:buerobereich": [
        "büro", "buero", "bueros", "arbeit", "homeoffice", "office",
        "arbeitszimmer", "studierzimmer", "study",
    ],
    "zone:gangbereich": [
        "gang", "flur", "diele", "eingang", "korridor", "hall",
        "entrance", "vestibule",
    ],
    "zone:schlafbereich": [
        "schlaf", "schlafzimmer", "bedroom", "schlafraum",
    ],
    "zone:zimmer_mira": [
        "mira", "zimmer mira", "kinderbett mira",
    ],
    "zone:zimmer_paul": [
        "paul", "zimmer paul", "pauls zimmer",
    ],
    "zone:aussenbereich": [
        "aussen", "garten", "garage", "terrasse", "balkon",
        "terrassen", "outdoor", "terrace", "balcony", "carport",
    ],
    "zone:kinderzimmer": [
        "kinderzimmer", "kinder", "kinderzimm", "playroom",
    ],
    "zone:kellerbereich": [
        "keller", "kellergeschoss", "cellar",
    ],
}

_VIRTUAL_AREAS: set[str] = {
    "energie", "netzwerk", "pv-anlage", "pv", "serverraum",
    "server", "kalender", "calendar", "ai-factory", "system",
}

_ZONE_NAMES: dict[str, str] = {
    "zone:wohnbereich": "Wohnbereich",
    "zone:badbereich": "Badbereich",
    "zone:kochbereich": "Kochbereich",
    "zone:buerobereich": "Bürobereich",
    "zone:gangbereich": "Gangbereich",
    "zone:schlafbereich": "Schlafbereich",
    "zone:zimmer_mira": "Zimmer Mira",
    "zone:zimmer_paul": "Zimmer Paul",
    "zone:aussenbereich": "Aussenbereich",
    "zone:kinderzimmer": "Kinderzimmer",
    "zone:kellerbereich": "Kellerbereich",
}


def _normalize(text: str) -> str:
    """Normalize text: lowercase + strip accents."""
    text = text.lower().strip()
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def _levenshtein(a: str, b: str) -> int:
    """Pure Python Levenshtein distance."""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[m][n]


def sort_entity_to_zone(
    entity_id: str,
    entity_name: str | None = None,
    area_name: str | None = None,
) -> tuple[str, float, dict]:
    """Sort a HA entity into a habitus zone.

    Returns (zone_id, confidence, extra_dict).
    zone_id is 'zone:ungeordnet' if confidence < 0.60.
    """
    parts = [_normalize(entity_id)]
    if entity_name:
        parts.append(_normalize(entity_name))
    if area_name:
        parts.append(_normalize(area_name))

    best_zone: str | None = None
    best_conf = 0.0
    best_keyword: str | None = None
    best_type = "none"

    # Virtual-area guard
    if area_name and any(va in _normalize(area_name) for va in _VIRTUAL_AREAS):
        return ("zone:ungeordnet", 1.0, {"match_type": "virtual_area", "is_virtual_area": True})

    # Area-exact match (highest priority)
    if area_name:
        area_n = _normalize(area_name)
        for zone_id, keywords in _ZONE_KEYWORDS.items():
            for kw in keywords:
                if _normalize(kw) == area_n:
                    conf = 0.95
                    if "." in entity_id:
                        domain = entity_id.split(".")[0]
                        if domain in ("light", "climate", "switch"):
                            conf += 0.05
                    if conf > best_conf:
                        best_conf, best_zone, best_keyword, best_type = conf, zone_id, kw, "area_exact"

    # Exact keyword match
    if best_conf < 0.90:
        for zone_id, keywords in _ZONE_KEYWORDS.items():
            for kw in keywords:
                kw_n = _normalize(kw)
                for part in parts:
                    if kw_n == part:
                        conf = 0.90
                        if conf > best_conf:
                            best_conf, best_zone, best_keyword, best_type = conf, zone_id, kw, "exact"
                        break

    # Substring match
    if best_conf < 0.75:
        for zone_id, keywords in _ZONE_KEYWORDS.items():
            for kw in keywords:
                kw_n = _normalize(kw)
                for part in parts:
                    if kw_n in part or part in kw_n:
                        conf = 0.80
                        if conf > best_conf:
                            best_conf, best_zone, best_keyword, best_type = conf, zone_id, kw, "substring"
                        break

    # Fuzzy match (Levenshtein <= 1, keyword >= 4 chars)
    if best_conf < 0.65:
        for zone_id, keywords in _ZONE_KEYWORDS.items():
            for kw in keywords:
                if len(kw) < 4:
                    continue
                kw_n = _normalize(kw)
                for part in parts:
                    if len(part) < 4:
                        continue
                    if _levenshtein(kw_n, part) <= 1:
                        conf = 0.65
                        if conf > best_conf:
                            best_conf, best_zone, best_keyword, best_type = conf, zone_id, kw, "fuzzy"
                        break

    if best_zone is None or best_conf < 0.60:
        return ("zone:ungeordnet", best_conf, {"match_type": "none", "confidence": best_conf})

    return (
        best_zone,
        best_conf,
        {
            "match_type": best_type,
            "matched_keyword": best_keyword or "",
            "zone_name_de": _ZONE_NAMES.get(best_zone, best_zone),
            "is_virtual_area": False,
        },
    )
