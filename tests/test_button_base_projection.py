"""Contract guards for custom_components/pilotsuite/button_base.py.

BB1: _call_service default domain is pilotsuite (not copilot_ha)
BB2: no stale copilot_ha domain default in CopilotButtonBase._call_service signature
"""
from __future__ import annotations

import ast
import pytest

SRC = "custom_components/pilotsuite/button_base.py"


def _find_call_service(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_call_service":
            return node
    return None


def _get_kwonly_defaults(cs: ast.FunctionDef | ast.AsyncFunctionDef):
    """Extract keyword-only arg -> default mapping from a function def.

    Python 3.11+: keyword-only args live in kwonlyargs with defaults in kw_defaults.
    Older Python: keyword-only args + defaults are merged; use kwonlydefaults dict.
    """
    kwonlyargs = getattr(cs.args, "kwonlyargs", []) or []
    # Python 3.11+: defaults for kwonlyargs are in kw_defaults (aligned same order)
    kw_defaults = getattr(cs.args, "kw_defaults", None)
    if kw_defaults is not None:
        return {arg.arg: default for arg, default in zip(kwonlyargs, kw_defaults) if default is not None}
    # Python < 3.11: kwonlydefaults is a dict
    return getattr(cs.args, "kwonlydefaults", None) or {}


class TestButtonBaseProjection:
    """Projection contract for CopilotButtonBase."""

    def test_bb1_call_service_default_domain_is_pilotsuite(self):
        """BB1: _call_service default domain is 'pilotsuite', not 'copilot_ha'."""
        with open(SRC) as f:
            src = f.read()
        tree = ast.parse(src)

        cs = _find_call_service(tree)
        assert cs is not None, "_call_service method not found"

        defaults = _get_kwonly_defaults(cs)
        domain_default = defaults.get("domain")
        assert domain_default is not None, "domain kwarg has no default"
        assert isinstance(domain_default, ast.Constant), "domain default is not a Constant"
        assert domain_default.value == "pilotsuite", (
            f"domain default is {domain_default.value!r}, expected 'pilotsuite'"
        )

    def test_bb2_no_stale_copilot_ha_domain_in_call_service(self):
        """BB2: _call_service domain default is not 'copilot_ha'."""
        with open(SRC) as f:
            src = f.read()
        tree = ast.parse(src)

        cs = _find_call_service(tree)
        assert cs is not None, "_call_service method not found"

        defaults = _get_kwonly_defaults(cs)
        domain_default = defaults.get("domain")
        assert domain_default is not None, "domain kwarg has no default"
        assert isinstance(domain_default, ast.Constant), "domain default is not a Constant"
        assert domain_default.value != "copilot_ha", (
            f"domain default still uses stale 'copilot_ha' (got {domain_default.value!r})"
        )