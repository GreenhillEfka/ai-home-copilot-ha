"""HA Service Wiring for Pattern Proposal Engine."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant

from .generator import SuggestionGenerator
from .models import PatternObservation, SuggestionTrigger
from .store import ProposalStore

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)

_STORE_DIR = "pattern_proposal"


async def async_setup_pattern_proposal(hass: HomeAssistant) -> bool:
    """Set up the pattern proposal engine."""
    store = ProposalStore(hass.config.path(_STORE_DIR))
    gen = SuggestionGenerator(store)
    hass.data.setdefault("copilot_pattern_proposal", {})["store"] = store
    hass.data["copilot_pattern_proposal"]["generator"] = gen
    _LOGGER.info("Pattern proposal engine started")
    return True


async def async_record_observation(
    hass: HomeAssistant,
    zone_id: str,
    trigger: SuggestionTrigger,
    payload: dict,
    source_entity_id: str | None = None,
) -> None:
    """Record an observation for pattern analysis."""
    data = hass.data.get("copilot_pattern_proposal", {})
    store: ProposalStore | None = data.get("store")
    if not store:
        _LOGGER.warning("Pattern proposal store not initialized")
        return
    obs = PatternObservation(
        zone_id=zone_id,
        trigger=trigger,
        payload=payload,
        source_entity_id=source_entity_id,
    )
    store.record_observation(obs)
    # Invalidate cache for this zone
    gen: SuggestionGenerator | None = data.get("generator")
    if gen:
        gen.invalidate_cache(zone_id)
