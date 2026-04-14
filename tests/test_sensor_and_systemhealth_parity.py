"""Contract test: sensor.py CopilotVersionSensor + systemhealth_entities.py parity guards."""
import ast
import sys

SRC_SENSOR = "custom_components/pilotsuite/sensor.py"
SRC_SYS = "custom_components/pilotsuite/systemhealth_entities.py"


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


def _scan_unique_ids(src: str) -> list[tuple[int, str]]:
    """Find all _attr_unique_id assignments via AST."""
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "_attr_unique_id":
                    if isinstance(node.value, ast.Constant):
                        hits.append((node.lineno, node.value.value))
    return hits


# ─── HA-432 contract tests ───────────────────────────────────────────────────

def S1_unique_id_is_pilotsuite_version():
    """S1: CopilotVersionSensor _attr_unique_id is pilotsuite_version."""
    src = _read(SRC_SENSOR)
    hits = _scan_unique_ids(src)
    version_hits = [(ln, v) for ln, v in hits if "version" in v.lower()]
    assert len(version_hits) >= 1, f"Expected at least 1 _attr_unique_id with 'version', got {version_hits}"
    _, val = version_hits[0]
    assert val == "pilotsuite_version", f"Expected 'pilotsuite_version', got '{val}'"


def S2_no_stale_copilot_ha_in_sensor_unique_ids():
    """S2: No stale copilot_ha literal in sensor.py _attr_unique_id assignments."""
    src = _read(SRC_SENSOR)
    hits = _scan_unique_ids(src)
    stale = [(ln, v) for ln, v in hits if "copilot_ha" in v]
    assert len(stale) == 0, f"Stale copilot_ha unique_ids found at {stale}"


def S3_ast_scan_no_copilot_ha_in_sensor():
    """S3: AST scan — no unexplained copilot_ha string literals in sensor.py."""
    src = _read(SRC_SENSOR)
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "copilot_ha" in node.value:
                hits.append((node.lineno, node.value))
    assert len(hits) == 0, f"Unexplained copilot_ha literals at {hits}"


def SYS1_entities_total_unique_id():
    """SYS1: SystemHealthEntityCountSensor _attr_unique_id is pilotsuite_system_health_entities_total."""
    src = _read(SRC_SYS)
    hits = _scan_unique_ids(src)
    total_hits = [(ln, v) for ln, v in hits if "entities_total" in v]
    assert len(total_hits) >= 1, f"Expected at least 1 _attr_unique_id with 'entities_total', got {total_hits}"
    _, val = total_hits[0]
    assert val == "pilotsuite_system_health_entities_total", f"Expected 'pilotsuite_system_health_entities_total', got '{val}'"


def SYS2_sqlite_db_size_unique_id():
    """SYS2: SystemHealthSqliteDbSizeSensor _attr_unique_id is pilotsuite_system_health_sqlite_db_size."""
    src = _read(SRC_SYS)
    hits = _scan_unique_ids(src)
    db_hits = [(ln, v) for ln, v in hits if "sqlite_db_size" in v]
    assert len(db_hits) >= 1, f"Expected at least 1 _attr_unique_id with 'sqlite_db_size', got {db_hits}"
    _, val = db_hits[0]
    assert val == "pilotsuite_system_health_sqlite_db_size", f"Expected 'pilotsuite_system_health_sqlite_db_size', got '{val}'"


def SYS3_no_stale_copilot_ha_in_systemhealth_unique_ids():
    """SYS3: No stale copilot_ha literal in systemhealth_entities.py _attr_unique_id assignments."""
    src = _read(SRC_SYS)
    hits = _scan_unique_ids(src)
    stale = [(ln, v) for ln, v in hits if "copilot_ha" in v]
    assert len(stale) == 0, f"Stale copilot_ha unique_ids found at {stale}"


def SYS4_ast_scan_no_copilot_ha_in_systemhealth():
    """SYS4: AST scan — no unexplained copilot_ha string literals in systemhealth_entities.py."""
    src = _read(SRC_SYS)
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "copilot_ha" in node.value:
                hits.append((node.lineno, node.value))
    assert len(hits) == 0, f"Unexplained copilot_ha literals at {hits}"


# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        S1_unique_id_is_pilotsuite_version,
        S2_no_stale_copilot_ha_in_sensor_unique_ids,
        S3_ast_scan_no_copilot_ha_in_sensor,
        SYS1_entities_total_unique_id,
        SYS2_sqlite_db_size_unique_id,
        SYS3_no_stale_copilot_ha_in_systemhealth_unique_ids,
        SYS4_ast_scan_no_copilot_ha_in_systemhealth,
    ]
    failed = []
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed.append(t.__name__)
    if failed:
        sys.exit(1)
    print(f"\nAll {len(tests)}/{len(tests)} green")