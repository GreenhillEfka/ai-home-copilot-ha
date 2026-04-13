"""
Contract test: pilotsuite_dashboard_v13*.yaml entity reference parity (HA-430).
Source-Guard for canonical pilotsuite sensor entity references in dashboard YAML.
"""
import re


def test_dashboard_v13_mood_entity_is_pilotsuite():
    """DV13-1: Mood card uses canonical sensor.pilotsuite_mood entity."""
    path = "custom_components/pilotsuite/dashboard/pilotsuite_dashboard_v13.yaml"
    content = open(path, encoding="utf-8").read()
    mood_entities = re.findall(r"entity:\s*(sensor\.copilot_ha_mood|sensor\.pilotsuite_mood)", content)
    assert mood_entities, "Must have at least one mood entity reference"
    for e in mood_entities:
        assert e == "sensor.pilotsuite_mood", \
            f"Mood card entity must be sensor.pilotsuite_mood, got {e}"


def test_dashboard_v13_no_stale_copilot_ha_mood():
    """DV13-2: No stale sensor.copilot_ha_mood references."""
    path = "custom_components/pilotsuite/dashboard/pilotsuite_dashboard_v13.yaml"
    content = open(path, encoding="utf-8").read()
    stale = re.search(r"\bsensor\.copilot_ha_mood\b", content)
    assert not stale, "Must not contain stale sensor.copilot_ha_mood in v13 dashboard"


def test_dashboard_v13_3tab_mood_entity_is_pilotsuite():
    """DV13-3: Mood card in 3tab dashboard uses canonical sensor.pilotsuite_mood."""
    path = "custom_components/pilotsuite/dashboard/pilotsuite_dashboard_v13_3tab.yaml"
    content = open(path, encoding="utf-8").read()
    mood_entities = re.findall(r"entity:\s*(sensor\.copilot_ha_mood|sensor\.pilotsuite_mood)", content)
    assert mood_entities, "Must have at least one mood entity reference"
    for e in mood_entities:
        assert e == "sensor.pilotsuite_mood", \
            f"Mood card entity must be sensor.pilotsuite_mood, got {e}"


def test_dashboard_v13_3tab_no_stale_copilot_ha_mood():
    """DV13-4: No stale sensor.copilot_ha_mood references in 3tab dashboard."""
    path = "custom_components/pilotsuite/dashboard/pilotsuite_dashboard_v13_3tab.yaml"
    content = open(path, encoding="utf-8").read()
    stale = re.search(r"\bsensor\.copilot_ha_mood\b", content)
    assert not stale, "Must not contain stale sensor.copilot_ha_mood in v13 3tab dashboard"
