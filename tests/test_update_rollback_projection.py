"""Contract test: update_rollback notification_id parity."""
import ast, sys

SOURCE = "custom_components/pilotsuite/update_rollback.py"
CUTOFF_LINE = 195  # line where the notification_id is written

def get_notification_id_line(source: str) -> str | None:
    """Find line with notification_id=... in update_rollback."""
    for line in source.splitlines():
        if "notification_id" in line and "=" in line:
            return line.strip()
    return None

def test_pilotsuite_notification_id():
    src = open(SOURCE).read()
    line = get_notification_id_line(src)
    assert line is not None, f"No notification_id found in {SOURCE}"
    assert "pilotsuite" in line, f"Expected pilotsuite notification_id, got: {line}"
    assert "copilot_ha" not in line, f"Stale copilot_ha still present: {line}"
    print(f"[UR1] PASS — notification_id = {line}")

def test_ast_no_unexplained_copilot_ha():
    src = open(SOURCE).read()
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "copilot_ha" in node.value and "pilotsuite" not in node.value:
                hits.append(node.value)
    assert not hits, f"Unexplained copilot_ha literals: {hits}"
    print(f"[UR2] PASS — AST scan clean, no unexplained copilot_ha literals")

def test_notification_id_line_is_canonical():
    src = open(SOURCE).read()
    line = get_notification_id_line(src)
    assert 'notification_id="pilotsuite_update_rollback_report"' in line, \
        f"Expected canonical notification_id, got: {line}"
    print(f"[UR3] PASS — canonical pilotsuite_update_rollback_report confirmed")

if __name__ == "__main__":
    test_pilotsuite_notification_id()
    test_ast_no_unexplained_copilot_ha()
    test_notification_id_line_is_canonical()
    print("All tests passed.")
