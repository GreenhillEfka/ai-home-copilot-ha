"""Protocol for SuggestionGenerator — enables DI and mocking."""

from typing import Protocol

from .models import SuggestionCandidate, SuggestionTrigger


class SuggestionGeneratorProtocol(Protocol):
    """Interface for suggestion generation."""

    def generate_for_zone(
        self,
        zone_id: str,
        triggers: frozenset[SuggestionTrigger] | None = None,
    ) -> list[SuggestionCandidate]:
        """Generate suggestion candidates for a zone."""

    def generate_all(
        self,
        zone_ids: list[str],
        triggers: frozenset[SuggestionTrigger] | None = None,
    ) -> list[SuggestionCandidate]:
        """Generate for multiple zones."""

    def invalidate_cache(self, zone_id: str | None = None) -> None:
        """Invalidate cache."""
