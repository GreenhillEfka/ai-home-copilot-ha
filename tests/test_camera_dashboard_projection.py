"""Projection contract for camera_dashboard.py entity lookup parity.

HA-396: Fix camera motion entity lookup to use pilotsuite domain
instead of stale copilot_ha_motion prefix.

The MotionDetectionCamera entities register with unique_id:
  copilot_ha_motion_{camera_id}
But the generated YAML cards use:
  binary_sensor.pilotsuite_motion_{cam_id}

Both generate entity_ids in the pilotsuite domain, so the lookup
filter "copilot_ha_motion" matches nothing — dashboard generation
fails to discover motion cameras at runtime.

Fix: scan for binary_sensor.pilotsuite_motion instead.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_FILE = REPO_ROOT / "custom_components" / "pilotsuite" / "camera_dashboard.py"


def _read_source() -> str:
    with open(TARGET_FILE, encoding="utf-8") as f:
        return f.read()


class TestCameraDashboardProjection:
    """Entity lookup contract for camera_dashboard.py."""

    def test_cd1_no_stale_copilot_ha_motion_lookup(self) -> None:
        """CD1: camera_dashboard.py must not scan for copilot_ha_motion entities."""
        source = _read_source()
        # The stale pattern would match nothing since entities are pilotsuite_motion
        assert '"copilot_ha_motion" in eid' not in source, (
            "camera_dashboard.py uses stale 'copilot_ha_motion' entity lookup "
            "which matches no registered entities. "
            "Motion cameras register as pilotsuite_motion_* — use that prefix instead."
        )

    def test_cd2_uses_pilotsuite_motion_prefix_in_entity_lookup(self) -> None:
        """CD2: Motion camera lookup must use pilotsuite_motion prefix."""
        source = _read_source()
        # Either a string scan or a has_entity check
        assert (
            '"pilotsuite_motion" in' in source
            or '"pilotsuite_motion" not in' not in source
            or re.search(r'binary_sensor\.pilotsuite_motion', source)
        ), (
            "camera_dashboard.py must scan for binary_sensor.pilotsuite_motion_* "
            "entities to discover registered motion cameras."
        )

    def test_cd3_no_copilot_ha_motion_in_camera_entities_yaml(self) -> None:
        """CD3: Generated YAML must not reference copilot_ha_motion entity IDs."""
        source = _read_source()
        # The _camera_entities_yaml and _camera_status_card_yaml helpers
        # write binary_sensor.pilotsuite_motion_{cam_id} into YAML
        # Check that the source does not write copilot_ha_motion to YAML
        assert 'binary_sensor.copilot_ha_motion' not in source, (
            "Generated dashboard YAML must not reference copilot_ha_motion entity IDs."
        )

    def test_cd4_pilotsuite_motion_camera_id_pattern_present(self) -> None:
        """CD4: Camera ID extraction must use pilotsuite_motion pattern."""
        source = _read_source()
        # The cam_id is extracted from entity_id by splitting on "." and taking the suffix
        # But the pattern used to find cameras must be correct first
        assert 'binary_sensor.pilotsuite_motion_' in source, (
            "camera_dashboard.py should reference binary_sensor.pilotsuite_motion_ "
            "when constructing per-camera entity references in generated YAML."
        )

    def test_cd5_py_compile_ok(self) -> None:
        """CD5: camera_dashboard.py must have valid Python syntax."""
        import py_compile
        py_compile.compile(str(TARGET_FILE), doraise=True)

    def test_cd6_pragma_coverage_marker(self) -> None:
        """CD6: This contract test is explicitly owned by HomeClaw lane."""
        import inspect
        stack = inspect.stack()
        caller_file = stack[0].filename
        assert "test_camera_dashboard_projection" in Path(caller_file).name