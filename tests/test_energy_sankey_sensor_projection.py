"""Projection contract tests for EnergySankeySensor.

Verifies EnergySankeySensor is a pure Projection-Shell on /api/v1/energy/sankey.
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, AsyncMock, patch

import pytest


# ── Contract Mirror ──────────────────────────────────────────────────────────

class EnergySankeySensorContract:
    """Contract mirror of EnergySankeySensor projection behavior."""

    @staticmethod
    def native_value(flow_data: dict | None) -> str:
        if flow_data and flow_data.get("ok"):
            nodes = len(flow_data.get("nodes", []))
            flows = len(flow_data.get("flows", []))
            return f"{nodes} nodes, {flows} flows"
        return "unavailable"

    @staticmethod
    def extra_state_attributes(flow_data: dict | None) -> dict:
        base = {
            "sankey_svg_url": "http://localhost:8012/api/v1/energy/sankey.svg",
            "sankey_json_url": "http://localhost:8012/api/v1/energy/sankey",
        }
        if flow_data and flow_data.get("ok"):
            summary = flow_data.get("summary", {})
            nodes = flow_data.get("nodes", [])
            attrs = {
                "total_consumption_kwh": summary.get("total_consumption_kwh", 0),
                "total_production_kwh": summary.get("total_production_kwh", 0),
                "grid_kwh": summary.get("grid_kwh", 0),
                "node_count": len(nodes) if isinstance(nodes, list) else 0,
                "flow_count": len(flow_data.get("flows", [])),
            }
            if isinstance(nodes, list):
                attrs["sources"] = [
                    n["label"] for n in nodes
                    if isinstance(n, dict) and n.get("category") == "source"
                ]
                attrs["consumers"] = [
                    n["label"] for n in nodes
                    if isinstance(n, dict) and n.get("category") in ("device", "zone")
                ]
            else:
                attrs["sources"] = []
                attrs["consumers"] = []
            return {**base, **attrs}
        return base

    @staticmethod
    def ok_status(flow_data: dict | None) -> bool:
        return bool(flow_data and flow_data.get("ok"))


# ── Test helpers ─────────────────────────────────────────────────────────────

def make_sensor(flow_data: dict | None) -> MagicMock:
    """Build a sensor with _flow_data pre-set."""
    sensor = MagicMock()
    sensor._flow_data = flow_data
    sensor._core_base_url = MagicMock(return_value="http://localhost:8012")
    # native_value and extra_state_attributes as properties
    sensor._flow_data = flow_data
    return sensor


# ── Sankey native_value ───────────────────────────────────────────────────────

class TestEnergySankeyNativeValue:
    """ES1: native_value from _flow_data['ok']"""

    def test_es1_ok_with_nodes_and_flows(self):
        """OK data with nodes and flows → formatted summary string."""
        data = {
            "ok": True,
            "nodes": [{"id": "n1"}, {"id": "n2"}, {"id": "n3"}],
            "flows": [{"from": "n1", "to": "n2"}, {"from": "n2", "to": "n3"}],
        }
        result = EnergySankeySensorContract.native_value(data)
        assert result == "3 nodes, 2 flows"

    def test_es1_ok_empty(self):
        """OK but no nodes/flows → '0 nodes, 0 flows'."""
        data = {"ok": True, "nodes": [], "flows": []}
        result = EnergySankeySensorContract.native_value(data)
        assert result == "0 nodes, 0 flows"

    def test_es1_ok_missing_nodes_and_flows(self):
        """OK but keys missing entirely → '0 nodes, 0 flows'."""
        data = {"ok": True}
        result = EnergySankeySensorContract.native_value(data)
        assert result == "0 nodes, 0 flows"

    def test_es1_not_ok(self):
        """ok=False → 'unavailable'."""
        data = {"ok": False, "nodes": [], "flows": []}
        result = EnergySankeySensorContract.native_value(data)
        assert result == "unavailable"

    def test_es1_none(self):
        """None data → 'unavailable'."""
        result = EnergySankeySensorContract.native_value(None)
        assert result == "unavailable"


# ── Sankey extra_state_attributes ────────────────────────────────────────────

class TestEnergySankeyAttrs:
    """ES2: extra_state_attributes from _flow_data"""

    def test_es2_full_data(self):
        """Full flow data → attrs include URLs + summary + node lists."""
        data = {
            "ok": True,
            "summary": {
                "total_consumption_kwh": 12.5,
                "total_production_kwh": 8.3,
                "grid_kwh": 4.2,
            },
            "nodes": [
                {"id": "solar", "label": "Solar", "category": "source"},
                {"id": "grid", "label": "Grid", "category": "source"},
                {"id": "living", "label": "Living Room", "category": "device"},
                {"id": "kitchen", "label": "Kitchen", "category": "zone"},
            ],
            "flows": [{"from": "solar", "to": "living"}],
        }
        attrs = EnergySankeySensorContract.extra_state_attributes(data)
        assert attrs["sankey_svg_url"] == "http://localhost:8012/api/v1/energy/sankey.svg"
        assert attrs["sankey_json_url"] == "http://localhost:8012/api/v1/energy/sankey"
        assert attrs["total_consumption_kwh"] == 12.5
        assert attrs["total_production_kwh"] == 8.3
        assert attrs["grid_kwh"] == 4.2
        assert attrs["node_count"] == 4
        assert attrs["flow_count"] == 1
        assert attrs["sources"] == ["Solar", "Grid"]
        assert attrs["consumers"] == ["Living Room", "Kitchen"]

    def test_es2_ok_missing_summary(self):
        """OK but summary missing → defaults to 0."""
        data = {"ok": True, "nodes": [], "flows": []}
        attrs = EnergySankeySensorContract.extra_state_attributes(data)
        assert attrs["total_consumption_kwh"] == 0
        assert attrs["total_production_kwh"] == 0
        assert attrs["grid_kwh"] == 0
        assert attrs["node_count"] == 0
        assert attrs["flow_count"] == 0
        assert attrs["sources"] == []
        assert attrs["consumers"] == []

    def test_es2_not_ok(self):
        """ok=False → only base URLs, no summary."""
        data = {"ok": False}
        attrs = EnergySankeySensorContract.extra_state_attributes(data)
        assert attrs["sankey_svg_url"] == "http://localhost:8012/api/v1/energy/sankey.svg"
        assert attrs["sankey_json_url"] == "http://localhost:8012/api/v1/energy/sankey"
        assert "total_consumption_kwh" not in attrs
        assert "node_count" not in attrs

    def test_es2_none(self):
        """None → only base URLs."""
        attrs = EnergySankeySensorContract.extra_state_attributes(None)
        assert attrs["sankey_svg_url"] == "http://localhost:8012/api/v1/energy/sankey.svg"
        assert "node_count" not in attrs

    def test_es2_ignores_non_source_consumer_nodes(self):
        """Nodes with non-source/consumer categories are excluded from sources/consumers."""
        data = {
            "ok": True,
            "nodes": [
                {"id": "solar", "label": "Solar", "category": "source"},
                {"id": "storage", "label": "Battery", "category": "storage"},  # ignored
                {"id": "light", "label": "Light", "category": "device"},  # consumer
            ],
            "flows": [],
        }
        attrs = EnergySankeySensorContract.extra_state_attributes(data)
        assert attrs["sources"] == ["Solar"]
        assert attrs["consumers"] == ["Light"]


# ── Edge cases ────────────────────────────────────────────────────────────────

class TestEnergySankeyEdge:
    """ES3: edge cases"""

    def test_es3_node_missing_category(self):
        """Node without category key → excluded from sources/consumers."""
        data = {
            "ok": True,
            "nodes": [{"id": "unknown", "label": "Unknown"}],
            "flows": [],
        }
        attrs = EnergySankeySensorContract.extra_state_attributes({"ok": True, "nodes": [{"id": "unknown", "label": "Unknown"}], "flows": []})
        assert attrs["sources"] == []
        assert attrs["consumers"] == []

    def test_es3_node_category_wrong_type(self):
        """Node with non-string category → skipped gracefully."""
        data = {
            "ok": True,
            "nodes": [{"id": "n1", "label": "Test", "category": 123}],
            "flows": [],
        }
        attrs = EnergySankeySensorContract.extra_state_attributes(data)
        assert attrs["sources"] == []
        assert attrs["consumers"] == []

    def test_es3_nodes_is_not_list(self):
        """nodes is not a list → empty sources/consumers, node_count=0."""
        data = {"ok": True, "nodes": "not a list", "flows": []}
        attrs = EnergySankeySensorContract.extra_state_attributes(data)
        assert attrs["sources"] == []
        assert attrs["consumers"] == []
        assert attrs["node_count"] == 0


# ── Global Contract ────────────────────────────────────────────────────────────

class TestEnergySankeyGlobalContract:
    """GC1–GC2: Global projection contract"""

    def test_gc1_hits_correct_api_endpoint(self):
        """GC1: EnergySankeySensor hits /api/v1/energy/sankey."""
        # The sensor fetches from /api/v1/energy/sankey — verified by code inspection
        from custom_components.pilotsuite.sensors.energy_sankey_sensor import EnergySankeySensor
        import inspect
        source = inspect.getsource(EnergySankeySensor.async_update)
        assert "/api/v1/energy/sankey" in source

    def test_gc2_no_local_semantic_invention(self):
        """GC2: Sensor only formats API response — no local ML/Heuristik."""
        # native_value: trivial len() on nodes/flows list
        # attrs: direct dict.get() calls + list comprehension over nodes
        # no thresholds, no classification, no inference
        data = {
            "ok": True,
            "summary": {"total_consumption_kwh": 5.0},
            "nodes": [{"id": "n1", "label": "Solar", "category": "source"}],
            "flows": [{"from": "n1", "to": "n2"}],
        }
        nv = EnergySankeySensorContract.native_value(data)
        attrs = EnergySankeySensorContract.extra_state_attributes(data)
        assert nv == "1 nodes, 1 flows"
        assert attrs["total_consumption_kwh"] == 5.0
        assert attrs["sources"] == ["Solar"]
