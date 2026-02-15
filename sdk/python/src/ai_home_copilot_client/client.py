"""AI Home CoPilot Python Client."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import aiohttp

from .models import (
    CandidateStats,
    CandidatesResponse,
    DashboardCardsResponse,
    EventIngest,
    EventIngestResponse,
    GraphState,
    GraphSyncRequest,
    GraphSyncResponse,
    HabitusStatus,
    MineRequest,
    MineResponse,
    MoodResponse,
    NeuronEvaluateRequest,
    NeuronEvaluateResponse,
    NeuronsListResponse,
    PatternsResponse,
    RulesResponse,
    SubjectTagsResponse,
    SystemHealth,
    Tag,
    TagAssignment,
    TagCreate,
    TagsResponse,
    VectorEmbeddingRequest,
    VectorStatsResponse,
    ZonesResponse,
)


class CopilotError(Exception):
    """Base exception for Copilot client errors."""
    pass


class CopilotAuthError(CopilotError):
    """Authentication error."""
    pass


class CopilotNotFoundError(CopilotError):
    """Resource not found."""
    pass


class CopilotClient:
    """Async Python client for AI Home CoPilot Core API."""

    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
        headers: Optional[dict[str, str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._headers: dict[str, str] = {
            "Content-Type": "application/json",
            **(headers or {}),
        }
        if auth_token:
            self._headers["X-Auth-Token"] = auth_token
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "CopilotClient":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self._headers,
                timeout=self.timeout,
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(
        self,
        method: str,
        path: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        session = await self._ensure_session()
        url = f"{self.base_url}{path}"
        headers = {**self._headers, **(extra_headers or {})}

        try:
            async with session.request(
                method,
                url,
                json=data,
                params=params,
                headers=headers,
            ) as response:
                if response.status == 401:
                    raise CopilotAuthError("Authentication failed")
                if response.status == 404:
                    raise CopilotNotFoundError(f"Resource not found: {path}")

                response_data = await response.json()

                if response.status >= 400:
                    error_msg = response_data.get("message") or response_data.get("error") or str(response_data)
                    raise CopilotError(f"API error {response.status}: {error_msg}")

                return response_data

        except aiohttp.ClientError as e:
            raise CopilotError(f"Request failed: {e}") from e

    # ==================== Habitus API ====================

    class HabitusAPI:
        def __init__(self, client: "CopilotClient"):
            self._client = client

        async def get_status(self) -> HabitusStatus:
            data = await self._client._request("GET", "/api/v1/habitus/status")
            return HabitusStatus(**data)

        async def get_rules(
            self,
            limit: Optional[int] = None,
            min_score: Optional[float] = None,
            a_filter: Optional[str] = None,
            b_filter: Optional[str] = None,
            domain_filter: Optional[str] = None,
        ) -> RulesResponse:
            params = {}
            if limit is not None:
                params["limit"] = limit
            if min_score is not None:
                params["min_score"] = min_score
            if a_filter:
                params["a_filter"] = a_filter
            if b_filter:
                params["b_filter"] = b_filter
            if domain_filter:
                params["domain_filter"] = domain_filter

            data = await self._client._request("GET", "/api/v1/habitus/rules", params=params)
            return RulesResponse(**data)

        async def mine_rules(self, events: list[dict[str, Any]], config: Optional[dict[str, Any]] = None) -> MineResponse:
            request = MineRequest(events=events, config=config)
            data = await self._client._request("POST", "/api/v1/habitus/mine", data=request.model_dump(exclude_none=True))
            return MineResponse(**data)

        async def get_config(self) -> dict[str, Any]:
            return await self._client._request("GET", "/api/v1/habitus/config")

        async def update_config(self, config: dict[str, Any]) -> dict[str, Any]:
            return await self._client._request("POST", "/api/v1/habitus/config", data=config)

        async def reset(self) -> dict[str, Any]:
            return await self._client._request("POST", "/api/v1/habitus/reset")

        async def get_zones(self) -> ZonesResponse:
            data = await self._client._request("GET", "/api/v1/habitus/dashboard_cards/zones")
            return ZonesResponse(**data)

        async def get_dashboard_cards(self) -> DashboardCardsResponse:
            data = await self._client._request("GET", "/api/v1/habitus/dashboard_cards")
            return DashboardCardsResponse(**data)

    @property
    def habitus(self) -> HabitusAPI:
        return self.HabitusAPI(self)

    # ==================== Graph API ====================

    class GraphAPI:
        def __init__(self, client: "CopilotClient"):
            self._client = client

        async def get_state(self, max_nodes: Optional[int] = None, max_edges: Optional[int] = None) -> GraphState:
            params = {}
            if max_nodes is not None:
                params["max_nodes"] = max_nodes
            if max_edges is not None:
                params["max_edges"] = max_edges

            data = await self._client._request("GET", "/api/v1/graph/state", params=params)
            return GraphState(**data)

        async def sync(self, entities: list[dict[str, Any]], full_sync: bool = False) -> GraphSyncResponse:
            request = GraphSyncRequest(entities=entities, full_sync=full_sync)
            data = await self._client._request("POST", "/api/v1/graph/sync", data=request.model_dump())
            return GraphSyncResponse(**data)

        async def get_patterns(self) -> PatternsResponse:
            data = await self._client._request("GET", "/api/v1/graph/patterns")
            return PatternsResponse(**data)

        async def get_stats(self) -> dict[str, Any]:
            return await self._client._request("GET", "/api/v1/graph/stats")

    @property
    def graph(self) -> GraphAPI:
        return self.GraphAPI(self)

    # ==================== Neurons API ====================

    class NeuronsAPI:
        def __init__(self, client: "CopilotClient"):
            self._client = client

        async def list(self) -> NeuronsListResponse:
            data = await self._client._request("GET", "/api/v1/neurons")
            return NeuronsListResponse(**data)

        async def get(self, neuron_id: str) -> dict[str, Any]:
            return await self._client._request("GET", f"/api/v1/neurons/{neuron_id}")

        async def evaluate(
            self,
            states: Optional[dict[str, Any]] = None,
            context: Optional[dict[str, Any]] = None,
            trigger: Optional[str] = None,
        ) -> NeuronEvaluateResponse:
            request = NeuronEvaluateRequest(states=states, context=context, trigger=trigger)
            data = await self._client._request("POST", "/api/v1/neurons/evaluate", data=request.model_dump(exclude_none=True))
            return NeuronEvaluateResponse(**data)

        async def update_states(self, states: dict[str, Any]) -> dict[str, Any]:
            return await self._client._request("POST", "/api/v1/neurons/update", data={"states": states})

        async def get_mood(self, zone_id: Optional[str] = None, user_id: Optional[str] = None) -> MoodResponse:
            params = {}
            if zone_id:
                params["zone_id"] = zone_id
            if user_id:
                params["user_id"] = user_id

            data = await self._client._request("GET", "/api/v1/neurons/mood", params=params)
            return MoodResponse(**data)

        async def evaluate_mood(
            self,
            states: Optional[dict[str, Any]] = None,
            context: Optional[dict[str, Any]] = None,
        ) -> NeuronEvaluateResponse:
            request = NeuronEvaluateRequest(states=states, context=context)
            data = await self._client._request("POST", "/api/v1/neurons/mood/evaluate", data=request.model_dump(exclude_none=True))
            return NeuronEvaluateResponse(**data)

        async def get_mood_history(self, limit: Optional[int] = None) -> dict[str, Any]:
            params = {}
            if limit is not None:
                params["limit"] = limit
            return await self._client._request("GET", "/api/v1/neurons/mood/history", params=params)

        async def get_suggestions(self) -> dict[str, Any]:
            return await self._client._request("GET", "/api/v1/neurons/suggestions")

    @property
    def neurons(self) -> NeuronsAPI:
        return self.NeuronsAPI(self)

    # ==================== Tags API ====================

    class TagsAPI:
        def __init__(self, client: "CopilotClient"):
            self._client = client

        async def list(self) -> TagsResponse:
            data = await self._client._request("GET", "/api/v1/tags2/tags")
            return TagsResponse(**data)

        async def create(self, tag_id: str, description: Optional[str] = None) -> Tag:
            request = TagCreate(tag_id=tag_id, description=description)
            data = await self._client._request("POST", "/api/v1/tags2/tags", data=request.model_dump(exclude_none=True))
            return Tag(**data)

        async def get(self, tag_id: str) -> Tag:
            data = await self._client._request("GET", f"/api/v1/tags2/tags/{tag_id}")
            return Tag(**data)

        async def get_subject_tags(self, subject_id: str) -> SubjectTagsResponse:
            data = await self._client._request("GET", f"/api/v1/tags2/subjects/{subject_id}/tags")
            return SubjectTagsResponse(**data)

        async def assign_tag(
            self,
            subject_id: str,
            tag_id: str,
            confidence: Optional[float] = None,
            source: Optional[str] = None,
        ) -> dict[str, Any]:
            assignment = TagAssignment(tag_id=tag_id, confidence=confidence, source=source)
            return await self._client._request(
                "POST",
                f"/api/v1/tags2/subjects/{subject_id}/tags",
                data=assignment.model_dump(exclude_none=True),
            )

        async def get_assignments(self) -> dict[str, Any]:
            return await self._client._request("GET", "/api/v1/tags2/assignments")

        async def create_assignment(
            self,
            subject_id: str,
            tag_id: str,
            confidence: Optional[float] = None,
            source: Optional[str] = None,
        ) -> dict[str, Any]:
            assignment = TagAssignment(tag_id=tag_id, confidence=confidence, source=source)
            return await self._client._request(
                "POST",
                "/api/v1/tags2/assignments",
                data={"subject_id": subject_id, **assignment.model_dump(exclude_none=True)},
            )

    @property
    def tags(self) -> TagsAPI:
        return self.TagsAPI(self)

    # ==================== Events API ====================

    class EventsAPI:
        def __init__(self, client: "CopilotClient"):
            self._client = client

        async def ingest(
            self,
            event_type: str,
            text: Optional[str] = None,
            payload: Optional[dict[str, Any]] = None,
            idempotency_key: Optional[str] = None,
            timestamp: Optional[str] = None,
        ) -> EventIngestResponse:
            event = EventIngest(
                type=event_type,
                text=text,
                payload=payload,
                idempotency_key=idempotency_key,
                timestamp=timestamp,
            )
            extra_headers = {}
            if idempotency_key:
                extra_headers["Idempotency-Key"] = idempotency_key

            data = await self._client._request(
                "POST",
                "/api/v1/events",
                data=event.model_dump(exclude_none=True),
                extra_headers=extra_headers if extra_headers else None,
            )
            return EventIngestResponse(**data)

        async def list(self, limit: Optional[int] = None, event_type: Optional[str] = None) -> dict[str, Any]:
            params = {}
            if limit is not None:
                params["limit"] = limit
            if event_type:
                params["type"] = event_type
            return await self._client._request("GET", "/api/v1/events", params=params)

        async def get_stats(self) -> dict[str, Any]:
            return await self._client._request("GET", "/api/v1/events/stats")

    @property
    def events(self) -> EventsAPI:
        return self.EventsAPI(self)

    # ==================== Candidates API ====================

    class CandidatesAPI:
        def __init__(self, client: "CopilotClient"):
            self._client = client

        async def list(self, min_score: Optional[float] = None, limit: Optional[int] = None) -> CandidatesResponse:
            params = {}
            if min_score is not None:
                params["min_score"] = min_score
            if limit is not None:
                params["limit"] = limit

            data = await self._client._request("GET", "/api/v1/candidates", params=params)
            return CandidatesResponse(**data)

        async def get(self, candidate_id: str) -> dict[str, Any]:
            return await self._client._request("GET", f"/api/v1/candidates/{candidate_id}")

        async def delete(self, candidate_id: str) -> dict[str, Any]:
            return await self._client._request("DELETE", f"/api/v1/candidates/{candidate_id}")

        async def get_stats(self) -> CandidateStats:
            data = await self._client._request("GET", "/api/v1/candidates/stats")
            return CandidateStats(**data)

        async def get_graph_candidates(self) -> dict[str, Any]:
            return await self._client._request("GET", "/api/v1/candidates/graph_candidates")

    @property
    def candidates(self) -> CandidatesAPI:
        return self.CandidatesAPI(self)

    # ==================== Vector API ====================

    class VectorAPI:
        def __init__(self, client: "CopilotClient"):
            self._client = client

        async def create_embedding(self, **kwargs) -> dict[str, Any]:
            request = VectorEmbeddingRequest(**kwargs)
            return await self._client._request(
                "POST",
                "/api/v1/vector/embeddings",
                data=request.model_dump(exclude_none=True),
            )

        async def create_embeddings_bulk(
            self,
            entities: Optional[list[dict[str, Any]]] = None,
            user_preferences: Optional[list[dict[str, Any]]] = None,
            patterns: Optional[list[dict[str, Any]]] = None,
        ) -> dict[str, Any]:
            data = {}
            if entities:
                data["entities"] = entities
            if user_preferences:
                data["user_preferences"] = user_preferences
            if patterns:
                data["patterns"] = patterns
            return await self._client._request("POST", "/api/v1/vector/embeddings/bulk", data=data)

        async def find_similar(
            self,
            entry_id: str,
            entry_type: Optional[str] = None,
            limit: Optional[int] = None,
            threshold: Optional[float] = None,
        ) -> dict[str, Any]:
            params = {}
            if entry_type:
                params["type"] = entry_type
            if limit is not None:
                params["limit"] = limit
            if threshold is not None:
                params["threshold"] = threshold
            return await self._client._request("GET", f"/api/v1/vector/similar/{entry_id}", params=params)

        async def list(self, entry_type: Optional[str] = None, limit: Optional[int] = None) -> dict[str, Any]:
            params = {}
            if entry_type:
                params["type"] = entry_type
            if limit is not None:
                params["limit"] = limit
            return await self._client._request("GET", "/api/v1/vector/vectors", params=params)

        async def get(self, entry_id: str) -> dict[str, Any]:
            return await self._client._request("GET", f"/api/v1/vector/vectors/{entry_id}")

        async def delete(self, entry_id: str) -> dict[str, Any]:
            return await self._client._request("DELETE", f"/api/v1/vector/vectors/{entry_id}")

        async def clear(self, entry_type: Optional[str] = None) -> dict[str, Any]:
            params = {}
            if entry_type:
                params["type"] = entry_type
            return await self._client._request("DELETE", "/api/v1/vector/vectors", params=params)

        async def get_stats(self) -> VectorStatsResponse:
            data = await self._client._request("GET", "/api/v1/vector/stats")
            return VectorStatsResponse(**data)

        async def compute_similarity(
            self,
            id1: Optional[str] = None,
            id2: Optional[str] = None,
            vector1: Optional[list[float]] = None,
            vector2: Optional[list[float]] = None,
        ) -> dict[str, Any]:
            data = {}
            if id1:
                data["id1"] = id1
            if id2:
                data["id2"] = id2
            if vector1:
                data["vector1"] = vector1
            if vector2:
                data["vector2"] = vector2
            return await self._client._request("POST", "/api/v1/vector/similarity", data=data)

    @property
    def vector(self) -> VectorAPI:
        return self.VectorAPI(self)

    # ==================== System API ====================

    async def health(self) -> SystemHealth:
        data = await self._request("GET", "/health")
        return SystemHealth(**data)

    async def version(self) -> dict[str, Any]:
        return await self._request("GET", "/version")


__all__ = [
    "CopilotClient",
    "CopilotError",
    "CopilotAuthError",
    "CopilotNotFoundError",
]