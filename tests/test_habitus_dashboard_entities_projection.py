"""Projection contract tests for habitus_dashboard_entities.py — HA-417."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SRC = REPO_ROOT / "custom_components" / "pilotsuite" / "habitus_dashboard_entities.py"


def _find_class_source(tree: ast.AST, class_name: str) -> str | None:
    """Return the source lines for a class by searching its QualifiedName."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            start = node.lineno
            end = max(n.lineno for n in ast.walk(node) if hasattr(n, "lineno"))
            lines = SRC.read_text(encoding="utf-8").splitlines()
            return "\n".join(lines[start - 1 : end])
    return None


# --------------------------------------------------------------------------- #
# HD1: canonical pilotsuite_zone_{zone_id}_score unique_id for HabitusZoneScoreSensor
# --------------------------------------------------------------------------- #
def test_habitus_zone_score_sensor_uses_pilotsuite_unique_id_prefix():
    """HD1: HabitusZoneScoreSensor constructs pilotsuite_zone_{zone_id}_score."""
    content = SRC.read_text(encoding="utf-8")
    tree = ast.parse(content)

    src = _find_class_source(tree, "HabitusZoneScoreSensor")
    assert src is not None, "HD1 FAIL: HabitusZoneScoreSensor class not found"
    assert "pilotsuite_zone_" in src, (
        f"HD1 FAIL: 'pilotsuite_zone_' not found in HabitusZoneScoreSensor source"
    )
    assert "copilot_ha_zone_" not in src, (
        f"HD1 FAIL: stale 'copilot_ha_zone_' still present in HabitusZoneScoreSensor"
    )
    # Verify it's an f-string ( JoinedStr ) so the {zone_id} interpolation is preserved
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "HabitusZoneScoreSensor":
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Attribute) and target.attr == "_attr_unique_id":
                            assert isinstance(child.value, ast.JoinedStr), (
                                f"HD1 FAIL: _attr_unique_id is not an f-string"
                            )
                            assert "pilotsuite_zone_" in ast.unparse(child.value), (
                                f"HD1 FAIL: expected pilotsuite_zone_ prefix, got {ast.unparse(child.value)!r}"
                            )
                            return

    pytest.fail("HD1 FAIL: could not locate _attr_unique_id in HabitusZoneScoreSensor")


# --------------------------------------------------------------------------- #
# HD2: canonical pilotsuite_habitus_zone_status unique_id for HabitusZoneStatusSensor
# --------------------------------------------------------------------------- #
def test_habitus_zone_status_sensor_uses_pilotsuite_unique_id():
    """HD2: HabitusZoneStatusSensor uses pilotsuite_habitus_zone_status."""
    content = SRC.read_text(encoding="utf-8")
    tree = ast.parse(content)

    src = _find_class_source(tree, "HabitusZoneStatusSensor")
    assert src is not None, "HD2 FAIL: HabitusZoneStatusSensor class not found"
    assert "pilotsuite_habitus_zone_status" in src, (
        f"HD2 FAIL: 'pilotsuite_habitus_zone_status' not found in HabitusZoneStatusSensor source"
    )
    assert "copilot_ha_habitus_zone_status" not in src, (
        f"HD2 FAIL: stale copilot_ha_habitus_zone_status still present"
    )


# --------------------------------------------------------------------------- #
# HD3: canonical pilotsuite_habitus_mood_distribution unique_id
# --------------------------------------------------------------------------- #
def test_habitus_mood_distribution_sensor_uses_pilotsuite_unique_id():
    """HD3: HabitusMoodDistributionSensor uses pilotsuite_habitus_mood_distribution."""
    content = SRC.read_text(encoding="utf-8")
    tree = ast.parse(content)

    src = _find_class_source(tree, "HabitusMoodDistributionSensor")
    assert src is not None, "HD3 FAIL: HabitusMoodDistributionSensor class not found"
    assert "pilotsuite_habitus_mood_distribution" in src, (
        f"HD3 FAIL: 'pilotsuite_habitus_mood_distribution' not found"
    )
    assert "copilot_ha_habitus_mood_distribution" not in src, (
        f"HD3 FAIL: stale copilot_ha_habitus_mood_distribution still present"
    )


