"""Contract tests: zone_automation_entities unique_id pilotsuite parity."""
import ast

SRC = "custom_components/pilotsuite/zone_automation_entities.py"


def _parse():
    with open(SRC) as f:
        return f.read(), ast.parse(f.read())


def _all_unique_id_lines(source: str):
    """Yield (lineno, rhs_string) for self._attr_unique_id = <expr> lines."""
    for lineno, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if not stripped.startswith("self._attr_unique_id"):
            continue
        if "=" not in line:
            continue
        rhs = line.split("=", 1)[1].strip()
        yield lineno, rhs


def test_zae1_automation_mode_unique_id():
    """ZA1: ZoneAutomationModeSelect unique_id uses pilotsuite_zone_..._automation_mode."""
    source, _ = _parse()
    for lineno, rhs in _all_unique_id_lines(source):
        if "automation_mode" in rhs:
            assert "pilotsuite_zone_" in rhs, f"L{lineno}: expected pilotsuite_zone_ in {rhs!r}"
            assert "copilot_ha_zone_" not in rhs, f"L{lineno}: stale copilot_ha_zone_ in {rhs!r}"
            return
    assert False, "automation_mode unique_id not found"


def test_zae2_target_unique_ids():
    """ZA2: _ZoneAutoSwitch base-class unique_ids use pilotsuite_zone_..._target_... pattern (via {target}_{key} in f-string)."""
    source, _ = _parse()
    # After replacement, target-based lines are the ones with pilotsuite_zone_..._{target}_{key}
    # These appear in _ZoneAutoSwitch (line ~145) and _ZoneConfigNumber (line ~249)
    # Both have pilotsuite_zone_ but NOT automation_mode and NOT module_id
    found = 0
    for lineno, rhs in _all_unique_id_lines(source):
        has_zone = "pilotsuite_zone_" in rhs
        has_automation = "automation_mode" in rhs
        has_module = "module_id" in rhs
        if has_zone and not has_automation and not has_module:
            assert "copilot_ha_zone_" not in rhs, f"L{lineno}: stale copilot_ha_zone_ in {rhs!r}"
            found += 1
    # 2 target-based: _ZoneAutoSwitch (L145) and _ZoneConfigNumber (L249)
    assert found >= 2, f"expected >=2 target-based unique_ids (zone+target+key, not automation_mode, not module_id), got {found}"


def test_zae3_module_unique_ids():
    """ZA3: _ZoneModuleSwitch/Number unique_ids use pilotsuite_zone_..._module_id_... ."""
    source, _ = _parse()
    found = 0
    for lineno, rhs in _all_unique_id_lines(source):
        if "module_id" in rhs:
            assert "pilotsuite_zone_" in rhs, f"L{lineno}: expected pilotsuite_zone_ in {rhs!r}"
            assert "copilot_ha_zone_" not in rhs, f"L{lineno}: stale copilot_ha_zone_ in {rhs!r}"
            found += 1
    assert found >= 2, f"expected >=2 module_id-based unique_ids, got {found}"


def test_zae4_ast_scan_no_stale_copilot_ha_zone():
    """ZA4: AST scan — no stale copilot_ha_zone_ string literals in the file."""
    source, tree = _parse()
    for lineno, line in enumerate(source.splitlines(), 1):
        if "copilot_ha_zone_" in line:
            stripped = line.strip()
            assert stripped.startswith("#"), f"L{lineno}: non-comment stale copilot_ha_zone_ found: {line!r}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "copilot_ha_zone_" in node.value:
                for lno, ln in enumerate(source.splitlines(), 1):
                    if node.value in ln and not ln.strip().startswith("#"):
                        assert False, f"L{lno}: stale copilot_ha_zone_ in string literal"
