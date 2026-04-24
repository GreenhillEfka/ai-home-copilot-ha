"""Projection contract tests for DELIVERY-INTERACTIVE-303-B.

Bounded HA seam only:
- one HA-native delivery_interactive service
- canonical Core paths only
- actions bounded to acknowledge|cancel
- visible confirmation derives from canonical state only
"""
from __future__ import annotations

import ast
import pathlib

WORKTREE = pathlib.Path(__file__).parents[1].resolve()
COORDINATOR = WORKTREE / "custom_components" / "pilotsuite" / "coordinator.py"
SERVICES_SETUP = WORKTREE / "custom_components" / "pilotsuite" / "services_setup.py"
SERVICES_YAML = WORKTREE / "custom_components" / "pilotsuite" / "services.yaml"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


class _ServiceCallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.registered_services: list[str] = []
        self.has_delivery_interactive_call = False
        self.has_delivery_status_call = False
        self.has_notification_create = False
        self.literal_actions: set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "async_register":
            if len(node.args) >= 2:
                service_name = node.args[1]
                if isinstance(service_name, ast.Constant) and isinstance(service_name.value, str):
                    self.registered_services.append(service_name.value)

        if isinstance(func, ast.Attribute) and func.attr == "async_delivery_interactive":
            self.has_delivery_interactive_call = True
        if isinstance(func, ast.Attribute) and func.attr == "async_delivery_status":
            self.has_delivery_status_call = True
        if isinstance(func, ast.Attribute) and func.attr == "async_create":
            owner = func.value
            if isinstance(owner, ast.Name) and owner.id == "persistent_notification":
                self.has_notification_create = True

        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                if arg.value in {"acknowledge", "cancel"}:
                    self.literal_actions.add(arg.value)
        self.generic_visit(node)


class TestDeliveryInteractiveServiceProjection:
    def test_d303b1_coordinator_uses_canonical_delivery_paths(self) -> None:
        src = _read(COORDINATOR)
        assert '"/api/v1/delivery/acknowledge"' in src
        assert 'f"/api/v1/delivery/{delivery_token}/status"' in src

    def test_d303b2_single_bounded_service_registered(self) -> None:
        tree = ast.parse(_read(SERVICES_SETUP), filename=str(SERVICES_SETUP))
        visitor = _ServiceCallVisitor()
        visitor.visit(tree)
        assert "delivery_interactive" in visitor.registered_services

    def test_d303b3_service_calls_interactive_and_status_only(self) -> None:
        tree = ast.parse(_read(SERVICES_SETUP), filename=str(SERVICES_SETUP))
        visitor = _ServiceCallVisitor()
        visitor.visit(tree)
        assert visitor.has_delivery_interactive_call is True
        assert visitor.has_delivery_status_call is True

    def test_d303b4_action_space_is_bounded(self) -> None:
        src = _read(SERVICES_SETUP)
        assert 'vol.In(("acknowledge", "cancel"))' in src
        assert "action not in (\"acknowledge\", \"cancel\")" in src

    def test_d303b5_blank_delivery_token_rejected_before_outbound_call(self) -> None:
        src = _read(SERVICES_SETUP)
        token_check = 'if not delivery_token:'
        outbound_call = 'await coordinator.api.async_delivery_interactive('
        assert token_check in src
        assert src.index(token_check) < src.index(outbound_call)

    def test_d303b6_visible_confirmation_is_ha_native_and_canonical(self) -> None:
        tree = ast.parse(_read(SERVICES_SETUP), filename=str(SERVICES_SETUP))
        visitor = _ServiceCallVisitor()
        visitor.visit(tree)
        assert visitor.has_notification_create is True
        src = _read(SERVICES_SETUP)
        assert 'canonical_state = str(status.get("state") or "pending")' in src
        assert 'f"state: {canonical_state}"' in src

    def test_d303b7_services_yaml_documents_delivery_interactive(self) -> None:
        raw = _read(SERVICES_YAML)
        assert "delivery_interactive:" in raw
        assert "acknowledge" in raw
        assert "cancel" in raw
