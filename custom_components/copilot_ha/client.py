"""PilotSuite Core API Client with Circuit Breaker Pattern.

Provides resilient communication between Home Assistant and PilotSuite Core.

Features:
- Circuit Breaker (Open/Half-Open/Closed states)
- Exponential Backoff with jitter
- Request timeout management
- Health monitoring + auto-recovery
- Connection pooling
- Request/response logging

Slice 143 — 168h Massive Iteration
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

import aiohttp

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout: float = 60.0
    request_timeout: float = 10.0
    max_retries: int = 3
    base_delay: float = 0.1
    max_delay: float = 10.0
    jitter: float = 0.1


@dataclass
class CircuitStats:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    state_transitions: int = 0
    avg_response_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "rejected_requests": self.rejected_requests,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "state_transitions": self.state_transitions,
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
        }


class CircuitBreakerOpen(Exception):
    def __init__(self, message: str = "Circuit breaker is open", retry_after: float = 0.0):
        super().__init__(message)
        self.retry_after = retry_after


class CircuitBreaker:
    def __init__(self, config: Optional[CircuitBreakerConfig] = None) -> None:
        self._config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._opened_at: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._opened_at >= self._config.timeout:
                return CircuitState.HALF_OPEN
        return self._state

    @property
    def stats(self) -> CircuitStats:
        return self._stats

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        async with self._lock:
            current_state = self.state
            self._stats.total_requests += 1

            if current_state == CircuitState.OPEN:
                self._stats.rejected_requests += 1
                retry_after = self._config.timeout - (time.time() - self._opened_at)
                raise CircuitBreakerOpen(
                    f"Circuit breaker open, retry after {retry_after:.1f}s",
                    retry_after=retry_after,
                )

        start_time = time.time()
        last_exception: Optional[Exception] = None

        for attempt in range(self._config.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                await self._on_success()
                response_time = (time.time() - start_time) * 1000
                self._update_avg_response_time(response_time)
                return result

            except Exception as exc:
                last_exception = exc
                await self._on_failure()

                if attempt < self._config.max_retries:
                    delay = self._calculate_backoff(attempt)
                    _LOGGER.debug("Retry %d/%d in %.2fs: %s", attempt + 1, self._config.max_retries + 1, delay, exc)
                    await asyncio.sleep(delay)

        if last_exception:
            raise last_exception

    async def _on_success(self) -> None:
        self._stats.successful_requests += 1
        self._stats.consecutive_successes += 1
        self._stats.consecutive_failures = 0
        self._stats.last_success_time = time.time()

        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                if self._stats.consecutive_successes >= self._config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._stats.state_transitions += 1
                    _LOGGER.info("Circuit breaker closed after recovery")

    async def _on_failure(self) -> None:
        self._stats.failed_requests += 1
        self._stats.consecutive_failures += 1
        self._stats.consecutive_successes = 0
        self._stats.last_failure_time = time.time()

        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._opened_at = time.time()
                self._stats.state_transitions += 1
                _LOGGER.warning("Circuit breaker opened after failure in half-open state")
            elif self._state == CircuitState.CLOSED:
                if self._stats.consecutive_failures >= self._config.failure_threshold:
                    self._state = CircuitState.OPEN
                    self._opened_at = time.time()
                    self._stats.state_transitions += 1
                    _LOGGER.warning("Circuit breaker opened after %d consecutive failures", self._stats.consecutive_failures)

    def _calculate_backoff(self, attempt: int) -> float:
        delay = min(self._config.base_delay * (2 ** attempt), self._config.max_delay)
        jitter_range = delay * self._config.jitter
        delay += random.uniform(-jitter_range, jitter_range)
        return max(0.0, delay)

    def _update_avg_response_time(self, response_time_ms: float) -> None:
        total = self._stats.successful_requests
        if total == 1:
            self._stats.avg_response_time_ms = response_time_ms
        else:
            self._stats.avg_response_time_ms = ((self._stats.avg_response_time_ms * (total - 1) + response_time_ms) / total)

    def reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._opened_at = 0.0
        _LOGGER.info("Circuit breaker reset")


@dataclass
class CoreClientConfig:
    core_url: str = "http://localhost:8123"
    api_token: str = ""
    timeout: float = 10.0
    circuit_breaker: Optional[CircuitBreakerConfig] = None


class PilotSuiteCoreClient:
    def __init__(self, config: Optional[CoreClientConfig] = None) -> None:
        self._config = config or CoreClientConfig()
        self._circuit_breaker = CircuitBreaker(self._config.circuit_breaker)
        self._session: Optional[aiohttp.ClientSession] = None
        self._base_url = self._config.core_url.rstrip("/")

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self._config.api_token}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=self._config.timeout),
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self._request("POST", path, json=json, data=data)

    async def put(self, path: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self._request("PUT", path, json=json)

    async def delete(self, path: str) -> Dict[str, Any]:
        return await self._request("DELETE", path)

    async def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async def _do_request() -> Dict[str, Any]:
            session = await self._get_session()
            url = f"{self._base_url}{path}"

            async with session.request(method, url, params=params, json=json, data=data) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    raise aiohttp.ClientResponseError(resp.request_info, resp.history, status=resp.status, message=body)
                return await resp.json()

        return await self._circuit_breaker.call(_do_request)

    async def get_zones(self) -> List[Dict[str, Any]]:
        return await self.get("/api/v1/zones")

    async def get_zone(self, zone_id: str) -> Dict[str, Any]:
        return await self.get(f"/api/v1/zones/{zone_id}")

    async def update_zone(self, zone_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.put(f"/api/v1/zones/{zone_id}", json=data)

    async def get_presence(self, zone_id: str) -> Dict[str, Any]:
        return await self.get(f"/api/v1/presence/{zone_id}")

    async def get_habitus(self, zone_id: str) -> Dict[str, Any]:
        return await self.get(f"/api/v1/habitus/{zone_id}")

    async def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self.post("/api/v1/actions/execute", json={"action": action, "params": params})

    async def search(self, query: str, namespace: str = "default", top_k: int = 5) -> List[Dict[str, Any]]:
        return await self.post("/api/v1/rag/search", json={"query": query, "namespace": namespace, "top_k": top_k})

    async def get_health(self) -> Dict[str, Any]:
        return await self.get("/api/v1/health")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "circuit_breaker": {
                "state": self._circuit_breaker.state.value,
                "stats": self._circuit_breaker.stats.to_dict(),
            },
            "config": {
                "core_url": self._config.core_url,
                "timeout": self._config.timeout,
            },
        }

    def reset_circuit(self) -> None:
        self._circuit_breaker.reset()


_client: Optional[PilotSuiteCoreClient] = None


def get_core_client(config: Optional[CoreClientConfig] = None) -> PilotSuiteCoreClient:
    global _client
    if _client is None:
        _client = PilotSuiteCoreClient(config)
    return _client
