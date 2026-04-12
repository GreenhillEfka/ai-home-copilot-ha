"""
Contract test: styx-mood-card.js Projection Parity (HA-377)
Source-Guard for canonical pilotsuite entity references in the mood card frontend.
"""
import re

def test_styx_mood_card_pilotsuite_entity_in_docstring():
    """SM1: Docstring references canonical sensor.pilotsuite_mood entities."""
    path = "custom_components/pilotsuite/www/styx-mood-card.js"
    content = open(path, encoding="utf-8").read()
    assert re.search(r"sensor\.pilotsuite_mood\b", content), \
        "Docstring must reference sensor.pilotsuite_mood"
    assert re.search(r"sensor\.pilotsuite_mood_confidence\b", content), \
        "Docstring must reference sensor.pilotsuite_mood_confidence"

def test_styx_mood_card_stubconfig_pilotsuite():
    """SM2: StubConfig returns canonical sensor.pilotsuite_mood entity."""
    path = "custom_components/pilotsuite/www/styx-mood-card.js"
    content = open(path, encoding="utf-8").read()
    match = re.search(r"getStubConfig\s*\(\s*\)\s*\{\s*return\s*\{\s*entity:\s*'([^']+)'\s*\}\s*;", content)
    assert match, "getStubConfig must return a stub config"
    entity = match.group(1)
    assert entity == "sensor.pilotsuite_mood", \
        f"StubConfig entity must be sensor.pilotsuite_mood, got {entity}"

def test_styx_mood_card_no_stale_copilot_ha_mood_strings():
    """SM3: No stale copilot_ha_mood or copilot_ha_mood_confidence strings in source."""
    path = "custom_components/pilotsuite/www/styx-mood-card.js"
    content = open(path, encoding="utf-8").read()
    stale_mood = re.search(r"\bsensor\.copilot_ha_mood\b(?!\s*_confidence)", content)
    stale_conf = re.search(r"\bsensor\.copilot_ha_mood_confidence\b", content)
    assert not stale_mood, "Source must not contain stale sensor.copilot_ha_mood (except as _confidence)"
    assert not stale_conf, "Source must not contain stale sensor.copilot_ha_mood_confidence"

def test_styx_mood_card_priority_order_pilotsuite_first():
    """SM4: _findEntity candidate order puts pilotsuite before copilot_ha."""
    path = "custom_components/pilotsuite/www/styx-mood-card.js"
    content = open(path, encoding="utf-8").read()
    # pilotsuite must appear before copilot_ha in the _findEntity candidates array
    p_idx = content.index("sensor.pilotsuite_${suffix}")
    c_idx = content.index("sensor.copilot_ha_${suffix}")
    assert p_idx < c_idx, \
        "_findEntity must list pilotsuite candidate before copilot_ha for priority"