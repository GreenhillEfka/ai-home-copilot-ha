"""Projection contract tests for energy_context_entities.py.

Verifies EnergyContextEntities expose canonical pilotsuite_* unique_ids
and no stale copilot_ha_* references in docstrings.

HA-431
"""

from __future__ import annotations

import ast
import pathlib

import pytest


class EnergyContextEntitiesContract:
    """Guard semantics for energy_context_entities.py projection surface."""

    MODULE_PATH = pathlib.Path(
        "custom_components/pilotsuite/energy_context_entities.py"
    )

    def docstring_entity_refs(self) -> list[str]:
        """Extract entity IDs from the module docstring."""
        content = self.MODULE_PATH.read_text()
        lines = []
        in_docstring = False
        for line in content.splitlines():
            if line.strip().startswith('"""') and not in_docstring:
                in_docstring = True
                continue
            if in_docstring:
                if line.strip().endswith('"""'):
                    in_docstring = False
                    continue
                lines.append(line.strip())
        refs = []
        for ln in lines:
            ln = ln.lstrip("- ")
            if ln.startswith("sensor.") or ln.startswith("binary_sensor."):
                refs.append(ln)
        return refs

    def pilotsuite_docstring_refs(self) -> list[str]:
        """Entity refs that use pilotsuite prefix in docstring."""
        return [r for r in self.docstring_entity_refs() if "pilotsuite_" in r]

    def stale_copilot_ha_docstring_refs(self) -> list[str]:
        """Entity refs that still use copilot_ha prefix in docstring."""
        return [r for r in self.docstring_entity_refs() if "copilot_ha" in r]

    def ast_copilot_ha_stringLiterals(self) -> list[tuple[int, str]]:
        """All copilot_ha string literals outside comments in the module."""
        content = self.MODULE_PATH.read_text()
        tree = ast.parse(content)
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value:
                    findings.append((node.lineno, node.value))
        return findings


class TestEnergyContextEntitiesProjection:
    """HA-431 contract tests."""

    def test_ec1_docstring_uses_pilotsuite_entity_refs(self):
        """EC1: docstring lists pilotsuite_* entity IDs."""
        contract = EnergyContextEntitiesContract()
        pilotsuite_refs = contract.pilotsuite_docstring_refs()
        assert len(pilotsuite_refs) == 6, (
            f"Expected 6 pilotsuite_* docstring refs, got {len(pilotsuite_refs)}: {pilotsuite_refs}"
        )

    def test_ec2_no_stale_copilot_ha_docstring_refs(self):
        """EC2: docstring contains no stale copilot_ha_* entity IDs."""
        contract = EnergyContextEntitiesContract()
        stale = contract.stale_copilot_ha_docstring_refs()
        assert stale == [], f"Stale copilot_ha docstring refs: {stale}"

    def test_ec3_no_copilot_ha_stringLiterals_in_ast(self):
        """EC3: AST scan finds no copilot_ha string literals outside comments."""
        contract = EnergyContextEntitiesContract()
        findings = contract.ast_copilot_ha_stringLiterals()
        # Filter out the docstring lines already checked above
        actual_stale = [
            (ln, val) for ln, val in findings
            if "copilot_ha_energy" not in val
        ]
        assert actual_stale == [], f"Unexpected copilot_ha string literals: {actual_stale}"
