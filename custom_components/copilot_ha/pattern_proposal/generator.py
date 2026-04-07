"""Suggestion Generator.

High-level API for generating suggestion candidates from zone observations.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from .generator_protocol import SuggestionGeneratorProtocol
from .matcher import PatternMatcher
from .models import SuggestionCandidate, SuggestionTrigger
from .store import ProposalStore

if TYPE_CHECKING:
    from typing import FrozenSet

_LOGGER = logging.getLogger(__name__)

_CACHE_TTL = timedelta(minutes=5)


class SuggestionGenerator:
    """Generates and caches suggestion candidates for all zones."""

    def __init__(self, store: ProposalStore) -> None:
        self._store = store
        self._matcher = PatternMatcher(store)
        self._cache: dict[str, tuple[datetime, list[SuggestionCandidate]]] = {}

    def generate_for_zone(
        self,
        zone_id: str,
        triggers: FrozenSet[SuggestionTrigger] | None = None,
    ) -> list[SuggestionCandidate]:
        """Generate suggestion candidates for a zone, using cache if fresh."""
        cache_key = zone_id
        if cache_key in self._cache:
            ts, candidates = self._cache[cache_key]
            if datetime.utcnow() - ts < _CACHE_TTL:
                _LOGGER.debug("Cache hit for zone %s", zone_id)
                return candidates

        triggers = triggers or frozenset(SuggestionTrigger)
        all_candidates: list[SuggestionCandidate] = []
        seen_actions: set[tuple[str, str]] = set()

        for trigger in triggers:
            cands = self._matcher.match(zone_id, trigger)
            for c in cands:
                key = (zone_id, c.suggested_action.get("entity_id", ""), c.trigger.value)
                if key not in seen_actions:
                    seen_actions.add(key)
                    all_candidates.append(c)

        # Sort: HIGH > MEDIUM > LOW, then by created_at desc
        all_candidates.sort(
            key=lambda c: (
                -["high", "medium", "low"].index(c.confidence.value),
                -c.created_at.timestamp(),
            )
        )
        self._cache[cache_key] = (datetime.utcnow(), all_candidates)
        return all_candidates

    def generate_all(
        self,
        zone_ids: list[str],
        triggers: FrozenSet[SuggestionTrigger] | None = None,
    ) -> list[SuggestionCandidate]:
        """Generate for multiple zones, deduplicated."""
        all_candidates: list[SuggestionCandidate] = []
        seen: set[str] = set()
        for zone_id in zone_ids:
            for c in self.generate_for_zone(zone_id, triggers):
                if c.candidate_id not in seen:
                    seen.add(c.candidate_id)
                    all_candidates.append(c)
        return all_candidates

    def invalidate_cache(self, zone_id: str | None = None) -> None:
        """Invalidate cache for a specific zone or all."""
        if zone_id:
            self._cache.pop(zone_id, None)
        else:
            self._cache.clear()
