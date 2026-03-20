"""Pattern Proposal Matcher.

Detects recurring patterns from observations and generates candidate suggestions.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from .models import (
    PatternObservation,
    SuggestionCandidate,
    SuggestionConfidence,
    SuggestionTrigger,
)

if TYPE_CHECKING:
    from .store import ProposalStore


_HOUR_BUCKETS = list(range(24))

# Default thresholds per trigger type
_DEFAULTS = {
    SuggestionTrigger.TEMPERATURE_PATTERN: {"min_occurrences": 3, "confidence": SuggestionConfidence.MEDIUM},
    SuggestionTrigger.ENERGY_SPIKE: {"min_occurrences": 2, "confidence": SuggestionConfidence.HIGH},
    SuggestionTrigger.PRESENCE_ARRIVAL: {"min_occurrences": 2, "confidence": SuggestionConfidence.MEDIUM},
    SuggestionTrigger.PRESENCE_DEPARTURE: {"min_occurrences": 2, "confidence": SuggestionConfidence.MEDIUM},
    SuggestionTrigger.WINDOW_OPEN_CLIMATE: {"min_occurrences": 2, "confidence": SuggestionConfidence.LOW},
    SuggestionTrigger.MANUAL_REPEAT: {"min_occurrences": 3, "confidence": SuggestionConfidence.HIGH},
    SuggestionTrigger.ZONE_TRANSITION: {"min_occurrences": 3, "confidence": SuggestionConfidence.MEDIUM},
    SuggestionTrigger.COVER_SUN_POSITION: {"min_occurrences": 2, "confidence": SuggestionConfidence.HIGH},
    SuggestionTrigger.LIGHT_AMBIGUOUS: {"min_occurrences": 2, "confidence": SuggestionConfidence.LOW},
}


class PatternMatcher:
    """Finds recurring patterns in zone observations."""

    def __init__(self, store: ProposalStore) -> None:
        self._store = store

    def match(
        self,
        zone_id: str,
        trigger: SuggestionTrigger,
        max_age: timedelta = timedelta(days=7),
    ) -> list[SuggestionCandidate]:
        """Find patterns for a zone+trigger combination."""
        since = datetime.utcnow() - max_age
        obs = self._store.get_observations(zone_id, trigger.value, since)

        if not obs:
            return []

        if trigger == SuggestionTrigger.TEMPERATURE_PATTERN:
            return self._match_temperature(zone_id, obs)
        if trigger == SuggestionTrigger.ENERGY_SPIKE:
            return self._match_energy_spike(zone_id, obs)
        if trigger in (SuggestionTrigger.PRESENCE_ARRIVAL, SuggestionTrigger.PRESENCE_DEPARTURE):
            return self._match_presence(zone_id, obs, trigger)
        if trigger == SuggestionTrigger.MANUAL_REPEAT:
            return self._match_manual_repeat(zone_id, obs)
        if trigger == SuggestionTrigger.WINDOW_OPEN_CLIMATE:
            return self._match_window_open(zone_id, obs)
        return []

    # ── Match strategies ──────────────────────────────────────────────────────

    def _match_temperature(self, zone_id: str, obs: list[PatternObservation]) -> list[SuggestionCandidate]:
        """Group observations by hour bucket, find consistent low temps."""
        hour_groups: dict[int, list[PatternObservation]] = defaultdict(list)
        for o in obs:
            hour_groups[o.timestamp.hour].append(o)

        candidates: list[SuggestionCandidate] = []
        for hour, group in hour_groups.items():
            if len(group) < 3:
                continue
            temps = [o.payload.get("temperature", 20.0) for o in group]
            avg = sum(temps) / len(temps)
            if avg < 19.0:
                candidates.append(
                    SuggestionCandidate(
                        zone_id=zone_id,
                        trigger=SuggestionTrigger.TEMPERATURE_PATTERN,
                        confidence=SuggestionConfidence.MEDIUM,
                        trigger_label=f"Temperatur um {hour:02d}:00",
                        suggestion_text=f"In diesem Raum ist es um {hour:02d}:00 oft kalt ({avg:.1f}°C). Heizung auf 20°C vorschlagen?",
                        suggested_action={"entity_id": group[0].payload.get("climate_entity"), "temperature": 20.0},
                        observations=group,
                    )
                )
        return candidates

    def _match_energy_spike(self, zone_id: str, obs: list[PatternObservation]) -> list[SuggestionCandidate]:
        """Find energy consumption spikes."""
        if len(obs) < 2:
            return []
        powers = [o.payload.get("power_w", 0) for o in obs]
        avg = sum(powers) / len(powers)
        spikes = [o for o in obs if o.payload.get("power_w", 0) > avg * 1.5]
        if len(spikes) >= 2:
            return [
                SuggestionCandidate(
                    zone_id=zone_id,
                    trigger=SuggestionTrigger.ENERGY_SPIKE,
                    confidence=SuggestionConfidence.HIGH,
                    trigger_label="Energiespitzen",
                    suggestion_text="Mehrfach hoher Energieverbrauch erkannt. Verbraucher prüfen?",
                    suggested_action={"zone_id": zone_id, "action": "investigate"},
                    observations=spikes,
                )
            ]
        return []

    def _match_presence(
        self, zone_id: str, obs: list[PatternObservation], trigger: SuggestionTrigger
    ) -> list[SuggestionCandidate]:
        """Group arrivals/departures by hour."""
        hour_groups: dict[int, list[PatternObservation]] = defaultdict(list)
        for o in obs:
            hour_groups[o.timestamp.hour].append(o)
        candidates: list[SuggestionCandidate] = []
        for hour, group in hour_groups.items():
            if len(group) >= 2:
                label = "Ankunft" if trigger == SuggestionTrigger.PRESENCE_ARRIVAL else "Abwesenheit"
                candidates.append(
                    SuggestionCandidate(
                        zone_id=zone_id,
                        trigger=trigger,
                        confidence=SuggestionConfidence.MEDIUM,
                        trigger_label=f"{label} um {hour:02d}:00",
                        suggestion_text=f"Regelmässige {label.lower()} um {hour:02d}:00 erkannt.",
                        suggested_action={"zone_id": zone_id, "hour": hour},
                        observations=group,
                    )
                )
        return candidates

    def _match_manual_repeat(self, zone_id: str, obs: list[PatternObservation]) -> list[SuggestionCandidate]:
        """Detect manual actions repeated at similar times."""
        hour_groups: dict[int, list[PatternObservation]] = defaultdict(list)
        for o in obs:
            hour_groups[o.timestamp.hour].append(o)
        candidates: list[SuggestionCandidate] = []
        for hour, group in hour_groups.items():
            if len(group) >= 3:
                entity = group[0].payload.get("entity_id", "unbekannt")
                candidates.append(
                    SuggestionCandidate(
                        zone_id=zone_id,
                        trigger=SuggestionTrigger.MANUAL_REPEAT,
                        confidence=SuggestionConfidence.HIGH,
                        trigger_label=f"Wiederholte Aktion um {hour:02d}:00",
                        suggestion_text=f"Aktion an {entity} wird regelmässig um {hour:02d}:00 ausgeführt. Automatisieren?",
                        suggested_action={"entity_id": entity, "hour": hour},
                        observations=group,
                    )
                )
        return candidates

    def _match_window_open(self, zone_id: str, obs: list[PatternObservation]) -> list[SuggestionCandidate]:
        """Detect repeated window-open-while-heating events."""
        if len(obs) < 2:
            return []
        return [
            SuggestionCandidate(
                zone_id=zone_id,
                trigger=SuggestionTrigger.WINDOW_OPEN_CLIMATE,
                confidence=SuggestionConfidence.LOW,
                trigger_label="Fenster offen bei Heizung",
                suggestion_text="Fenster wird häufig bei aktiver Heizung geöffnet. Automatische Heizungsreduzierung?",
                suggested_action={"zone_id": zone_id, "action": "reduce_heating_on_window_open"},
                observations=obs,
            )
        ]
