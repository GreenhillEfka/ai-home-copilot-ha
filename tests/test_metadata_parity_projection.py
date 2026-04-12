"""Metadata parity guard for PilotSuite HA.

Verifies the HACS / manifest / VERSION files stay aligned on the landed
repo contract and do not drift back to stale metadata.
"""
from __future__ import annotations

import json
from pathlib import Path


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


def test_metadata_versions_and_names_are_aligned() -> None:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    root_manifest = _load_json(ROOT_MANIFEST)
    component_manifest = _load_json(COMPONENT_MANIFEST)

    assert version == EXPECTED_VERSION
    assert root_manifest["version"] == version
    assert component_manifest["version"] == version
    assert root_manifest["domain"] == "pilotsuite"
    assert component_manifest["domain"] == "pilotsuite"
    assert root_manifest["name"] == "PilotSuite HA"
    assert component_manifest["name"] == "PilotSuite HA"


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
