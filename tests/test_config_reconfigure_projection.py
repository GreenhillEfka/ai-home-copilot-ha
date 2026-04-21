"""Projection contract for HA-CONFIG-301 reconfigure flow wiring."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FLOW = REPO_ROOT / "custom_components" / "pilotsuite" / "config_flow.py"
CONFIG_OPTIONS_FLOW = REPO_ROOT / "custom_components" / "pilotsuite" / "config_options_flow.py"


def _read(path: Path) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestConfigReconfigureProjection:
    """HA-CONFIG-301 source contracts for reconfigure zone/habitus flow."""

    def test_hc301_configflow_reconfigure_zones_seeds_runtime_context(self) -> None:
        source = _read(CONFIG_FLOW)
        assert 'options_flow.hass = self.hass' in source, (
            "ConfigFlow reconfigure_zones must pass hass into the delegated "
            "OptionsFlowHandler so zone editing keeps the live HA runtime context"
        )
        assert 'options_flow._entry = self._entry' in source, (
            "ConfigFlow reconfigure_zones must pass the active config entry into "
            "the delegated OptionsFlowHandler"
        )
        assert '"reconfigure": True' in source, (
            "ConfigFlow reconfigure_zones must mark delegated options flow as "
            "reconfigure-aware so back-navigation returns to the reconfigure menu"
        )

    def test_hc302_optionsflow_config_path_writes_to_configflow_stage(self) -> None:
        source = _read(CONFIG_OPTIONS_FLOW)
        assert 'from .config_flow import ConfigFlow' in source, (
            "OptionsFlow reconfigure connection path must import ConfigFlow for "
            "the shared ConfigFlow staging buffer"
        )
        assert 'ConfigFlow._reconfigure_data[key] = user_input[key]' in source, (
            "ConfigFlow-owned reconfigure connection edits must stage into "
            "ConfigFlow._reconfigure_data"
        )
        assert 'OptionsFlowHandler._pending_shared_params[key] = user_input[key]' in source, (
            "OptionsFlow-owned reconfigure connection edits must still stage into "
            "OptionsFlowHandler._pending_shared_params"
        )

    def test_hc303_no_cross_write_into_options_stage_from_configflow_branch(self) -> None:
        source = _read(CONFIG_OPTIONS_FLOW)
        config_branch = source.split('if from_options_flow:', 1)[1].split('# Show form with current values', 1)[0]
        else_branch = config_branch.split('else:', 1)[1]
        assert 'OptionsFlowHandler._pending_shared_params[key] = user_input[key]' not in else_branch, (
            "ConfigFlow branch must not write shared reconfigure params into the "
            "OptionsFlow-only staging buffer"
        )

    def test_hc304_reconfigure_sources_parse(self) -> None:
        for path in (CONFIG_FLOW, CONFIG_OPTIONS_FLOW):
            source = _read(path)
            try:
                ast.parse(source, filename=str(path))
            except SyntaxError as exc:
                pytest.fail(f"Syntax error in {path.name}: {exc}")
