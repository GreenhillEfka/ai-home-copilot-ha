"""Neural Cross-Dependency Sensor for PilotSuite HA Integration.

Analyzes and exposes neural cross-dependencies between automation entities,
zones, and brain graph nodes. Shows which entities influence each other
across different domains and layers.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

import aiohttp

logger = logging.getLogger(__name__)


class CrossDependencySensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing neural cross-dependencies between entities and zones."""

    _attr_name = "Neural Cross-Dependencies"
    _attr_icon = "mdi:transit-connection-variant"
    _attr_unique_id = "pilotsuite_neural_cross_dependencies"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}
        self._graph_data: dict[str, Any] = {}

    async def _fetch_graph(self) -> dict | None:
        try:
            url = f"{self._core_base_url()}/api/v1/graph/state?limitNodes=200&limitEdges=400"
            headers = self._core_headers()
            session = async_get_clientsession(self.hass)
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            logger.debug("Failed to fetch graph state for cross-dependencies")
        return None

    async def _fetch_suggestions(self) -> dict | None:
        try:
            url = f"{self._core_base_url()}/api/v1/suggestions/repairs"
            headers = self._core_headers()
            session = async_get_clientsession(self.hass)
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            logger.debug("Failed to fetch repair suggestions")
        return None

    async def async_update(self) -> None:
        graph = await self._fetch_graph()
        if graph:
            self._graph_data = graph

        suggestions = await self._fetch_suggestions()
        if suggestions and suggestions.get("ok"):
            self._data["repairs"] = suggestions

        # Analyze cross-dependencies from graph data
        self._analyze_cross_deps()

    def _analyze_cross_deps(self) -> None:
        """Analyze cross-dependencies from graph nodes and edges."""
        nodes = self._graph_data.get("nodes", []) if isinstance(self._graph_data, dict) else []
        edges = self._graph_data.get("edges", []) if isinstance(self._graph_data, dict) else []

        if not nodes or not edges:
            return

        # Build domain lookup
        node_domains: dict[str, str] = {}
        node_zones: dict[str, str] = {}
        for n in nodes:
            if not isinstance(n, dict):
                continue
            nid = n.get("id", "")
            domain = n.get("domain", "")
            zone = n.get("zone", "")
            if nid:
                node_domains[nid] = domain
                if zone:
                    node_zones[nid] = zone

        # Identify cross-domain edges
        cross_domain: list[dict[str, str]] = []
        cross_zone: list[dict[str, str]] = []
        domain_pairs: dict[str, int] = {}

        for e in edges:
            if not isinstance(e, dict):
                continue
            frm = e.get("from", "")
            to = e.get("to", "")
            if not frm or not to:
                continue

            frm_domain = node_domains.get(frm, "")
            to_domain = node_domains.get(to, "")
            frm_zone = node_zones.get(frm, "")
            to_zone = node_zones.get(to, "")

            if frm_domain and to_domain and frm_domain != to_domain:
                cross_domain.append({
                    "from": frm,
                    "to": to,
                    "from_domain": frm_domain,
                    "to_domain": to_domain,
                })
                pair_key = f"{min(frm_domain, to_domain)}<->{max(frm_domain, to_domain)}"
                domain_pairs[pair_key] = domain_pairs.get(pair_key, 0) + 1

            if frm_zone and to_zone and frm_zone != to_zone:
                cross_zone.append({
                    "from": frm,
                    "to": to,
                    "from_zone": frm_zone,
                    "to_zone": to_zone,
                })

        self._data["cross_domain_count"] = len(cross_domain)
        self._data["cross_zone_count"] = len(cross_zone)
        self._data["domain_pairs"] = domain_pairs
        self._data["top_cross_domain"] = cross_domain[:10]
        self._data["top_cross_zone"] = cross_zone[:10]
        self._data["total_nodes"] = len(nodes)
        self._data["total_edges"] = len(edges)

    @property
    def native_value(self) -> str:
        cd = self._data.get("cross_domain_count", 0)
        cz = self._data.get("cross_zone_count", 0)
        if cd == 0 and cz == 0:
            return "Keine Daten"
        return f"{cd} Domain / {cz} Zone Cross-Deps"

    @property
    def icon(self) -> str:
        cd = self._data.get("cross_domain_count", 0)
        if cd > 20:
            return "mdi:transit-connection-variant"
        if cd > 5:
            return "mdi:vector-link"
        return "mdi:link-variant"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {
            "cross_domain_count": self._data.get("cross_domain_count", 0),
            "cross_zone_count": self._data.get("cross_zone_count", 0),
            "total_nodes": self._data.get("total_nodes", 0),
            "total_edges": self._data.get("total_edges", 0),
        }

        domain_pairs = self._data.get("domain_pairs", {})
        if domain_pairs:
            # Sort by count descending
            sorted_pairs = sorted(domain_pairs.items(), key=lambda x: x[1], reverse=True)
            attrs["domain_pair_ranking"] = [
                {"pair": pair, "count": count}
                for pair, count in sorted_pairs[:10]
            ]

        top_cd = self._data.get("top_cross_domain", [])
        if top_cd:
            attrs["top_cross_domain_edges"] = top_cd

        top_cz = self._data.get("top_cross_zone", [])
        if top_cz:
            attrs["top_cross_zone_edges"] = top_cz

        repairs = self._data.get("repairs", {})
        if repairs:
            attrs["repair_suggestion_count"] = repairs.get("count", 0)
            attrs["total_potential_savings_eur"] = repairs.get("total_potential_savings_eur", 0)
            cats = repairs.get("categories", {})
            if cats:
                attrs["repair_categories"] = cats

        return attrs
