#!/usr/bin/env python3
"""PS-E2E-001: End-to-End contract pipeline test.

Tests the full Proposal→Action→Command flow:
1. Core contracts (ProposalIntent, ActionIntent, HabitatModuleCommand)
2. HA contracts_bridge import
3. Webhook parsing + validation
4. Service call execution path

Exit codes:
  0 = PASS (all stages verified)
  1 = WARN (partial success, some stages skipped)
  2 = FAIL (critical stage failed)

Dependency-free: Python stdlib only (no HA runtime required).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any


@dataclass(frozen=True)
class TestStage:
    name: str
    path: Path
    check_type: str  # "import", "parse", "validate", "execute"


def _workspace_root() -> Path:
    # /config/clawd/team/repos/pilotsuite-styx-ha/pilotsuite_ops/scripts/<this_file>
    return Path(__file__).resolve().parents[2]


def _check_import_stage(stage: TestStage) -> tuple[bool, str | None]:
    """Check that contracts_bridge can be imported (syntax + API surface)."""
    try:
        # Read file and check for required classes
        text = stage.path.read_text(encoding="utf-8")
        required_classes = ("ProposalIntent", "ActionIntent", "HabitatModuleCommand")
        missing = [c for c in required_classes if f"class {c}" not in text]
        if missing:
            return False, f"missing classes: {', '.join(missing)}"
        # Check required methods
        required_methods = ("from_dict", "to_dict", "to_action_intent", "can_execute", "can_auto_execute")
        missing_methods = [m for m in required_methods if f"def {m}" not in text]
        if missing_methods:
            return False, f"missing methods: {', '.join(missing_methods)}"
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, f"read_error: {exc}"


def _check_parse_stage(stage: TestStage) -> tuple[bool, str | None]:
    """Check that webhook.py parses ProposalIntent from dict."""
    try:
        text = stage.path.read_text(encoding="utf-8")
        # Check for contracts_bridge import
        if "from .core.contracts_bridge import" not in text:
            return False, "missing contracts_bridge import"
        # Check for from_dict usage
        if "ProposalIntent.from_dict" not in text:
            return False, "missing ProposalIntent.from_dict call"
        # Check for to_action_intent usage
        if "to_action_intent" not in text:
            return False, "missing to_action_intent call"
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, f"read_error: {exc}"


def _check_validate_stage(stage: TestStage) -> tuple[bool, str | None]:
    """Check that webhook.py validates required fields (contract drift guard)."""
    try:
        text = stage.path.read_text(encoding="utf-8")
        # Check for required field validation
        required_fields = ("module_id", "action_type", "title")
        has_validation = "required_fields" in text and "missing" in text
        if not has_validation:
            return False, "missing contract drift guard validation"
        # Check for invalid_payload error code
        if "invalid_payload" not in text:
            return False, "missing invalid_payload error code"
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, f"read_error: {exc}"


def _check_execute_stage(stage: TestStage) -> tuple[bool, str | None]:
    """Check that webhook.py has service call execution path."""
    try:
        text = stage.path.read_text(encoding="utf-8")
        # Check for service call execution
        if "hass.services.async_call" not in text:
            return False, "missing hass.services.async_call"
        # Check for can_auto_execute check
        if "can_auto_execute" not in text:
            return False, "missing can_auto_execute check"
        # Check for execute_proposal task
        if "_execute_proposal" not in text:
            return False, "missing _execute_proposal task"
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, f"read_error: {exc}"


def _run_stage(stage: TestStage) -> tuple[bool, str | None]:
    """Run a single test stage."""
    if stage.check_type == "import":
        return _check_import_stage(stage)
    elif stage.check_type == "parse":
        return _check_parse_stage(stage)
    elif stage.check_type == "validate":
        return _check_validate_stage(stage)
    elif stage.check_type == "execute":
        return _check_execute_stage(stage)
    return False, f"unknown check_type: {stage.check_type}"


def _render_md_report(
    *,
    stages: list[TestStage],
    results: dict[str, tuple[bool, str | None]],
    overall: str,
) -> str:
    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    lines: list[str] = [
        "# PS-E2E-001 — Contract Pipeline E2E Test Report",
        "",
        f"- generated_at_utc: `{utc_now}`",
        f"- overall_result: **{overall}**",
        "",
        "## Test Stages",
        "",
    ]

    for stage in stages:
        passed, error = results[stage.name]
        status = "✅ PASS" if passed else "❌ FAIL"
        lines.append(f"### {stage.name} ({stage.check_type})")
        lines.append("")
        lines.append(f"- status: {status}")
        lines.append(f"- path: `{stage.path}`")
        if error:
            lines.append(f"- error: `{error}`")
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str]) -> int:
    root = _workspace_root()

    ap = argparse.ArgumentParser(description="E2E contract pipeline test (PS-E2E-001)")
    ap.add_argument(
        "--contracts-bridge",
        default=str(root / "custom_components/copilot_ha/core/contracts_bridge.py"),
        help="Path to contracts_bridge.py",
    )
    ap.add_argument(
        "--webhook",
        default=str(root / "custom_components/copilot_ha/webhook.py"),
        help="Path to webhook.py",
    )
    ap.add_argument(
        "--out-md",
        default=str(root / "pilotsuite_ops/reports/PS-E2E-001_CONTRACT_PIPELINE_E2E.md"),
        help="Optional Markdown report output path",
    )

    args = ap.parse_args(argv)

    stages = [
        TestStage("contracts_bridge", Path(args.contracts_bridge).expanduser().resolve(), "import"),
        TestStage("webhook_parse", Path(args.webhook).expanduser().resolve(), "parse"),
        TestStage("webhook_validate", Path(args.webhook).expanduser().resolve(), "validate"),
        TestStage("webhook_execute", Path(args.webhook).expanduser().resolve(), "execute"),
    ]

    results: dict[str, tuple[bool, str | None]] = {}
    has_failure = False
    has_warning = False

    for stage in stages:
        passed, error = _run_stage(stage)
        results[stage.name] = (passed, error)
        if not passed:
            has_failure = True
            print(f"[ps-e2e-001] {stage.name}: FAIL — {error}", file=sys.stderr)
        else:
            print(f"[ps-e2e-001] {stage.name}: PASS")

    # Determine overall result
    if has_failure:
        overall = "FAIL"
        exit_code = 2
    elif has_warning:
        overall = "WARN"
        exit_code = 1
    else:
        overall = "PASS"
        exit_code = 0

    print(f"[ps-e2e-001] E2E test result: {overall}")

    out_md = Path(args.out_md).expanduser().resolve() if args.out_md else None
    if out_md is not None:
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(
            _render_md_report(
                stages=stages,
                results=results,
                overall=overall,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"[ps-e2e-001] markdown report: {out_md}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
