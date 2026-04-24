"""Projection proof for DELIVERY-CONTEXT-306-B on the HA seam.

Bounded claim only:
- existing HA delivery_interactive seam projects the canonical delivery context
- context stays explicit and small
- no new HA action family or UI family is introduced
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
        self.status_calls = 0
        self.notification_id_literals: list[str] = []
        self.bus_payload_keys: set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "async_delivery_status":
            self.status_calls += 1
        elif isinstance(func, ast.Attribute) and func.attr == "async_create":
            owner = func.value
            if isinstance(owner, ast.Name) and owner.id == "persistent_notification":
                for kw in node.keywords:
                    if kw.arg == "notification_id" and isinstance(kw.value, ast.JoinedStr):
                        parts: list[str] = []
                        for value in kw.value.values:
                            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                                parts.append(value.value)
                        self.notification_id_literals.append("".join(parts))
        elif isinstance(func, ast.Attribute) and func.attr == "async_fire":
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Dict):
                for key in node.args[1].keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        self.bus_payload_keys.add(key.value)
        self.generic_visit(node)


class TestDeliveryContext306HAProjection:
    def test_d306b1_reads_context_from_canonical_delivery_status(self) -> None:
        src = _read(SERVICES_SETUP)
        assert 'status = await coordinator.api.async_delivery_status(delivery_token)' in src
        assert 'context_raw = status.get("context") if isinstance(status, dict) else {}' in src

    def test_d306b2_context_shape_stays_small_and_explicit(self) -> None:
        src = _read(SERVICES_SETUP)
        assert '"zone": context_raw.get("zone")' in src
        assert '"surface": context_raw.get("surface")' in src
        assert '"prompt_label": (' in src
        assert 'context.prompt_label: {canonical_context[\'prompt_label\']}' in src

    def test_d306b3_missing_context_is_explicit_and_non_crashing(self) -> None:
        src = _read(SERVICES_SETUP)
        assert 'context_raw = context_raw if isinstance(context_raw, dict) else {}' in src
        assert 'else None' in src

    def test_d306b4_notification_stays_on_existing_bounded_path(self) -> None:
        visitor = _HandlerVisitor()
        visitor.visit(_delivery_handler())
        assert visitor.status_calls == 1
        assert visitor.notification_id_literals == ["pilotsuite_delivery_interactive_"]

    def test_d306b5_event_projection_carries_context_without_widening_action_family(self) -> None:
        visitor = _HandlerVisitor()
        visitor.visit(_delivery_handler())
        assert {"ok", "delivery_token", "action", "state", "context"} <= visitor.bus_payload_keys
        src = _read(SERVICES_SETUP)
        assert src.count("async_delivery_interactive(") == 1
        assert src.count("async_delivery_status(") == 1
