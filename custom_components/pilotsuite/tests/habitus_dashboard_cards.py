"""Standalone card helper functions used by legacy dashboard card tests.

These helpers intentionally return YAML snippets as strings and are small,
low-coupling adapters used only in tests and local tooling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ZoneStatusData:
    zone_id: str
    zone_name: str
    score: float
    mood: str | None = None
    active_entities: int | None = None
    last_activity: str | None = None


@dataclass(frozen=True)
class ZoneTransitionData:
    timestamp: str
    from_zone: str | None
    to_zone: str
    trigger: str | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class MoodDistributionData:
    mood: str
    count: int
    percentage: float
    zone_name: str | None = None


def _entities_card(zone_name: str, entities: list[str]) -> str:
    if not entities:
        return (
            f"- type: entities\n"
            f"  title: {zone_name}\n"
            "  entities:\n"
            "    - sensor: none\n"
            "      name: (keine)"
        )
    entity_yaml = "\n".join(f"    - {ent}" for ent in entities)
    return (
        "- type: entities\n"
        f"  title: {zone_name}\n"
        "  entities:\n"
        f"{entity_yaml}"
    )


def _gauge_card(sensor_id: str, name: str, min_value: int, max_value: int) -> str:
    return (
        "- type: gauge\n"
        f"  entity: {sensor_id}\n"
        f"  name: {name}\n"
        f"  min: {min_value}\n"
        f"  max: {max_value}\n"
        "  severity:\n"
        "    - value: 0\n"
        "      color: red\n"
        "    - value: 50\n"
        "      color: yellow\n"
        "    - value: 80\n"
        "      color: green\n"
    )


def _history_graph_card(title: str, entities: list[str], hours: int = 24) -> str:
    entities_yaml = "\n".join(f"    - {eid}" for eid in entities)
    return (
        "- type: history-graph\n"
        f"  title: {title}\n"
        f"  hours_to_show: {hours}\n"
        "  entities:\n"
        f"{entities_yaml}"
    )


def _markdown_card(header: str, text: str) -> str:
    return (
        "- type: markdown\n"
        f"  title: {header}\n"
        "  content: >-\n"
        f"    {text}"
    )


def _grid_card(cards: list[str], columns: int = 1) -> str:
    return (
        "- type: grid\n"
        f"  columns: {columns}\n"
        "  cards:\n"
        + "\n".join(c.lstrip() for c in cards)
    )


def _vertical_stack_card(cards: list[str]) -> str:
    return (
        "- type: vertical-stack\n"
        "  cards:\n"
        + "\n".join(c if c.startswith("  -") else f"  - {c}" for c in cards)
    )


def generate_zone_status_card_simple(zone_name: str, score: float) -> str:
    return _vertical_stack_card(
        [
            _markdown_card(
                "Habitus Zone",
                f"Zone **{zone_name}**: {score}",
            ),
            _gauge_card("sensor.zone_score", "Zone Score", 0, 100),
        ]
    )


def generate_zone_status_card_yaml(zones: list[Any], active_zone_id: str | None = None, score_entity_id: str = "sensor.zone_score") -> str:
    if not zones:
        return _markdown_card("Aktueller Status", "Keine Zonen gefunden").strip()

    title = "Aktueller Status"
    rows: list[str] = []
    for z in zones:
        active_marker = " *" if active_zone_id and getattr(z, "zone_id", None) == active_zone_id else ""
        rows.append(f"- {z.name}{active_marker}")

    content = "\\n".join(rows)
    return _markdown_card(title, "\\n".join(rows)) + "\n" + _gauge_card(score_entity_id, "Zone Score", 0, 100)


def generate_zone_status_card_yaml_from_data(zone_data: list[ZoneStatusData], score_entity_id: str = "sensor.zone_score") -> str:
    rows = [f"- {z.zone_name}: {z.score}" for z in zone_data]
    return _markdown_card("Aktueller Status", "\\n".join(rows)) + "\n" + _gauge_card(score_entity_id, "Zone Score", 0, 100)


def generate_zone_transitions_card_yaml(transitions: list[ZoneTransitionData]) -> str:
    if not transitions:
        return _markdown_card("Zone Transitions", "Keine Übergänge")

    lines: list[str] = []
    for t in transitions:
        src = t.from_zone or "-"
        conf = f" ({t.confidence:.2f})" if t.confidence is not None else ""
        trig = f" [{t.trigger}]" if t.trigger else ""
        lines.append(f"{t.timestamp}: {src} -> {t.to_zone}{trig}{conf}")
    return _markdown_card("Zone Transitions", "\\n".join(lines))


def generate_mood_distribution_card_yaml(moods: list[MoodDistributionData]) -> str:
    if not moods:
        return _markdown_card("Stimmungsverteilung", "Keine Mood-Daten")
    lines = [f"{m.mood}: {m.count} ({m.percentage:.1f}%)" for m in moods]
    return _markdown_card("Stimmungsverteilung", "\\n".join(lines))


def generate_mood_distribution_card_simple(mood_counts: dict[str, int], total_zones: int = 0) -> str:
    if total_zones <= 0:
        total_zones = max(1, sum(mood_counts.values()) or 1)
    lines = []
    for mood, count in mood_counts.items():
        pct = (count / total_zones) * 100 if total_zones else 0.0
        lines.append(f"{mood}: {count} ({pct:.1f}%)")
    if not lines:
        lines = ["Keine Daten"]
    return _markdown_card("Mood Verteilung", "\\n".join(lines))


def generate_habitus_dashboard_view(
    zones: list[Any],
    active_zone_id: str | None,
    transitions: list[ZoneTransitionData],
    mood_data: list[MoodDistributionData],
) -> str:
    cards: list[str] = []
    cards.append(generate_zone_status_card_simple(active_zone_id or "", 0.0))
    cards.append(generate_zone_status_card_yaml(zones, active_zone_id))
    cards.append(generate_zone_transitions_card_yaml(transitions))
    cards.append(generate_mood_distribution_card_yaml(mood_data))
    return _vertical_stack_card(cards)


def calculate_zone_score(zone: Any, hass: Any) -> float | None:
    entities = list(getattr(zone, "entity_ids", []) or [])
    if not entities:
        return None

    active = 0
    for entity_id in entities:
        st = hass.states.get(entity_id)
        if st is None:
            continue
        value = getattr(st, "state", "").lower()
        if value in {"on", "open", "playing", "home", "occupied"}:
            active += 1
    return round((active / len(entities)) * 100, 1)


def aggregate_mood_distribution(
    zones: list[Any], zone_moods: dict[str, str]
) -> list[MoodDistributionData]:
    if not zones:
        return []

    zone_by_id = {getattr(z, "zone_id", ""): z for z in zones}
    counts: dict[str, int] = {}
    total = 0
    for zone_id, zone_mood in zone_moods.items():
        if zone_id not in zone_by_id:
            continue
        if zone_mood is None:
            continue
        counts[zone_mood] = counts.get(zone_mood, 0) + 1
        total += 1

    if total == 0:
        return []

    results = [
        MoodDistributionData(
            mood=m,
            count=c,
            percentage=round((c / total) * 100, 2),
            zone_name=None,
        )
        for m, c in counts.items()
    ]
    results.sort(key=lambda i: i.count, reverse=True)
    return results
