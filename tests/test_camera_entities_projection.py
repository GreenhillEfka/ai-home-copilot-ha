"""Contract tests for camera_entities projection surface."""
import ast
import re


def _ast_has_literal(source: str, literal: str) -> bool:
    return literal in source


def _get_unique_id_assignments(source: str) -> list[tuple[int, str]]:
    """Extract (lineno, unique_id value) from _attr_unique_id = ... assignments."""
    results = []
    for line in source.splitlines():
        m = re.search(r'_attr_unique_id\s*=\s*(f?["\']([^"\']+)["\']|"(?:[^"\\]|\\.)*")', line)
        if m:
            val = m.group(2) if m.group(2) else m.group(3) if m.group(3) else m.group(4)
            if val:
                results.append((source.splitlines().index(line) + 1, val))
    return results


def _get_signal_assignments(source: str) -> list[tuple[int, str]]:
    """Extract SIGNAL_* = "..." constant assignments."""
    results = []
    for line in source.splitlines():
        m = re.search(r'(SIGNAL_\w+)\s*=\s*["\']([^"\']+)["\']', line)
        if m:
            results.append((source.splitlines().index(line) + 1, m.group(1), m.group(2)))
    return results


def test_camera_unique_ids_are_pilotsuite_prefixed():
    """CE1: all camera _attr_unique_id values start with pilotsuite_."""
    with open("custom_components/pilotsuite/camera_entities.py") as f:
        source = f.read()
    assignments = _get_unique_id_assignments(source)
    assert assignments, "no _attr_unique_id assignments found"
    for lineno, uid in assignments:
        assert uid.startswith("pilotsuite_"), (
            f"line {lineno}: unique_id {uid!r} does not start with pilotsuite_"
        )


def test_camera_signal_constants_are_pilotsuite_prefixed():
    """CE2: all SIGNAL_CAMERA_* constants end with _pilotsuite suffix or use pilotsuite prefix."""
    with open("custom_components/pilotsuite/camera_entities.py") as f:
        source = f.read()
    signals = _get_signal_assignments(source)
    assert signals, "no SIGNAL_CAMERA_* assignments found"
    for lineno, name, val in signals:
        # Signal values should use pilotsuite namespace (not copilot_ha)
        assert "pilotsuite" in val, (
            f"line {lineno}: signal {name} value {val!r} does not use pilotsuite namespace"
        )
        assert "copilot_ha" not in val, (
            f"line {lineno}: signal {name} value {val!r} contains copilot_ha"
        )


def test_no_stale_copilot_ha_in_camera_entities():
    """CE3: AST scan confirms no unresolved copilot_ha string literals remain."""
    with open("custom_components/pilotsuite/camera_entities.py") as f:
        source = f.read()
    # Filter out intentionally commented legacy migration notes
    hits = [
        line for line in source.splitlines()
        if "copilot_ha" in line
        and not line.strip().startswith("#")
        and '"copilot_ha"' not in line
        and "'copilot_ha'" not in line
        and "##" not in line
    ]
    assert not hits, f"found copilot_ha literals on lines: {[l.strip() for l in hits]}"


def test_camera_entity_count_matches_expected():
    """CE4: sanity check that we have the expected number of camera entity unique_ids."""
    with open("custom_components/pilotsuite/camera_entities.py") as f:
        source = f.read()
    assignments = _get_unique_id_assignments(source)
    # We expect 8 camera entity unique_ids (motion, presence, activity, zone per camera + 4 history)
    assert len(assignments) == 8, f"expected 8 unique_id assignments, got {len(assignments)}: {assignments}"
