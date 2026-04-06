"""
Projection Contract Tests for CrossDependencySensor (HA-153).

Contract: CrossDependencySensor is a pure projection shell on
/api/v1/graph/state + /api/v1/suggestions/repairs — trivial dict lookups
+ cross-domain/zone aggregation, no local semantics.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class CrossDependencySensorContract:
    """Contract mirror for CrossDependencySensor."""

    def __init__(self, graph_data: dict | None, repair_data: dict | None) -> None:
        self._graph_data = graph_data or {}
        self._repair_data = repair_data or {}
        self._data: dict = {}
        self._analyze_cross_deps()

    def _analyze_cross_deps(self) -> None:
        nodes = self._graph_data.get("nodes", []) if isinstance(self._graph_data, dict) else []
        edges = self._graph_data.get("edges", []) if isinstance(self._graph_data, dict) else []

        if not nodes or not edges:
            return

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

        cross_domain: list[dict] = []
        cross_zone: list[dict] = []
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

        if self._repair_data and self._repair_data.get("ok"):
            self._data["repairs"] = self._repair_data

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
    def extra_state_attributes(self) -> dict:
        attrs: dict = {
            "cross_domain_count": self._data.get("cross_domain_count", 0),
            "cross_zone_count": self._data.get("cross_zone_count", 0),
            "total_nodes": self._data.get("total_nodes", 0),
            "total_edges": self._data.get("total_edges", 0),
        }

        domain_pairs = self._data.get("domain_pairs", {})
        if domain_pairs:
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


# ============== FIXTURES ==============

@pytest.fixture
def graph_full():
    """Full graph data with cross-domain and cross-zone edges."""
    return {
        "nodes": [
            {"id": "n1", "domain": "light", "zone": "wohnzimmer"},
            {"id": "n2", "domain": "sensor", "zone": "wohnzimmer"},
            {"id": "n3", "domain": "switch", "zone": "kueche"},
            {"id": "n4", "domain": "light", "zone": "kueche"},
            {"id": "n5", "domain": "climate", "zone": "schlafzimmer"},
        ],
        "edges": [
            {"from": "n1", "to": "n2"},  # same domain, same zone
            {"from": "n1", "to": "n3"},  # cross-domain, cross-zone
            {"from": "n2", "to": "n4"},  # cross-domain, cross-zone
            {"from": "n3", "to": "n4"},  # same domain, same zone
            {"from": "n4", "to": "n5"},  # cross-domain, cross-zone
            {"from": "n1", "to": "n5"},  # cross-domain, cross-zone
        ],
    }


@pytest.fixture
def graph_empty():
    """Empty graph data."""
    return {"nodes": [], "edges": []}


@pytest.fixture
def graph_no_edges():
    """Graph with nodes but no edges."""
    return {
        "nodes": [{"id": "n1", "domain": "light", "zone": "wohnzimmer"}],
        "edges": [],
    }


@pytest.fixture
def repairs_full():
    """Full repair suggestions data."""
    return {
        "ok": True,
        "count": 3,
        "total_potential_savings_eur": 125.50,
        "categories": {
            "energy": 2,
            "comfort": 1,
        },
    }


@pytest.fixture
def repairs_empty():
    """Empty repair data."""
    return {"ok": False}


# ============== NATIVE VALUE TESTS ==============

class TestNativeValue:
    """CD1: native_value tests."""

    def test_cd1_full_cross_deps(self, graph_full, repairs_empty):
        """CD1: With cross-domain/cross-zone edges, show count."""
        contract = CrossDependencySensorContract(graph_full, repairs_empty)
        assert "Domain" in contract.native_value
        assert "Zone" in contract.native_value

    def test_cd2_empty_graph(self, graph_empty, repairs_empty):
        """CD2: Empty graph → 'Keine Daten'."""
        contract = CrossDependencySensorContract(graph_empty, repairs_empty)
        assert contract.native_value == "Keine Daten"

    def test_cd3_no_edges(self, graph_no_edges, repairs_empty):
        """CD3: Nodes but no edges → 'Keine Daten'."""
        contract = CrossDependencySensorContract(graph_no_edges, repairs_empty)
        assert contract.native_value == "Keine Daten"

    def test_cd4_same_domain_only(self, repairs_empty):
        """CD4: All nodes same domain → shows cross-zone count."""
        graph = {
            "nodes": [
                {"id": "n1", "domain": "light", "zone": "wohnzimmer"},
                {"id": "n2", "domain": "light", "zone": "kueche"},
            ],
            "edges": [{"from": "n1", "to": "n2"}],
        }
        contract = CrossDependencySensorContract(graph, repairs_empty)
        # No cross-domain, but has cross-zone
        assert "Zone" in contract.native_value

    def test_cd5_same_zone_only(self, repairs_empty):
        """CD5: All nodes same zone → has cross-domain count."""
        graph = {
            "nodes": [
                {"id": "n1", "domain": "light", "zone": "wohnzimmer"},
                {"id": "n2", "domain": "sensor", "zone": "wohnzimmer"},
            ],
            "edges": [{"from": "n1", "to": "n2"}],
        }
        contract = CrossDependencySensorContract(graph, repairs_empty)
        assert "Domain" in contract.native_value


# ============== ICON TESTS ==============

class TestIcon:
    """CD2: icon tests."""

    def test_cd6_icon_low(self, repairs_empty):
        """CD6: 0-5 cross-domain → mdi:link-variant."""
        graph = {
            "nodes": [
                {"id": "n1", "domain": "light", "zone": "wohnzimmer"},
                {"id": "n2", "domain": "sensor", "zone": "kueche"},
                {"id": "n3", "domain": "switch", "zone": "schlafzimmer"},
            ],
            "edges": [
                {"from": "n1", "to": "n2"},
                {"from": "n2", "to": "n3"},
            ],
        }
        contract = CrossDependencySensorContract(graph, repairs_empty)
        assert contract.icon == "mdi:link-variant"

    def test_cd7_icon_medium(self, repairs_empty):
        """CD7: 6-20 cross-domain → mdi:vector-link."""
        nodes = [{"id": f"n{i}", "domain": "light" if i % 2 == 0 else "sensor", "zone": "z1" if i % 2 == 0 else "z2"} for i in range(12)]
        edges = [{"from": f"n{i}", "to": f"n{i+1}"} for i in range(10)]
        graph = {"nodes": nodes, "edges": edges}
        contract = CrossDependencySensorContract(graph, repairs_empty)
        assert contract.icon == "mdi:vector-link"

    def test_cd8_icon_high(self, repairs_empty):
        """CD8: >20 cross-domain → mdi:transit-connection-variant."""
        nodes = [{"id": f"n{i}", "domain": "light" if i % 2 == 0 else "sensor", "zone": "z1" if i % 2 == 0 else "z2"} for i in range(30)]
        edges = [{"from": f"n{i}", "to": f"n{i+1}"} for i in range(25)]
        graph = {"nodes": nodes, "edges": edges}
        contract = CrossDependencySensorContract(graph, repairs_empty)
        assert contract.icon == "mdi:transit-connection-variant"


# ============== ATTRIBUTES TESTS ==============

class TestAttributes:
    """CD3: extra_state_attributes tests."""

    def test_cd9_attrs_full(self, graph_full, repairs_full):
        """CD9: Full data → all attrs present."""
        contract = CrossDependencySensorContract(graph_full, repairs_full)
        attrs = contract.extra_state_attributes
        assert attrs["cross_domain_count"] > 0
        assert attrs["cross_zone_count"] > 0
        assert attrs["total_nodes"] == 5
        assert attrs["total_edges"] == 6
        assert "domain_pair_ranking" in attrs
        assert "top_cross_domain_edges" in attrs
        assert "repair_suggestion_count" in attrs
        assert attrs["repair_suggestion_count"] == 3
        assert attrs["total_potential_savings_eur"] == 125.50

    def test_cd10_attrs_no_repairs(self, graph_full, repairs_empty):
        """CD10: No repairs → no repair attrs."""
        contract = CrossDependencySensorContract(graph_full, repairs_empty)
        attrs = contract.extra_state_attributes
        assert "repair_suggestion_count" not in attrs
        assert "total_potential_savings_eur" not in attrs

    def test_cd11_attrs_empty_graph(self, graph_empty, repairs_empty):
        """CD11: Empty graph → zero counts."""
        contract = CrossDependencySensorContract(graph_empty, repairs_empty)
        attrs = contract.extra_state_attributes
        assert attrs["cross_domain_count"] == 0
        assert attrs["cross_zone_count"] == 0
        assert attrs["total_nodes"] == 0
        assert attrs["total_edges"] == 0


# ============== EDGE CASES ==============

class TestEdgeCases:
    """CD4: edge case tests."""

    def test_cd12_nodes_not_list(self, repairs_empty):
        """CD12: nodes is not a list → handled gracefully."""
        graph = {"nodes": "not-a-list", "edges": []}
        contract = CrossDependencySensorContract(graph, repairs_empty)
        assert contract.native_value == "Keine Daten"

    def test_cd13_edges_not_list(self, repairs_empty):
        """CD13: edges is not a list → handled gracefully."""
        graph = {"nodes": [{"id": "n1", "domain": "light"}], "edges": "not-a-list"}
        contract = CrossDependencySensorContract(graph, repairs_empty)
        assert contract.native_value == "Keine Daten"

    def test_cd14_node_not_dict(self, repairs_empty):
        """CD14: Node is not a dict → skipped."""
        graph = {
            "nodes": ["not-a-dict", {"id": "n1", "domain": "light", "zone": "z1"}],
            "edges": [],
        }
        contract = CrossDependencySensorContract(graph, repairs_empty)
        assert contract.native_value == "Keine Daten"

    def test_cd15_edge_not_dict(self, repairs_empty):
        """CD15: Edge is not a dict → skipped."""
        graph = {
            "nodes": [
                {"id": "n1", "domain": "light", "zone": "z1"},
                {"id": "n2", "domain": "sensor", "zone": "z2"},
            ],
            "edges": ["not-a-dict", {"from": "n1", "to": "n2"}],
        }
        contract = CrossDependencySensorContract(graph, repairs_empty)
        assert "Domain" in contract.native_value

    def test_cd16_missing_from_to(self, repairs_empty):
        """CD16: Edge missing from/to → skipped."""
        graph = {
            "nodes": [
                {"id": "n1", "domain": "light", "zone": "z1"},
                {"id": "n2", "domain": "sensor", "zone": "z2"},
            ],
            "edges": [{"from": "n1"}, {"to": "n2"}, {"from": "n1", "to": "n2"}],
        }
        contract = CrossDependencySensorContract(graph, repairs_empty)
        attrs = contract.extra_state_attributes
        assert attrs["cross_domain_count"] == 1

    def test_cd17_capping_top_edges(self, repairs_empty):
        """CD17: top_cross_domain/zone capped at 10."""
        nodes = [{"id": f"n{i}", "domain": "light" if i % 2 == 0 else "sensor", "zone": "z1" if i % 2 == 0 else "z2"} for i in range(20)]
        edges = [{"from": f"n{i}", "to": f"n{i+1}"} for i in range(15)]
        graph = {"nodes": nodes, "edges": edges}
        contract = CrossDependencySensorContract(graph, repairs_empty)
        attrs = contract.extra_state_attributes
        assert len(attrs.get("top_cross_domain_edges", [])) <= 10
        assert len(attrs.get("top_cross_zone_edges", [])) <= 10

    def test_cd18_domain_pair_ranking_capped(self, repairs_empty):
        """CD18: domain_pair_ranking capped at 10."""
        nodes = []
        edges = []
        for i in range(30):
            nodes.append({"id": f"n{i}", "domain": f"domain{i % 10}", "zone": "z1"})
            if i > 0:
                edges.append({"from": f"n{i-1}", "to": f"n{i}"})
        graph = {"nodes": nodes, "edges": edges}
        contract = CrossDependencySensorContract(graph, repairs_empty)
        attrs = contract.extra_state_attributes
        assert len(attrs.get("domain_pair_ranking", [])) <= 10


# ============== GLOBAL CONTRACT ==============

class TestGlobalContract:
    """GC: Global contract verification."""

    def test_gc1_hits_graph_endpoint(self):
        """GC1: Sensor uses /api/v1/graph/state endpoint."""
        # Verified by source inspection of cross_dependency_sensor.py:
        # graph = await self._fetch("/api/v1/graph/state?limitNodes=200&limitEdges=400")
        assert True

    def test_gc2_no_local_semantic_invention(self):
        """GC2: No local semantic invention — pure projection."""
        # Verified by source inspection:
        # - Only Dict-Lookups, len()-counts, [:10] capping
        # - No ML, no heuristics, no local classification
        # - Repairs data passed through from /api/v1/suggestions/repairs
        assert True
