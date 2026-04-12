"""Metadata parity guard for PilotSuite HA.

Verifies the HACS / manifest / VERSION files stay aligned on the landed
repo contract and do not drift back to stale metadata.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = REPO_ROOT / "VERSION"
ROOT_MANIFEST = REPO_ROOT / "manifest.json"
COMPONENT_MANIFEST = REPO_ROOT / "custom_components" / "pilotsuite" / "manifest.json"
COMPONENT_VERSION_STUB = REPO_ROOT / "custom_components" / "pilotsuite" / "VERSION"
HACS_FILE = REPO_ROOT / "hacs.json"
COMPONENT_HACS_FILE = REPO_ROOT / "custom_components" / "pilotsuite" / "hacs.json"
EXPECTED_VERSION = "20.0.8"
EXPECTED_HOMEASSISTANT = "2024.4.0"
EXPECTED_REPO_URL = "https://github.com/GreenhillEfka/pilotsuite-styx-ha"
EXPECTED_ROOT_MANIFEST = {
    "domain": "pilotsuite",
    "name": "PilotSuite HA",
    "codeowners": ["@GreenhillEfka"],
    "config_flow": True,
    "iot_class": "local_polling",
    "version": EXPECTED_VERSION,
}
EXPECTED_HACS = {
    "name": "PilotSuite HA",
    "domain": "pilotsuite",
    "content_in_root": False,
    "render_readme": True,
    "homeassistant": EXPECTED_HOMEASSISTANT,
    "zip_release": False,
    "filename": "pilotsuite-styx-ha.zip",
}
EXPECTED_COMPONENT_MANIFEST_KEYS = {
    "after_dependencies",
    "codeowners",
    "config_flow",
    "dependencies",
    "documentation",
    "domain",
    "homeassistant",
    "icon",
    "integration_type",
    "iot_class",
    "issue_tracker",
    "name",
    "requirements",
    "version",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _git_show_text(revision: str, path: str) -> str | None:
    result = _git("show", f"{revision}:{path}")
    if result.returncode == 0:
        return result.stdout
    stderr = result.stderr.lower()
    if "does not exist in" in stderr or "exists on disk, but not in" in stderr:
        return None
    raise AssertionError(f"git show {revision}:{path} failed: {result.stderr.strip()}")


def test_metadata_versions_and_names_are_aligned() -> None:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    root_manifest = _load_json(ROOT_MANIFEST)
    component_manifest = _load_json(COMPONENT_MANIFEST)

    assert version == EXPECTED_VERSION
    assert root_manifest == EXPECTED_ROOT_MANIFEST
    assert root_manifest["version"] == version
    assert component_manifest["version"] == version
    assert root_manifest["domain"] == "pilotsuite"
    assert component_manifest["domain"] == "pilotsuite"
    assert root_manifest["name"] == "PilotSuite HA"
    assert component_manifest["name"] == "PilotSuite HA"


def test_root_manifest_stays_in_release_lockstep_with_component_manifest() -> None:
    root_manifest = _load_json(ROOT_MANIFEST)
    component_manifest = _load_json(COMPONENT_MANIFEST)
    mirrored_release_fields = {
        field: component_manifest[field]
        for field in ("domain", "name", "codeowners", "config_flow", "iot_class", "version")
    }

    assert root_manifest == EXPECTED_ROOT_MANIFEST
    assert root_manifest == mirrored_release_fields


def test_manifest_contract_matches_hacs_release_metadata() -> None:
    root_manifest = _load_json(ROOT_MANIFEST)
    component_manifest = _load_json(COMPONENT_MANIFEST)
    hacs = _load_json(HACS_FILE)
    component_hacs = _load_json(COMPONENT_HACS_FILE)
    repo_url = component_manifest["documentation"]
    repo_slug = repo_url.rstrip("/").rsplit("/", 1)[-1]

    assert root_manifest["iot_class"] == "local_polling"
    assert component_manifest["iot_class"] == "local_polling"
    assert root_manifest["config_flow"] is True
    assert component_manifest["config_flow"] is True
    assert repo_url == EXPECTED_REPO_URL
    assert component_manifest["issue_tracker"] == f"{repo_url}/issues"
    assert component_manifest["codeowners"] == ["@GreenhillEfka"]
    assert component_manifest["homeassistant"] == EXPECTED_HOMEASSISTANT

    assert hacs == component_hacs
    assert hacs["name"] == "PilotSuite HA"
    assert hacs["domain"] == component_manifest["domain"]
    assert hacs["domain"] == root_manifest["domain"]
    assert hacs["content_in_root"] is False
    assert hacs["render_readme"] is True
    assert hacs["zip_release"] is False
    assert hacs["filename"] == f"{repo_slug}.zip"
    assert hacs["homeassistant"] == component_manifest["homeassistant"]


def test_hacs_and_component_manifest_match_expected_release_contract() -> None:
    component_manifest = _load_json(COMPONENT_MANIFEST)
    hacs = _load_json(HACS_FILE)
    component_hacs = _load_json(COMPONENT_HACS_FILE)

    assert hacs == EXPECTED_HACS
    assert component_hacs == EXPECTED_HACS
    assert set(component_manifest) == EXPECTED_COMPONENT_MANIFEST_KEYS
    assert component_manifest["documentation"] == EXPECTED_REPO_URL
    assert component_manifest["issue_tracker"] == f"{EXPECTED_REPO_URL}/issues"
    assert component_manifest["version"] == EXPECTED_VERSION
    assert component_manifest["homeassistant"] == EXPECTED_HOMEASSISTANT
    assert component_manifest["dependencies"] == [
        "conversation",
        "history",
        "http",
        "recorder",
        "stt",
        "tag",
        "tts",
        "webhook",
    ]
    assert component_manifest["after_dependencies"] == ["assist_pipeline"]
    assert component_manifest["requirements"] == []


def test_component_version_stub_is_absent() -> None:
    assert COMPONENT_VERSION_STUB.exists() is False


def test_metadata_source_guard_blocks_stale_values() -> None:
    text = "\n".join(
        [
            VERSION_FILE.read_text(encoding="utf-8"),
            ROOT_MANIFEST.read_text(encoding="utf-8"),
            COMPONENT_MANIFEST.read_text(encoding="utf-8"),
            HACS_FILE.read_text(encoding="utf-8"),
            COMPONENT_HACS_FILE.read_text(encoding="utf-8"),
            (REPO_ROOT / "custom_components" / "pilotsuite" / "const.py").read_text(encoding="utf-8"),
            (REPO_ROOT / "custom_components" / "pilotsuite" / "config_flow.py").read_text(encoding="utf-8"),
        ]
    )

    assert '"version": "1.0.0"' not in text
    assert '"version": "16.0.0"' not in text
    assert '"version": "20.0.5"' not in text
    assert '"name": "PilotSuite"' not in text
    assert '"iot_class": "local_push"' not in text
    assert '"zip_release": true' not in text
    assert '"filename": "copilot-ha.zip"' not in text
    assert '"homeassistant": "2024.1.0"' not in text
    assert '"domain": "copilot_ha"' not in text
    # HA-290 / HA-292 / HA-374: block legacy-domain and known behind-1 metadata rollback values.
    assert 'DOMAIN = "copilot_ha"' not in text
    assert 'CONFIG_FLOW_DOMAIN = "copilot_ha"' not in text


def test_branch_recheck_against_origin_main_blocks_documented_metadata_and_config_rollback() -> None:
    git_probe = _git("rev-parse", "--git-dir")
    if git_probe.returncode != 0:
        pytest.skip("git-backed branch recheck requires repository metadata")

    behind_ahead = _git("rev-list", "--left-right", "--count", "origin/main...HEAD")
    assert behind_ahead.returncode == 0
    assert behind_ahead.stdout.strip().startswith("1\t")

    upstream_commit = _git("log", "--format=%H %s", "-1", "HEAD..origin/main")
    assert upstream_commit.returncode == 0
    assert upstream_commit.stdout.strip().startswith("9b934614")
    assert "restore missing setup-flow files from known-good state" in upstream_commit.stdout

    head_version = _git_show_text("HEAD", "VERSION")
    origin_version = _git_show_text("origin/main", "VERSION")
    head_root_manifest = _git_show_text("HEAD", "manifest.json")
    origin_root_manifest = _git_show_text("origin/main", "manifest.json")
    head_root_hacs = _git_show_text("HEAD", "hacs.json")
    origin_root_hacs = _git_show_text("origin/main", "hacs.json")
    head_component_manifest = _git_show_text("HEAD", "custom_components/pilotsuite/manifest.json")
    origin_component_manifest = _git_show_text("origin/main", "custom_components/pilotsuite/manifest.json")
    head_component_hacs = _git_show_text("HEAD", "custom_components/pilotsuite/hacs.json")
    origin_component_hacs = _git_show_text("origin/main", "custom_components/pilotsuite/hacs.json")
    head_const = _git_show_text("HEAD", "custom_components/pilotsuite/const.py")
    origin_const = _git_show_text("origin/main", "custom_components/pilotsuite/const.py")
    head_snapshot = _git_show_text("HEAD", "custom_components/pilotsuite/config_snapshot.py")
    origin_snapshot = _git_show_text("origin/main", "custom_components/pilotsuite/config_snapshot.py")

    assert head_version == "20.0.8\n"
    assert origin_version == "20.0.5\n"
    assert '"version": "20.0.8"' in (head_root_manifest or "")
    assert '"version": "20.0.5"' in (origin_root_manifest or "")
    assert '"version": "20.0.8"' in (head_component_manifest or "")
    assert '"version": "20.0.5"' in (origin_component_manifest or "")

    assert '"name": "PilotSuite HA"' in (head_root_hacs or "")
    assert '"domain": "pilotsuite"' in (head_root_hacs or "")
    assert '"filename": "pilotsuite-styx-ha.zip"' in (head_root_hacs or "")
    assert '"homeassistant": "2024.4.0"' in (head_root_hacs or "")
    assert '"name": "PilotSuite"' in (origin_root_hacs or "")
    assert '"domain": "pilotsuite"' not in (origin_root_hacs or "")
    assert '"filename": "pilotsuite-styx-ha.zip"' not in (origin_root_hacs or "")
    assert '"homeassistant": "2024.4.0"' not in (origin_root_hacs or "")
    assert '"homeassistant": "2024.1.0"' in (origin_root_hacs or "")

    assert json.loads(head_component_hacs or "{}") == EXPECTED_HACS
    assert origin_component_hacs is None

    assert 'DOMAIN = "pilotsuite"' in (head_const or "")
    assert 'DOMAIN = "copilot_ha"' in (origin_const or "")
    assert '"schema": "pilotsuite_config_snapshot"' in (head_snapshot or "")
    assert '"schema": "copilot_ha_config_snapshot"' in (origin_snapshot or "")
    assert 'EXPORT_DIR = "/config/pilotsuite-styx/exports"' in (head_snapshot or "")
    assert 'EXPORT_DIR = "/config/copilot_ha/exports"' in (origin_snapshot or "")
    assert 'PUBLISH_DIR = "/config/www/pilotsuite-styx"' in (head_snapshot or "")
    assert 'PUBLISH_DIR = "/config/www/copilot_ha"' in (origin_snapshot or "")


def test_branch_recheck_against_origin_main_blocks_remaining_config_surface_rollback() -> None:
    git_probe = _git("rev-parse", "--git-dir")
    if git_probe.returncode != 0:
        pytest.skip("git-backed branch recheck requires repository metadata")

    behind_ahead = _git("rev-list", "--left-right", "--count", "origin/main...HEAD")
    assert behind_ahead.returncode == 0
    assert behind_ahead.stdout.strip().startswith("1\t")

    upstream_commit = _git("log", "--format=%H %s", "-1", "HEAD..origin/main")
    assert upstream_commit.returncode == 0
    assert upstream_commit.stdout.strip().startswith("9b934614")
    assert "restore missing setup-flow files from known-good state" in upstream_commit.stdout

    head_init = _git_show_text("HEAD", "custom_components/pilotsuite/__init__.py")
    origin_init = _git_show_text("origin/main", "custom_components/pilotsuite/__init__.py")
    head_tags_flow = _git_show_text("HEAD", "custom_components/pilotsuite/config_tags_flow.py")
    origin_tags_flow = _git_show_text("origin/main", "custom_components/pilotsuite/config_tags_flow.py")

    assert 'CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)' in (head_init or "")
    assert 'from .core.runtime import CopilotRuntime' in (head_init or "")
    assert '"voice_context": (".core.modules.voice_context", "VoiceContextModule")' in (head_init or "")
    assert 'async_register_all_services' in (head_init or "")
    assert 'hass.components.frontend.async_register_built_in_panel' not in (head_init or "")

    assert 'hass.components.frontend.async_register_built_in_panel' in (origin_init or "")
    assert "config={'url': '/api/hassio_ingress/pilotsuite_core/'}" in (origin_init or "")
    assert 'return True' in (origin_init or "")
    assert 'CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)' not in (origin_init or "")
    assert 'from .core.runtime import CopilotRuntime' not in (origin_init or "")

    assert 'from .const import DOMAIN' in (head_tags_flow or "")
    assert 'data = flow.hass.data.get(DOMAIN, {}).get(entry_id)' in (head_tags_flow or "")
    assert 'data = flow.hass.data.get("copilot_ha", {}).get(entry_id, {})' in (head_tags_flow or "")

    assert 'from .const import DOMAIN' not in (origin_tags_flow or "")
    assert 'data = flow.hass.data.get(DOMAIN, {}).get(entry_id)' not in (origin_tags_flow or "")
    assert 'data = flow.hass.data.get("copilot_ha", {}).get(entry_id, {})' in (origin_tags_flow or "")
