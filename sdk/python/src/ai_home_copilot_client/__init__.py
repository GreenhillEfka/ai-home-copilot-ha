"""PilotSuite Python SDK.
Version: 0.4.33
"""

from .client import CopilotClient, CopilotError, CopilotAuthError, CopilotNotFoundError
from .models import (
    # Common
    ErrorResponse,
    # Habitus
    HabitusStatus,
    HabitusStatusStatistics,
    HabitusStatusConfig,
    Rule,
    RuleEvidence,
    RulesResponse,
    MineRequest,
    MineResponse,
    TopRule,
    Zone,
    ZonesResponse,
    DashboardCardsResponse,
    # Graph
    GraphNode,
    GraphEdge,
    GraphState,
    GraphSyncRequest,
    GraphSyncResponse,
    PatternsResponse,
    # Mood
    MoodFactor,
    MoodData,
    MoodResponse,
    # Neurons
    NeuronState,
    NeuronsListData,
    NeuronsListResponse,
    NeuronEvaluateRequest,
    NeuronEvaluateData,
    NeuronEvaluateResponse,
    # Tags
    TagSource,
    Tag,
    TagsResponse,
    TagCreate,
    TagAssignment,
    SubjectTagsResponse,
    # Events
    EventIngest,
    EventIngestResponse,
    # Candidates
    Candidate,
    CandidatesResponse,
    CandidateStats,
    # Vector
    VectorEntryType,
    VectorEntry,
    VectorEmbeddingRequest,
    VectorStats,
    VectorStatsResponse,
    # System
    SystemCheckStatus,
    SystemChecks,
    SystemHealthStatus,
    SystemHealth,
)

__version__ = "0.4.33"

__all__ = [
    # Client
    "CopilotClient",
    "CopilotError",
    "CopilotAuthError",
    "CopilotNotFoundError",
    # Common
    "ErrorResponse",
    # Habitus
    "HabitusStatus",
    "HabitusStatusStatistics",
    "HabitusStatusConfig",
    "Rule",
    "RuleEvidence",
    "RulesResponse",
    "MineRequest",
    "MineResponse",
    "TopRule",
    "Zone",
    "ZonesResponse",
    "DashboardCardsResponse",
    # Graph
    "GraphNode",
    "GraphEdge",
    "GraphState",
    "GraphSyncRequest",
    "GraphSyncResponse",
    "PatternsResponse",
    # Mood
    "MoodFactor",
    "MoodData",
    "MoodResponse",
    # Neurons
    "NeuronState",
    "NeuronsListData",
    "NeuronsListResponse",
    "NeuronEvaluateRequest",
    "NeuronEvaluateData",
    "NeuronEvaluateResponse",
    # Tags
    "TagSource",
    "Tag",
    "TagsResponse",
    "TagCreate",
    "TagAssignment",
    "SubjectTagsResponse",
    # Events
    "EventIngest",
    "EventIngestResponse",
    # Candidates
    "Candidate",
    "CandidatesResponse",
    "CandidateStats",
    # Vector
    "VectorEntryType",
    "VectorEntry",
    "VectorEmbeddingRequest",
    "VectorStats",
    "VectorStatsResponse",
    # System
    "SystemCheckStatus",
    "SystemChecks",
    "SystemHealthStatus",
    "SystemHealth",
]