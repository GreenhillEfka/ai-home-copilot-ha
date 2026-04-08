"""Metadata parity guard for PilotSuite HA (HA-217, HA-229).

Verifies the HACS / manifest / VERSION files stay aligned on the landed
v20.0.0 repo contract and do not drift back to stale metadata.
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


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_metadata_versions_and_names_are_aligned() -> None:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    root_manifest = _load_json(ROOT_MANIFEST)
    component_manifest = _load_json(COMPONENT_MANIFEST)

    assert version == "20.0.5"
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

    assert root_manifest["iot_class"] == "local_polling"
    assert component_manifest["iot_class"] == "local_polling"
    assert root_manifest["config_flow"] is True
    assert component_manifest["config_flow"] is True
    assert component_manifest["documentation"] == "https://github.com/GreenhillEfka/pilotsuite-styx-ha"
    assert component_manifest["codeowners"] == ["@GreenhillEfka"]

    assert hacs["name"] == "PilotSuite"
    assert hacs["content_in_root"] is False
    assert hacs["render_readme"] is True
    assert hacs["zip_release"] is False
    assert hacs["homeassistant"] == "2024.1.0"


def test_component_version_stub_is_absent() -> None:
    assert COMPONENT_VERSION_STUB.exists() is False



def test_metadata_source_guard_blocks_stale_values() -> None:
    text = "\n".join(
        [
            VERSION_FILE.read_text(encoding="utf-8"),
            ROOT_MANIFEST.read_text(encoding="utf-8"),
            COMPONENT_MANIFEST.read_text(encoding="utf-8"),
            HACS_FILE.read_text(encoding="utf-8"),
        ]
    )

    assert '"version": "1.0.0"' not in text
    assert '"version": "16.0.0"' not in text
    assert '"iot_class": "local_push"' not in text
    assert '"zip_release": true' not in text