# --------------------------------------------------------------------------- #
# HD4: canonical pilotsuite_habitus_current_mood unique_id
# --------------------------------------------------------------------------- #
def test_habitus_current_mood_sensor_uses_pilotsuite_unique_id():
    """HD4: HabitusCurrentMoodSensor uses pilotsuite_habitus_current_mood."""
    content = SRC.read_text(encoding="utf-8")
    tree = ast.parse(content)

    src = _find_class_source(tree, "HabitusCurrentMoodSensor")
    assert src is not None, "HD4 FAIL: HabitusCurrentMoodSensor class not found"
    assert "pilotsuite_habitus_current_mood" in src, (
        f"HD4 FAIL: 'pilotsuite_habitus_current_mood' not found"
    )
    assert "copilot_ha_habitus_current_mood" not in src, (
        f"HD4 FAIL: stale copilot_ha_habitus_current_mood still present"
    )


# --------------------------------------------------------------------------- #
# HD5: canonical pilotsuite_habitus_transitions unique_id
# --------------------------------------------------------------------------- #
def test_habitus_zone_transition_log_sensor_uses_pilotsuite_unique_id():
    """HD5: HabitusZoneTransitionLogSensor uses pilotsuite_habitus_transitions."""
    content = SRC.read_text(encoding="utf-8")
    tree = ast.parse(content)

    src = _find_class_source(tree, "HabitusZoneTransitionLogSensor")
    assert src is not None, "HD5 FAIL: HabitusZoneTransitionLogSensor class not found"
    assert "pilotsuite_habitus_transitions" in src, (
        f"HD5 FAIL: 'pilotsuite_habitus_transitions' not found"
    )
    assert "copilot_ha_habitus_transitions" not in src, (
        f"HD5 FAIL: stale copilot_ha_habitus_transitions still present"
    )


# --------------------------------------------------------------------------- #
# HD6: canonical pilotsuite_habitus_cards_yaml unique_id for HabitusCardsConfigText
# --------------------------------------------------------------------------- #
def test_habitus_cards_config_text_uses_pilotsuite_unique_id():
    """HD6: HabitusCardsConfigText uses pilotsuite_habitus_cards_yaml."""
    content = SRC.read_text(encoding="utf-8")
    tree = ast.parse(content)

    src = _find_class_source(tree, "HabitusCardsConfigText")
    assert src is not None, "HD6 FAIL: HabitusCardsConfigText class not found"
    assert "pilotsuite_habitus_cards_yaml" in src, (
        f"HD6 FAIL: 'pilotsuite_habitus_cards_yaml' not found"
    )
    assert "copilot_ha_habitus_cards_yaml" not in src, (
        f"HD6 FAIL: stale copilot_ha_habitus_cards_yaml still present"
    )


# --------------------------------------------------------------------------- #
# HD7: AST scan — no stale copilot_ha unique_id literals anywhere in the file
# --------------------------------------------------------------------------- #
def test_no_stale_copilot_ha_unique_id_literals_in_ast():
    """HD7: AST scan confirms zero stale copilot_ha unique_id literals remain."""
    content = SRC.read_text(encoding="utf-8")
    tree = ast.parse(content)

    stale: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name in (
            "HabitusZoneScoreSensor",
            "HabitusZoneStatusSensor",
            "HabitusMoodDistributionSensor",
            "HabitusCurrentMoodSensor",
            "HabitusZoneTransitionLogSensor",
            "HabitusCardsConfigText",
        ):
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name) and target.id == "_attr_unique_id":
                            val_repr = ast.unparse(child.value)
                            if "copilot_ha_" in val_repr:
                                stale.append(val_repr)

    assert not stale, f"HD7 FAIL: stale copilot_ha unique_id literals still present: {stale}"
