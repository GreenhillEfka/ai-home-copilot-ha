"""Contract tests: NeuronFeedEntities projection surface.

Covers:
NF1: NeuronFeedTagSwitch unique_id uses pilotsuite_neuron_feed_<tag_id> prefix
NF2: NeuronFeedSummarySensor unique_id is pilotsuite_neuron_feed_summary
NF3: AST scan: no stale copilot_ha unique_id literals in neuron_feed_entities.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parent.parent / "custom_components" / "pilotsuite" / "neuron_feed_entities.py"
SOURCE = MODULE_PATH.read_text()


class TestNeuronFeedEntitiesProjection:
    """Contract tests for neuron_feed_entities projection surface."""

    def test_neuron_feed_tag_switch_unique_id_uses_pilotsuite_prefix(self):
        """NF1: NeuronFeedTagSwitch._attr_unique_id uses pilotsuite_neuron_feed_<tag_id>."""
        tree = ast.parse(SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "NeuronFeedTagSwitch":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        for stmt in ast.walk(item):
                            if isinstance(stmt, ast.Assign):
                                for target in stmt.targets:
                                    if isinstance(target, ast.Attribute) and target.attr == "_attr_unique_id":
                                        value = ast.unparse(stmt.value)
                                        assert "pilotsuite_neuron_feed_" in value, (
                                            f"NeuronFeedTagSwitch._attr_unique_id must use "
                                            f"'pilotsuite_neuron_feed_' prefix, got: {value}"
                                        )
                                        assert "copilot_ha_neuron_feed_" not in value, (
                                            f"Stale copilot_ha_neuron_feed_ prefix in "
                                            f"NeuronFeedTagSwitch._attr_unique_id: {value}"
                                        )

    def test_neuron_feed_summary_sensor_unique_id_is_pilotsuite(self):
        """NF2: NeuronFeedSummarySensor._attr_unique_id is pilotsuite_neuron_feed_summary."""
        tree = ast.parse(SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "NeuronFeedSummarySensor":
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Attribute) and target.attr == "_attr_unique_id":
                                value = ast.unparse(item.value).strip('"').strip("'")
                                assert value == "pilotsuite_neuron_feed_summary", (
                                    f"NeuronFeedSummarySensor._attr_unique_id must be "
                                    f"'pilotsuite_neuron_feed_summary', got: {value}"
                                )

    def test_ast_scan_no_stale_copilot_ha_unique_id_literals(self):
        """NF3: AST scan finds zero stale copilot_ha unique_id literals in neuron_feed_entities."""
        tree = ast.parse(SOURCE)
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and target.attr == "_attr_unique_id":
                        value = ast.unparse(node.value)
                        if "copilot_ha" in value:
                            findings.append(value)
        assert not findings, (
            f"AST scan found stale copilot_ha unique_id literals in neuron_feed_entities.py: {findings}"
        )
