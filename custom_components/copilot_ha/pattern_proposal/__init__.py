"""Pattern Proposal Engine.

Generates contextual suggestions from recurring zone patterns.
"""

from .generator import SuggestionGenerator
from .generator_protocol import SuggestionGeneratorProtocol
from .ha_service import async_record_observation, async_setup_pattern_proposal
from .matcher import PatternMatcher
from .models import (
    PatternObservation,
    SuggestionCandidate,
    SuggestionConfidence,
    SuggestionTrigger,
)
from .store import ProposalStore

__all__ = [
    "PatternMatcher",
    "PatternObservation",
    "ProposalStore",
    "SuggestionCandidate",
    "SuggestionConfidence",
    "SuggestionGenerator",
    "SuggestionGeneratorProtocol",
    "SuggestionTrigger",
    "async_record_observation",
    "async_setup_pattern_proposal",
]
