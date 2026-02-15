"""AI Home CoPilot API Types.
Generated from OpenAPI spec v0.4.33
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ==================== Common ====================


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    code: Optional[str] = None


# ==================== Habitus ====================


class HabitusStatusStatistics(BaseModel):
    total_rules: int
    total_events: int
    last_mining_ms: Optional[int] = None


class HabitusStatusConfig(BaseModel):
    windows: list[int]
    min_support_A: float
    min_hits: int
    min_confidence: float
    min_lift: float
    max_rules: int


class HabitusStatus(BaseModel):
    status: str
    version: str
    statistics: HabitusStatusStatistics
    config: HabitusStatusConfig


class RuleEvidence(BaseModel):
    hit_examples: list[dict[str, Any]] = Field(default_factory=list)
    miss_examples: list[dict[str, Any]] = Field(default_factory=list)
    latency_quantiles: list[float] = Field(default_factory=list)


class Rule(BaseModel):
    A: str
    B: str
    dt_sec: float
    nA: int
    nB: int
    nAB: int
    confidence: float
    confidence_lb: float
    lift: float
    leverage: float
    score: float
    observation_period_days: Optional[float] = None
    created_at_ms: Optional[int] = None
    evidence: Optional[RuleEvidence] = None


class RulesResponse(BaseModel):
    status: str
    total_rules: int
    rules: list[Rule]


class MineRequest(BaseModel):
    events: list[dict[str, Any]]
    config: Optional[dict[str, Any]] = None


class TopRule(BaseModel):
    A: str
    B: str
    confidence: float
    lift: float
    dt_sec: float


class MineResponse(BaseModel):
    status: str
    mining_time_sec: float
    total_input_events: int
    discovered_rules: int
    top_rules: list[TopRule] = Field(default_factory=list)


class Zone(BaseModel):
    zone_id: str
    name: str
    entities: list[str] = Field(default_factory=list)


class ZonesResponse(BaseModel):
    status: str
    zones: list[Zone]


class DashboardCardsResponse(BaseModel):
    status: str
    cards: list[dict[str, Any]]


# ==================== Graph ====================


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    domain: Optional[str] = None
    score: Optional[float] = None


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    weight: float


class GraphState(BaseModel):
    status: str
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class GraphSyncRequest(BaseModel):
    entities: list[dict[str, Any]] = Field(default_factory=list)
    full_sync: bool = False


class GraphSyncResponse(BaseModel):
    status: str
    nodes_added: int
    nodes_updated: int
    nodes_removed: int
    edges_added: int


class PatternsResponse(BaseModel):
    status: str
    patterns: list[dict[str, Any]]


# ==================== Mood ====================


class MoodFactor(BaseModel):
    name: str
    value: float
    weight: float


class MoodData(BaseModel):
    score: float
    confidence: float
    factors: list[MoodFactor] = Field(default_factory=list)


class MoodResponse(BaseModel):
    status: str
    mood: MoodData
    zone_id: Optional[str] = None
    user_id: Optional[str] = None


# ==================== Neurons ====================


class NeuronState(BaseModel):
    name: str
    type: str
    state: dict[str, Any]
    config: Optional[dict[str, Any]] = None


class NeuronsListData(BaseModel):
    context: dict[str, Any]
    state: dict[str, Any]
    mood: dict[str, Any]
    total_count: int


class NeuronsListResponse(BaseModel):
    success: bool
    data: NeuronsListData


class NeuronEvaluateRequest(BaseModel):
    states: Optional[dict[str, Any]] = None
    context: Optional[dict[str, Any]] = None
    trigger: Optional[str] = None


class NeuronEvaluateData(BaseModel):
    timestamp: str
    context_values: dict[str, float]
    state_values: dict[str, float]
    mood_values: dict[str, float]
    dominant_mood: str
    mood_confidence: float
    suggestions: list[str]
    neuron_count: int


class NeuronEvaluateResponse(BaseModel):
    success: bool
    data: NeuronEvaluateData


# ==================== Tags ====================


class TagSource(str, Enum):
    MANUAL = "manual"
    INFERRED = "inferred"
    LEARNED = "learned"


class Tag(BaseModel):
    tag_id: str
    namespace: str
    facet: str
    key: str
    description: Optional[str] = None
    created_at: Optional[str] = None


class TagsResponse(BaseModel):
    status: str
    tags: list[Tag]


class TagCreate(BaseModel):
    tag_id: str
    description: Optional[str] = None


class TagAssignment(BaseModel):
    tag_id: str
    confidence: Optional[float] = None
    source: Optional[TagSource] = None


class SubjectTagsResponse(BaseModel):
    status: str
    subject_id: str
    tags: list[Tag]


# ==================== Events ====================


class EventIngest(BaseModel):
    type: str
    text: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    idempotency_key: Optional[str] = None
    timestamp: Optional[str] = None


class EventIngestResponse(BaseModel):
    ok: bool
    stored: bool
    deduped: bool
    event_id: Optional[str] = None


# ==================== Candidates ====================


class Candidate(BaseModel):
    candidate_id: str
    trigger: dict[str, Any]
    action: dict[str, Any]
    score: float
    source: str


class CandidatesResponse(BaseModel):
    status: str
    candidates: list[Candidate]


class CandidateStats(BaseModel):
    status: str
    total: int
    by_source: dict[str, int]
    by_domain: dict[str, int]


# ==================== Vector Store ====================


class VectorEntryType(str, Enum):
    ENTITY = "entity"
    USER_PREFERENCE = "user_preference"
    PATTERN = "pattern"


class VectorEntry(BaseModel):
    id: str
    type: VectorEntryType
    vector: list[float]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class VectorEmbeddingRequest(BaseModel):
    type: VectorEntryType
    id: str
    domain: Optional[str] = None
    area: Optional[str] = None
    capabilities: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    state: Optional[dict[str, Any]] = None
    preferences: Optional[dict[str, Any]] = None
    pattern_type: Optional[str] = None
    entities: Optional[list[str]] = None
    conditions: Optional[dict[str, Any]] = None
    confidence: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None


class VectorStats(BaseModel):
    total_vectors: int
    by_type: dict[str, int]
    dimension: int


class VectorStatsResponse(BaseModel):
    ok: bool
    stats: VectorStats


# ==================== System ====================


class SystemCheckStatus(str, Enum):
    OK = "ok"
    ERROR = "error"


class SystemChecks(BaseModel):
    api: SystemCheckStatus
    storage: SystemCheckStatus
    ha_connection: SystemCheckStatus


class SystemHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class SystemHealth(BaseModel):
    status: SystemHealthStatus
    checks: SystemChecks
    version: str
    uptime_seconds: int