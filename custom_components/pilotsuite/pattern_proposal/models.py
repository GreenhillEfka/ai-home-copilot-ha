"""Pattern Proposal Models.

Defines Pydantic models for the pattern-based suggestion engine.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SuggestionConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SuggestionTrigger(str, Enum):
    TEMPERATURE_PATTERN = "temperature_pattern"
    ENERGY_SPIKE = "energy_spike"
    PRESENCE_ARRIVAL = "presence_arrival"
    PRESENCE_DEPARTURE = "presence_departure"
    WINDOW_OPEN_CLIMATE = "window_open_climate"
    MANUAL_REPEAT = "manual_repeat"
    ZONE_TRANSITION = "zone_transition"
    COVER_SUN_POSITION = "cover_sun_position"
    LIGHT_AMBIGUOUS = "light_ambiguous"


class PatternObservation(BaseModel):
    """A single observed event or sensor reading."""
    observation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    zone_id: str
    trigger: SuggestionTrigger
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = Field(default_factory=dict)
    source_entity_id: str | None = None


class SuggestionCandidate(BaseModel):
    """A generated suggestion ready for user review."""
    candidate_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    zone_id: str
    trigger: SuggestionTrigger
    confidence: SuggestionConfidence
    trigger_label: str
    suggestion_text: str
    suggested_action: dict[str, Any] = Field(default_factory=dict)
    observations: list[PatternObservation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accepted: bool | None = None
    dismissed: bool = False
