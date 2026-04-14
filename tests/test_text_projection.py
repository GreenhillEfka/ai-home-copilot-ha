"""Projection contract tests for text.py (HA-439)."""
import ast
import sys
import os

# Ensure the custom_components path is in sys.path for ast.parse-only analysis
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestTextEntitiesProjection:
    """Test that text.py unique_ids are canonically pilotsuite namespaced."""

    def test_seed_allow_domains_unique_id(self):
        """T1: unique_id for seed allow domains is pilotsuite namespaced."""
        src_path = os.path.join(os.path.dirname(__file__), "..", "custom_components", "pilotsuite", "text.py")
        src = open(src_path).read()
        tree = ast.parse(src)
        # Find the two unique_id kwargs in the async_add_entities call
        unique_ids = []
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "unique_id":
                val = node.value
                if isinstance(val, ast.Constant):
                    unique_ids.append(val.value)
        assert len(unique_ids) >= 2, f"Expected at least 2 unique_id values, got {len(unique_ids)}"
        assert unique_ids[0] == "pilotsuite_seed_allow_domains_csv", (
            f"Expected pilotsuite_seed_allow_domains_csv, got {unique_ids[0]!r}"
        )

    def test_seed_block_domains_unique_id(self):
        """T2: unique_id for seed block domains is pilotsuite namespaced."""
        src_path = os.path.join(os.path.dirname(__file__), "..", "custom_components", "pilotsuite", "text.py")
        src = open(src_path).read()
        tree = ast.parse(src)
        unique_ids = []
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "unique_id":
                val = node.value
                if isinstance(val, ast.Constant):
                    unique_ids.append(val.value)
        assert len(unique_ids) >= 2, f"Expected at least 2 unique_id values, got {len(unique_ids)}"
        assert unique_ids[1] == "pilotsuite_seed_block_domains_csv", (
            f"Expected pilotsuite_seed_block_domains_csv, got {unique_ids[1]!r}"
        )

    def test_no_stale_copilot_ha_in_text_module(self):
        """T3: AST scan — null stale copilot_ha unique_id literals in text.py."""
        src_path = os.path.join(os.path.dirname(__file__), "..", "custom_components", "pilotsuite", "text.py")
        src = open(src_path).read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "unique_id":
                val = node.value
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    assert "copilot_ha" not in val.value, (
                        f"Stale copilot_ha found in unique_id literal: {val.value!r}"
                    )

    def test_syntax_ok(self):
        """T4: text.py has valid Python syntax."""
        src_path = os.path.join(os.path.dirname(__file__), "..", "custom_components", "pilotsuite", "text.py")
        src = open(src_path).read()
        tree = ast.parse(src)
        assert tree is not None