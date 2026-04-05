"""Projection Contract Tests: cross_dependency_sensor.py

Verifies: CrossDependencySensor projects cross-dependency analysis
from graph data fetched via Core API — local analysis on fetched data
is considered projection.

Contract verified:
- state = formatted summary of cross-domain and cross-zone counts
- attrs = derived dependency metrics from graph data
- Icon varies by dependency density
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


class FakeResp:
    """Fake aiohttp response for patching _fetch."""
    def __init__(self, json_data, status=200):
        self._json = json_data
        self.status = status

    async def json(self):
        return self._json

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


# === Fixtures ===

@pytest.fixture
def coordinator():
    c = MagicMock()
    c.data = {}
    c._config = {"host": "localhost", "port": 8909, "token": "test_token"}
    return c


@pytest.fixture
def sensor(coordinator):
    from custom_components.copilot_ha.sensors.cross_dependency_sensor import CrossDependencySensor
    return CrossDependencySensor(coordinator)


# === CD1: native_value ===

def test_cross_dependency_cd1_no_data(sensor):
    """CD1: No graph data → 'Keine Daten'"""
    assert sensor.native_value == "Keine Daten"


def test_cross_dependency_cd1_with_counts(sensor):
    """CD1: With cross-dependency counts → formatted string"""
    sensor._data = {
        "cross_domain_count": 5,
        "cross_zone_count": 3,
    }
    assert sensor.native_value == "5 Domain / 3 Zone Cross-Deps"


def test_cross_dependency_cd1_zero_counts(sensor):
    """CD1: Zero counts → 'Keine Daten'"""
    sensor._data = {
        "cross_domain_count": 0,
        "cross_zone_count": 0,
    }
    assert sensor.native_value == "Keine Daten"


# === CD2: extra_state_attributes ===

def test_cross_dependency_cd2_attrs_structure(sensor):
    """CD2: attrs contain counts, totals, and derived metrics"""
    sensor._data = {
        "cross_domain_count": 10,
        "cross_zone_count": 5,
        "total_nodes": 50,
        "total_edges": 100,
        "domain_pairs": {"light<->switch": 8, "sensor<->binary_sensor": 2},
        "top_cross_domain": [{"from": "light.l1", "to": "switch.s1"}],
        "top_cross_zone": [{"from": "zone.living", "to": "zone.bedroom"}],
    }
    attrs = sensor.extra_state_attributes
    assert attrs["cross_domain_count"] == 10
    assert attrs["cross_zone_count"] == 5
    assert attrs["total_nodes"] == 50
    assert attrs["total_edges"] == 100
    assert len(attrs["domain_pair_ranking"]) == 2


def test_cross_dependency_cd2_empty_domain_pairs(sensor):
    """CD2: Empty domain_pairs → no domain_pair_ranking in attrs"""
    sensor._data = {
        "cross_domain_count": 0,
        "cross_zone_count": 0,
        "domain_pairs": {},
    }
    attrs = sensor.extra_state_attributes
    assert "domain_pair_ranking" not in attrs


def test_cross_dependency_cd2_with_repairs(sensor):
    """CD2: Repairs data included in attrs when available"""
    sensor._data = {
        "cross_domain_count": 5,
        "cross_zone_count": 2,
        "repairs": {
            "count": 3,
            "total_potential_savings_eur": 12.50,
            "categories": {"energy": 2, "comfort": 1},
        },
    }
    attrs = sensor.extra_state_attributes
    assert attrs["repair_suggestion_count"] == 3
    assert attrs["total_potential_savings_eur"] == 12.50
    assert attrs["repair_categories"] == {"energy": 2, "comfort": 1}


# === CD3: icon ===

def test_cross_dependency_cd3_icon_high_deps(sensor):
    """CD3: Many cross-domain deps → mdi:transit-connection-variant"""
    sensor._data = {"cross_domain_count": 25}
    assert sensor.icon == "mdi:transit-connection-variant"


def test_cross_dependency_cd3_icon_medium_deps(sensor):
    """CD3: Medium cross-domain deps → mdi:vector-link"""
    sensor._data = {"cross_domain_count": 10}
    assert sensor.icon == "mdi:vector-link"


def test_cross_dependency_cd3_icon_low_deps(sensor):
    """CD3: Few/no cross-domain deps → mdi:link-variant"""
    sensor._data = {"cross_domain_count": 2}
    assert sensor.icon == "mdi:link-variant"


# === CD4: _analyze_cross_deps ===

def test_cross_dependency_cd4_analyzes_graph(sensor):
    """CD4: _analyze_cross_deps extracts cross-domain/zone edges from graph"""
    sensor._graph_data = {
        "nodes": [
            {"id": "light.l1", "domain": "light", "zone": "living"},
            {"id": "switch.s1", "domain": "switch", "zone": "bedroom"},
            {"id": "sensor.t1", "domain": "sensor", "zone": "living"},
        ],
        "edges": [
            {"from": "light.l1", "to": "switch.s1"},  # cross-domain + cross-zone
            {"from": "sensor.t1", "to": "light.l1"},   # same-domain + cross-zone
        ],
    }
    sensor._analyze_cross_deps()
    assert sensor._data["cross_domain_count"] == 1
    assert sensor._data["cross_zone_count"] == 2
    assert sensor._data["total_nodes"] == 3
    assert sensor._data["total_edges"] == 2


def test_cross_dependency_cd4_empty_graph(sensor):
    """CD4: Empty graph → no analysis results"""
    sensor._graph_data = {"nodes": [], "edges": []}
    sensor._analyze_cross_deps()
    assert sensor._data.get("cross_domain_count") == 0
    assert sensor._data.get("cross_zone_count") == 0


def test_cross_dependency_cd4_invalid_edge_data(sensor):
    """CD4: Invalid edge data handled gracefully"""
    sensor._graph_data = {
        "nodes": [
            {"id": "light.l1", "domain": "light"},
        ],
        "edges": [
            {"from": "", "to": "switch.s1"},  # empty from
            {"from": "light.l1", "to": ""},   # empty to
            {"not_from": "x", "not_to": "y"}, # missing keys
        ],
    }
    # Should not raise
    sensor._analyze_cross_deps()
    assert sensor._data.get("cross_domain_count", 0) == 0


# === CD5: async_update ===

@pytest.mark.asyncio
async def test_cross_dependency_cd5_fetch_graph(sensor):
    """CD5: async_update fetches graph state from Core API"""
    graph_data = {
        "nodes": [{"id": "n1", "domain": "light"}],
        "edges": [],
    }
    with patch.object(sensor, '_fetch', return_value=graph_data):
        await sensor.async_update()
        assert sensor._graph_data == graph_data


@pytest.mark.asyncio
async def test_cross_dependency_cd5_fetch_suggestions(sensor):
    """CD5: async_update fetches repair suggestions"""
    suggestions = {"ok": True, "count": 2, "total_potential_savings_eur": 5.0}
    with patch.object(sensor, '_fetch') as mock_fetch:
        mock_fetch.side_effect = [
            {"nodes": [], "edges": []},  # graph
            suggestions,  # repairs
        ]
        await sensor.async_update()
        assert sensor._data.get("repairs") == suggestions


@pytest.mark.asyncio
async def test_cross_dependency_cd5_fetch_none(sensor):
    """CD5: Fetch returning None handled gracefully"""
    with patch.object(sensor, '_fetch', return_value=None):
        await sensor.async_update()
        # Should not raise, sensor remains in default state
        assert sensor._graph_data == {}


# === GC: Global Contract ===

def test_cross_dependency_gc1_projection_from_coordinator(sensor):
    """GC1: Sensor state derived from coordinator graph data projection"""
    sensor._data = {
        "cross_domain_count": 15,
        "cross_zone_count": 8,
        "total_nodes": 100,
        "total_edges": 200,
    }
    assert sensor.native_value == "15 Domain / 8 Zone Cross-Deps"
    attrs = sensor.extra_state_attributes
    assert attrs["total_nodes"] == 100
    assert attrs["total_edges"] == 200


def test_cross_dependency_gc2_icon_reflects_dependency_density(sensor):
    """GC2: Icon dynamically reflects cross-dependency density"""
    # High density
    sensor._data = {"cross_domain_count": 30}
    assert sensor.icon == "mdi:transit-connection-variant"
    # Medium density
    sensor._data = {"cross_domain_count": 15}
    assert sensor.icon == "mdi:vector-link"
    # Low density
    sensor._data = {"cross_domain_count": 0}
    assert sensor.icon == "mdi:link-variant"
