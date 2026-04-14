"""Contract tests for pilotsuite_dashboard_v14.yaml entity references."""
import pathlib
import re
import pytest

YAML_FILE = pathlib.Path(
    "/config/clawd/team/worktrees/pilotsuite-styx-ha-current"
    "/custom_components/pilotsuite/dashboard/pilotsuite_dashboard_v14.yaml"
)

# Known-good entity_id → canonical pilotsuite name
EXPECTED_ENTITIES = {
    "sensor.pilotsuite_predictive_automation": "sensor.pilotsuite_predictive_automation",
    "sensor.pilotsuite_zone_scenes": "sensor.pilotsuite_zone_scenes",
    "button.pilotsuite_validate_habitus_zones_v2": "button.pilotsuite_validate_habitus_zones_v2",
    "sensor.pilotsuite_music_now_playing": "sensor.pilotsuite_music_now_playing",
    "sensor.pilotsuite_music_primary_area": "sensor.pilotsuite_music_primary_area",
    "sensor.pilotsuite_music_active_count": "sensor.pilotsuite_music_active_count",
    "sensor.pilotsuite_energy_insight": "sensor.pilotsuite_energy_insight",
    "sensor.pilotsuite_energy_recommendation": "sensor.pilotsuite_energy_recommendation",
    "button.pilotsuite_generate_pilotsuite_dashboard": "button.pilotsuite_generate_pilotsuite_dashboard",
    "button.pilotsuite_generate_habitus_dashboard": "button.pilotsuite_generate_habitus_dashboard",
    "button.pilotsuite_fetch_ha_errors": "button.pilotsuite_fetch_ha_errors",
    "button.pilotsuite_devlogs_fetch": "button.pilotsuite_devlogs_fetch",
    "button.pilotsuite_fetch_core_events": "button.pilotsuite_fetch_core_events",
}

STALE_PATTERNS = [
    re.compile(r"copilot_ha_zone_scenes[^a-z0-9]"),
    re.compile(r"copilot_ha_predictive_automation[^a-z0-9]"),
    re.compile(r"copilot_ha_music_now_playing[^a-z0-9]"),
    re.compile(r"copilot_ha_music_primary_area[^a-z0-9]"),
    re.compile(r"copilot_ha_music_active_count[^a-z0-9]"),
    re.compile(r"copilot_ha_energy_insight[^a-z0-9]"),
    re.compile(r"copilot_ha_energy_recommendation[^a-z0-9]"),
    re.compile(r"copilot_ha_validate_habitus_zones[^_]"),
    re.compile(r"copilot_ha_generate_pilotsuite_dashboard[^_]"),
    re.compile(r"copilot_ha_generate_habitus_dashboard[^_]"),
    re.compile(r"copilot_ha_fetch_ha_errors[^_]"),
    re.compile(r"copilot_ha_devlogs_fetch[^_]"),
    re.compile(r"copilot_ha_fetch_core_events[^_]"),
]


def _get_entity_refs() -> list[tuple[str, str]]:
    """Return (entity_id, line) tuples for entity: fields in the YAML."""
    refs = []
    text = YAML_FILE.read_text()
    for lineno, line in enumerate(text.splitlines(), 1):
        m = re.search(r"^\s+-\s+entity:\s+(\S+)", line)
        if m:
            refs.append((m.group(1), f"{lineno}: {line.strip()}"))
    return refs


class TestV14EntityRefs:
    """V14 dashboard entity reference contract."""

    def _test_canonical_entities(self):
        """VD14-1: All known entity refs point to canonical pilotsuite names."""
        refs = _get_entity_refs()
        canonical = {eid for eid in EXPECTED_ENTITIES}
        found = {eid for eid, _ in refs if eid in canonical}
        missing = canonical - found
        assert not missing, f"Expected canonical entities not found in YAML: {missing}"

    def _test_no_stale_copilot_ha_entity_refs(self):
        """VD14-2: No stale copilot_ha entity references remain."""
        text = YAML_FILE.read_text()
        stale_lines = []
        for lineno, line in enumerate(text.splitlines(), 1):
            for pattern in STALE_PATTERNS:
                if pattern.search(line):
                    stale_lines.append(f"{lineno}: {line.strip()}")
        assert not stale_lines, f"Stale copilot_ha entity refs found:\n" + "\n".join(stale_lines)

    def _test_ast_scan_no_stale_literals(self):
        """VD14-3: AST-level scan — no stale copilot_ha entity literals."""
        text = YAML_FILE.read_text()
        stale_matches = []
        # Match any copilot_ha entity ref (not in comments, not in www paths)
        for lineno, line in enumerate(text.splitlines(), 1):
            if re.search(r"#.*copilot_ha", line):
                continue  # skip comments
            if re.search(r"copilot_ha[_a-z]", line):
                stale_matches.append(f"{lineno}: {line.strip()}")
        assert not stale_matches, f"Unexpected copilot_ha literals:\n" + "\n".join(stale_matches)


# Aliases for pytest autodiscovery
def test_v14_canonical_entities():
    TestV14EntityRefs()._test_canonical_entities()

def test_v14_no_stale_entity_refs():
    TestV14EntityRefs()._test_no_stale_copilot_ha_entity_refs()

def test_v14_ast_no_stale_literals():
    TestV14EntityRefs()._test_ast_scan_no_stale_literals()
