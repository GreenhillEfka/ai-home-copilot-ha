"""Projection proof for E2E-OBSERVABILITY-305 on the HA seam.

Bounded claim only:
- the existing HA delivery_interactive seam exposes a machine-checkable proof chain
- canonical Core state is observed in HA-visible confirmation
- no feature widening beyond the existing service / notification / event path
"""
from __future__ import annotations

import ast
import pathlib

WORKTREE = pathlib.Path(__file__).parents[1].resolve()
SERVICES_SETUP = WORKTREE / "custom_components" / "pilotsuite" / "services_setup.py"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _delivery_handler() -> ast.AsyncFunctionDef:
    tree = ast.parse(_read(SERVICES_SETUP), filename=str(SERVICES_SETUP))
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_handle_delivery_interactive":
            return node
    raise AssertionError("_handle_delivery_interactive not found")


class _HandlerVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.call_order: list[str] = []
        self.notification_id_literals: list[str] = []
        self.bus_event_names: list[str] = []
        self.bus_payload_keys: set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "async_delivery_interactive":
            self.call_order.append("interactive")
        elif isinstance(func, ast.Attribute) and func.attr == "async_delivery_status":
            self.call_order.append("status")
        elif isinstance(func, ast.Attribute) and func.attr == "async_create":
            owner = func.value
            if isinstance(owner, ast.Name) and owner.id == "persistent_notification":
                self.call_order.append("notification")
                for kw in node.keywords:
                    if kw.arg == "notification_id" and isinstance(kw.value, ast.JoinedStr):
                        parts: list[str] = []
                        for value in kw.value.values:
                            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                                parts.append(value.value)
                        self.notification_id_literals.append("".join(parts))
        elif isinstance(func, ast.Attribute) and func.attr == "async_fire":
            self.call_order.append("event")
            if node.args and isinstance(node.args[0], ast.JoinedStr):
                parts: list[str] = []
                for value in node.args[0].values:
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        parts.append(value.value)
                self.bus_event_names.append("".join(parts))
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Dict):
                for key in node.args[1].keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        self.bus_payload_keys.add(key.value)
        self.generic_visit(node)


class TestE2EObservability305HAProjection:
    def test_e2e305_ha1_chain_order_is_machine_checkable(self) -> None:
        visitor = _HandlerVisitor()
        visitor.visit(_delivery_handler())
        assert visitor.call_order == ["interactive", "status", "notification", "event"]

    def test_e2e305_ha2_ha_visible_confirmation_reads_canonical_state(self) -> None:
        src = _read(SERVICES_SETUP)
        assert 'canonical_state = str(status.get("state") or "pending")' in src
        assert 'f"delivery_token: {delivery_token}\\n"' in src
        assert 'f"action: {action}\\n"' in src
        assert 'f"state: {canonical_state}"' in src

    def test_e2e305_ha3_notification_id_stays_on_existing_bounded_path(self) -> None:
        visitor = _HandlerVisitor()
        visitor.visit(_delivery_handler())
        assert visitor.notification_id_literals == ["pilotsuite_delivery_interactive_"]

    def test_e2e305_ha4_event_projection_carries_observable_chain_state(self) -> None:
        visitor = _HandlerVisitor()
        visitor.visit(_delivery_handler())
        assert visitor.bus_event_names == ["_delivery_interactive"]
        assert {"ok", "delivery_token", "action", "state"} <= visitor.bus_payload_keys

    def test_e2e305_ha5_no_extra_delivery_api_family_is_introduced(self) -> None:
        src = _read(SERVICES_SETUP)
        assert src.count("async_delivery_interactive(") == 1
        assert src.count("async_delivery_status(") == 1
