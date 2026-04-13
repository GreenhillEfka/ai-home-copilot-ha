"""
Projection contract tests for services_setup.py (HA-412).

Validates:
  SVS1 - Legacy service names copilot_ha_unifi_run_diagnostics / copilot_ha_unifi_get_report
         are replaced by pilotsuite_unifi_run_diagnostics / pilotsuite_unifi_get_report
  SVS2 - Canonical service names pilotsuite_unifi_run_diagnostics / pilotsuite_unifi_get_report
         are registered in the DOMAIN namespace
  SVS3 - No copilot_ha string literals remain in services_setup.py
"""
from __future__ import annotations

import ast
import pathlib
import pytest

WORKTREE = pathlib.Path(__file__).parents[1].resolve()
SERVICES_SETUP = WORKTREE / "custom_components" / "pilotsuite" / "services_setup.py"


class ServiceSetupValidator(ast.NodeVisitor):
    """AST-based guard for copilot_ha legacy service references in services_setup.py."""

    def __init__(self) -> None:
        self.legacy_service_names: list[tuple[str, int]] = []
        self.canonical_service_names: list[tuple[str, int]] = []
        self.copilot_ha_literals: list[tuple[str, int]] = []

    def visit_Call(self, node: ast.Call) -> None:
        # Detect hass.services.async_register or hass.services.has_service calls
        func = node.func
        is_register = (
            isinstance(func, ast.Attribute)
            and func.attr in ("async_register", "has_service")
        )
        is_services_ns = (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Attribute)
            and func.value.attr == "services"
        )
        if is_register and is_services_ns:
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    name = arg.value
                    if name == "copilot_ha_unifi_run_diagnostics":
                        self.legacy_service_names.append((name, arg.lineno))
                    elif name == "copilot_ha_unifi_get_report":
                        self.legacy_service_names.append((name, arg.lineno))
                    elif name == "pilotsuite_unifi_run_diagnostics":
                        self.canonical_service_names.append((name, arg.lineno))
                    elif name == "pilotsuite_unifi_get_report":
                        self.canonical_service_names.append((name, arg.lineno))
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str) and "copilot_ha" in node.value:
            self.copilot_ha_literals.append((node.value, node.lineno))
        self.generic_visit(node)


def _read_services_setup() -> str:
    return SERVICES_SETUP.read_text()


def _parse_services_setup(src: str) -> ast.Module:
    return ast.parse(src, filename=str(SERVICES_SETUP))


class TestServiceSetupProjection:
    """Projection contract for services_setup.py unique_id / service name parity."""

    def test_svcs1_legacy_service_names_replaced(self) -> None:
        """SVS1: copilot_ha_unifi_* legacy service names no longer registered."""
        src = _read_services_setup()
        tree = _parse_services_setup(src)
        visitor = ServiceSetupValidator()
        visitor.visit(tree)
        assert (
            visitor.legacy_service_names == []
        ), f"Legacy service names still present: {visitor.legacy_service_names}"

    def test_svcs2_canonical_service_names_present(self) -> None:
        """SVS2: pilotsuite_unifi_* canonical service names are registered."""
        src = _read_services_setup()
        tree = _parse_services_setup(src)
        visitor = ServiceSetupValidator()
        visitor.visit(tree)
        expected = {"pilotsuite_unifi_run_diagnostics", "pilotsuite_unifi_get_report"}
        found = {name for name, _ in visitor.canonical_service_names}
        assert (
            expected <= found
        ), f"Missing canonical service names: {expected - found} (found: {visitor.canonical_service_names})"

    def test_svcs3_no_copilot_ha_literals(self) -> None:
        """SVS3: No copilot_ha string literals remain in services_setup.py."""
        src = _read_services_setup()
        tree = _parse_services_setup(src)
        visitor = ServiceSetupValidator()
        visitor.visit(tree)
        assert (
            visitor.copilot_ha_literals == []
        ), f"copilot_ha literals still present: {visitor.copilot_ha_literals}"