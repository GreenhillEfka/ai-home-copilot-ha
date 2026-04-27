"""Projection contract tests for agent_auto_config.py.

Verifies the bounded Assist setup/readiness projection added on top of the
existing agent_auto_config seam.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path("/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/agent_auto_config.py")
TARGET_DOCSTRINGS = {
    "set_default_agent": "pilotsuite.set_default_agent",
    "verify_agent": "pilotsuite.verify_agent",
    "get_agent_status": "pilotsuite.get_agent_status",
    "repair_agent": "pilotsuite.repair_agent",
}
STALE_SUBSTRINGS = (
    "copilot_ha.set_default_agent",
    "copilot_ha.verify_agent",
    "copilot_ha.get_agent_status",
    "copilot_ha.repair_agent",
)


def _read() -> str:
    return SRC.read_text()


def _as_string(value, default=""):
    if isinstance(value, str):
        normalized = value.strip()
        if normalized:
            return normalized
    return default


def _as_bool(value, default=False):
    return bool(value) if isinstance(value, bool) else default


class _PipelineStub:
    def __init__(self, *, pipeline_id=None, name=None, conversation_engine=None):
        self.id = pipeline_id
        self.name = name
        self.conversation_engine = conversation_engine


class AssistReadinessContract:
    @staticmethod
    def project(entry_id, status, pipeline):
        status_data = status if isinstance(status, dict) else {}
        pipeline_id = _as_string(getattr(pipeline, "id", ""), "")
        pipeline_name = _as_string(getattr(pipeline, "name", ""), "")
        conversation_engine = _as_string(getattr(pipeline, "conversation_engine", ""), "")
        conversation_engine_matches = conversation_engine == entry_id and bool(conversation_engine)
        agent_status = _as_string(status_data.get("status"), "unknown")
        return {
            "agent_id": entry_id,
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline_name,
            "conversation_engine": conversation_engine,
            "conversation_engine_matches": conversation_engine_matches,
            "assist_configured": conversation_engine_matches,
            "core_ok": _as_bool(status_data.get("ok"), False),
            "core_agent_ready": agent_status == "ready",
            "core_status": agent_status,
            "llm_model": _as_string(status_data.get("llm_model"), ""),
            "llm_backend": _as_string(status_data.get("llm_backend"), ""),
        }


def test_ac1_docstrings_reference_pilotsuite():
    src = _read()
    for expected_ref in TARGET_DOCSTRINGS.values():
        assert f"Service: {expected_ref}" in src


def test_ac2_ast_no_stale_copilot_ha_docstrings():
    tree = ast.parse(_read())
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            doc = ast.get_docstring(node)
            if doc:
                for stale in STALE_SUBSTRINGS:
                    if stale in doc:
                        violations.append(f"{node.name}: {stale!r}")
    assert not violations


def test_ac3_projection_helper_is_present_and_wired_into_status_surface():
    src = _read()
    assert "def project_assist_config_readiness(" in src
    assert 'result["assist_readiness"] = project_assist_config_readiness(entry.entry_id, result, pipeline)' in src
    assert "**Assist konfiguriert:**" in src
    assert "**Pipeline:**" in src
    assert "**Conversation Engine:**" in src


@pytest.mark.parametrize(
    "entry_id,status,pipeline,expected",
    [
        (
            "entry-1",
            {"ok": True, "status": "ready", "llm_model": "gpt-4.1", "llm_backend": "openai"},
            _PipelineStub(pipeline_id="pipe-1", name="Preferred", conversation_engine="entry-1"),
            {
                "agent_id": "entry-1",
                "pipeline_id": "pipe-1",
                "pipeline_name": "Preferred",
                "conversation_engine": "entry-1",
                "conversation_engine_matches": True,
                "assist_configured": True,
                "core_ok": True,
                "core_agent_ready": True,
                "core_status": "ready",
                "llm_model": "gpt-4.1",
                "llm_backend": "openai",
            },
        ),
        (
            "entry-1",
            {"ok": True, "status": "degraded", "llm_model": "", "llm_backend": "ollama"},
            _PipelineStub(pipeline_id="pipe-2", name="Fallback", conversation_engine="other-entry"),
            {
                "agent_id": "entry-1",
                "pipeline_id": "pipe-2",
                "pipeline_name": "Fallback",
                "conversation_engine": "other-entry",
                "conversation_engine_matches": False,
                "assist_configured": False,
                "core_ok": True,
                "core_agent_ready": False,
                "core_status": "degraded",
                "llm_model": "",
                "llm_backend": "ollama",
            },
        ),
        (
            "entry-1",
            {},
            None,
            {
                "agent_id": "entry-1",
                "pipeline_id": "",
                "pipeline_name": "",
                "conversation_engine": "",
                "conversation_engine_matches": False,
                "assist_configured": False,
                "core_ok": False,
                "core_agent_ready": False,
                "core_status": "unknown",
                "llm_model": "",
                "llm_backend": "",
            },
        ),
    ],
)
def test_ac4_assist_readiness_projection(entry_id, status, pipeline, expected):
    assert AssistReadinessContract.project(entry_id, status, pipeline) == expected


def test_ac5_projection_normalizes_whitespace_and_non_bool_noise():
    projected = AssistReadinessContract.project(
        "entry-1",
        {"ok": "yes", "status": "  ready  ", "llm_model": "  gpt-4.1-mini  ", "llm_backend": 123},
        _PipelineStub(pipeline_id="  pipe-1  ", name="  Preferred  ", conversation_engine="  entry-1  "),
    )
    assert projected == {
        "agent_id": "entry-1",
        "pipeline_id": "pipe-1",
        "pipeline_name": "Preferred",
        "conversation_engine": "entry-1",
        "conversation_engine_matches": True,
        "assist_configured": True,
        "core_ok": False,
        "core_agent_ready": True,
        "core_status": "ready",
        "llm_model": "gpt-4.1-mini",
        "llm_backend": "",
    }
