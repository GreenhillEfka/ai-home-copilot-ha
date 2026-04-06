"""Conflict-Aware HTTP Client Mixin — Q2 Patch.

Provides automatic retry-on-409 conflict resolution:
1. On 409 → re-fetch current state from the conflicting endpoint
2. Re-apply the update with fresh version data
3. Repeat until success or max_retries

Use as mixin with any aiohttp-session-based client.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import aiohttp

_LOGGER = logging.getLogger(__name__)

MAX_CONFLICT_RETRIES = 3


class ConflictAwareClient:
    """Mixin that adds automatic 409-conflict retry to an aiohttp client.

    Requires the subclass to provide:
        _session: aiohttp.ClientSession
        _core_url: str
    """

    async def _fetch_fresh_state(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Fetch fresh state after a 409 conflict."""
        try:
            import aiohttp
            url = f"{self._core_url}{endpoint}"
            async with self._session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                _LOGGER.warning("Fresh fetch of %s returned %s", endpoint, resp.status)
                return None
        except Exception as e:
            _LOGGER.warning("Fresh fetch failed for %s: %s", endpoint, e)
            return None

    async def _post_json_retry(
        self,
        endpoint: str,
        data: Dict[str, Any],
        *,
        fresh_fetch_endpoint: Optional[str] = None,
        merge_fn: Optional[Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = None,
        max_retries: int = MAX_CONFLICT_RETRIES,
    ) -> Dict[str, Any]:
        """POST with automatic 409-conflict retry.

        Args:
            endpoint: Target API endpoint (e.g. "/api/v1/kg/nodes/{id}")
            data: Payload to POST
            fresh_fetch_endpoint: If given, fetch fresh state from this endpoint
                                  after a 409 before retrying.
            merge_fn: Optional function(local_data, fresh_data) → merged_data.
                      If not given, fresh_data replaces local_data.
            max_retries: Maximum retry attempts (default 3).
        """
        import aiohttp

        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                url = f"{self._core_url}{endpoint}"
                async with self._session.post(url, json=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    if resp.status == 409:
                        _LOGGER.info(
                            "409 Conflict on %s (attempt %d/%d) — fetching fresh state",
                            endpoint, attempt + 1, max_retries
                        )
                        if fresh_fetch_endpoint:
                            fresh = await self._fetch_fresh_state(fresh_fetch_endpoint)
                            if fresh is not None:
                                if merge_fn:
                                    data = merge_fn(data, fresh)
                                else:
                                    data = fresh
                            else:
                                _LOGGER.warning(
                                    "Could not fetch fresh state for conflict resolution"
                                )
                        continue
                    # Non-409 error
                    text = await resp.text()
                    raise aiohttp.ClientResponseError(
                        resp.request_info, resp.history,
                        status=resp.status, message=text
                    )
            except aiohttp.ClientError as e:
                last_error = e
                _LOGGER.debug("Request failed (attempt %d): %s", attempt + 1, e)
                if attempt == max_retries - 1:
                    break
                import asyncio
                await asyncio.sleep(0.2 * (attempt + 1))

        # All retries exhausted
        raise last_error or RuntimeError(
            f"_post_json_retry failed after {max_retries} attempts"
        )

    async def _put_json_retry(
        self,
        endpoint: str,
        data: Dict[str, Any],
        *,
        fresh_fetch_endpoint: Optional[str] = None,
        merge_fn: Optional[Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = None,
        max_retries: int = MAX_CONFLICT_RETRIES,
    ) -> Dict[str, Any]:
        """PUT with automatic 409-conflict retry. Same semantics as _post_json_retry."""
        import aiohttp

        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                url = f"{self._core_url}{endpoint}"
                async with self._session.put(url, json=data) as resp:
                    if resp.status in (200, 201):
                        return await resp.json()
                    if resp.status == 409:
                        _LOGGER.info(
                            "409 Conflict on PUT %s (attempt %d/%d) — fetching fresh state",
                            endpoint, attempt + 1, max_retries
                        )
                        if fresh_fetch_endpoint:
                            fresh = await self._fetch_fresh_state(fresh_fetch_endpoint)
                            if fresh is not None:
                                if merge_fn:
                                    data = merge_fn(data, fresh)
                                else:
                                    data = fresh
                        continue
                    text = await resp.text()
                    raise aiohttp.ClientResponseError(
                        resp.request_info, resp.history,
                        status=resp.status, message=text
                    )
            except aiohttp.ClientError as e:
                last_error = e
                if attempt == max_retries - 1:
                    break
                import asyncio
                await asyncio.sleep(0.2 * (attempt + 1))

        raise last_error or RuntimeError(
            f"_put_json_retry failed after {max_retries} attempts"
        )

    async def _patch_json_retry(
        self,
        endpoint: str,
        data: Dict[str, Any],
        *,
        max_retries: int = MAX_CONFLICT_RETRIES,
    ) -> Dict[str, Any]:
        """PATCH with 409-conflict retry using If-Match/If-Unmodified-Since."""
        import aiohttp

        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                url = f"{self._core_url}{endpoint}"
                headers = {}
                if attempt > 0:
                    # Re-fetch etag on retry
                    async with self._session.get(url) as etag_resp:
                        if etag_resp.status == 200:
                            etag = etag_resp.headers.get("ETag") or etag_resp.headers.get("etag")
                            if etag:
                                headers["If-Match"] = etag

                async with self._session.patch(url, json=data, headers=headers) as resp:
                    if resp.status in (200, 201):
                        return await resp.json()
                    if resp.status == 409:
                        _LOGGER.info(
                            "409 Conflict on PATCH %s (attempt %d/%d) — retrying with fresh ETag",
                            endpoint, attempt + 1, max_retries
                        )
                        continue
                    text = await resp.text()
                    raise aiohttp.ClientResponseError(
                        resp.request_info, resp.history,
                        status=resp.status, message=text
                    )
            except aiohttp.ClientError as e:
                last_error = e
                if attempt == max_retries - 1:
                    break
                import asyncio
                await asyncio.sleep(0.2 * (attempt + 1))

        raise last_error or RuntimeError(
            f"_patch_json_retry failed after {max_retries} attempts"
        )
