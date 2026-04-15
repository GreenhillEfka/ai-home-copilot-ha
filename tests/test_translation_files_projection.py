"""Contract tests for translation file copilot_ha -> pilotsuite parity.

HA-481: Align translation file stale copilot_ha/ www path strings with pilotsuite.
Slice: translations/en.json + translations/de.json + strings.json generate_dashboard
      and publish_dashboard description strings.
"""

import json
import pytest

# Files under test
TRANSLATION_FILES = [
    "custom_components/pilotsuite/translations/en.json",
    "custom_components/pilotsuite/translations/de.json",
    "custom_components/pilotsuite/strings.json",
]


def _load_json(path):
    with open(path) as f:
        return json.load(f)


# --- T1: en.json generate_dashboard description ---
def test_en_generate_dashboard_no_stale_copilot_ha_path():
    data = _load_json(TRANSLATION_FILES[0])
    desc = data["options"]["step"]["generate_dashboard"]["description"]
    assert "copilot_ha/" not in desc, f"stale copilot_ha/ path in en generate_dashboard: {desc}"


def test_en_generate_dashboard_uses_canonical_pilotsuite():
    data = _load_json(TRANSLATION_FILES[0])
    desc = data["options"]["step"]["generate_dashboard"]["description"]
    assert "pilotsuite/" in desc, f"missing canonical pilotsuite/ in en generate_dashboard: {desc}"


# --- T2: en.json publish_dashboard description ---
def test_en_publish_dashboard_no_stale_www_copilot_ha_path():
    data = _load_json(TRANSLATION_FILES[0])
    desc = data["options"]["step"]["publish_dashboard"]["description"]
    assert "www/copilot_ha/" not in desc, f"stale www/copilot_ha/ path in en publish_dashboard: {desc}"


def test_en_publish_dashboard_uses_canonical_www_pilotsuite():
    data = _load_json(TRANSLATION_FILES[0])
    desc = data["options"]["step"]["publish_dashboard"]["description"]
    assert "www/pilotsuite/" in desc, f"missing canonical www/pilotsuite/ in en publish_dashboard: {desc}"


# --- T3: de.json generate_dashboard description ---
def test_de_generate_dashboard_no_stale_copilot_ha_path():
    data = _load_json(TRANSLATION_FILES[1])
    desc = data["options"]["step"]["generate_dashboard"]["description"]
    assert "copilot_ha/" not in desc, f"stale copilot_ha/ path in de generate_dashboard: {desc}"


def test_de_generate_dashboard_uses_canonical_pilotsuite():
    data = _load_json(TRANSLATION_FILES[1])
    desc = data["options"]["step"]["generate_dashboard"]["description"]
    assert "pilotsuite/" in desc, f"missing canonical pilotsuite/ in de generate_dashboard: {desc}"


# --- T4: de.json publish_dashboard description ---
def test_de_publish_dashboard_no_stale_www_copilot_ha_path():
    data = _load_json(TRANSLATION_FILES[1])
    desc = data["options"]["step"]["publish_dashboard"]["description"]
    assert "www/copilot_ha/" not in desc, f"stale www/copilot_ha/ path in de publish_dashboard: {desc}"


def test_de_publish_dashboard_uses_canonical_www_pilotsuite():
    data = _load_json(TRANSLATION_FILES[1])
    desc = data["options"]["step"]["publish_dashboard"]["description"]
    assert "www/pilotsuite/" in desc, f"missing canonical www/pilotsuite/ in de publish_dashboard: {desc}"


# --- T5: strings.json generate_dashboard description ---
def test_strings_generate_dashboard_no_stale_copilot_ha_path():
    data = _load_json(TRANSLATION_FILES[2])
    desc = data["options"]["step"]["generate_dashboard"]["description"]
    assert "copilot_ha/" not in desc, f"stale copilot_ha/ path in strings.json generate_dashboard: {desc}"


def test_strings_generate_dashboard_uses_canonical_pilotsuite():
    data = _load_json(TRANSLATION_FILES[2])
    desc = data["options"]["step"]["generate_dashboard"]["description"]
    assert "pilotsuite/" in desc, f"missing canonical pilotsuite/ in strings.json generate_dashboard: {desc}"


# --- T6: strings.json publish_dashboard description ---
def test_strings_publish_dashboard_no_stale_www_copilot_ha_path():
    data = _load_json(TRANSLATION_FILES[2])
    desc = data["options"]["step"]["publish_dashboard"]["description"]
    assert "www/copilot_ha/" not in desc, f"stale www/copilot_ha/ path in strings.json publish_dashboard: {desc}"


def test_strings_publish_dashboard_uses_canonical_www_pilotsuite():
    data = _load_json(TRANSLATION_FILES[2])
    desc = data["options"]["step"]["publish_dashboard"]["description"]
    assert "www/pilotsuite/" in desc, f"missing canonical www/pilotsuite/ in strings.json publish_dashboard: {desc}"