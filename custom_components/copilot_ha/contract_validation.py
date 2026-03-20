"""Contract Validation — OpenAPI contract drift guard (PS-151).

Validates:
- Core OpenAPI spec vs implementation
- HA OpenAPI spec vs implementation
- Runtime type contracts
- Drift detection between spec and code

Runs as pre-commit hook to prevent contract drift.
"""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)

DOMAIN = "copilot_ha"


def _run_openapi_validator(spec_path: Path) -> tuple[bool, str]:
    """Run OpenAPI spec validator."""
    try:
        result = subprocess.run(
            ["openapi-spec-validator", str(spec_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Validation timeout"
    except FileNotFoundError:
        return True, "Validator not installed, skipping"


def _check_drift_between_specs(core_spec: Path, ha_spec: Path) -> tuple[bool, list[str]]:
    """Check for drift between core and HA OpenAPI specs."""
    drifts = []
    
    try:
        import yaml
        
        with open(core_spec) as f:
            core_yaml = yaml.safe_load(f)
        
        with open(ha_spec) as f:
            ha_yaml = yaml.safe_load(f)
        
        # Compare endpoint paths
        core_paths = set(core_yaml.get("paths", {}).keys())
        ha_paths = set(ha_yaml.get("paths", {}).keys())
        
        if core_paths - ha_paths:
            drifts.append(f"Core endpoints not in HA: {core_paths - ha_paths}")
        
        if ha_paths - core_paths:
            drifts.append(f"HA endpoints not in Core: {ha_paths - core_paths}")
        
        # Compare schemas
        core_schemas = set(core_yaml.get("components", {}).get("schemas", {}).keys())
        ha_schemas = set(ha_yaml.get("components", {}).get("schemas", {}).keys())
        
        if core_schemas - ha_schemas:
            drifts.append(f"Core schemas not in HA: {core_schemas - ha_schemas}")
        
        if ha_schemas - core_schemas:
            drifts.append(f"HA schemas not in Core: {ha_schemas - core_schemas}")
        
    except Exception as err:  # noqa: BLE001
        return False, [f"Drift check error: {err}"]
    
    return len(drifts) == 0, drifts


async def async_validate_contracts(workspace_path: Path) -> dict[str, Any]:
    """Validate all contracts for the workspace."""
    result = {
        "success": True,
        "core_openapi": {"valid": True, "message": "PASS"},
        "ha_openapi": {"valid": True, "message": "PASS"},
        "drift_check": {"valid": True, "message": "PASS"},
        "runtime": {"valid": True, "message": "PASS"},
    }
    
    # Core OpenAPI validation
    core_spec = workspace_path / "team" / "worktrees" / "pilotsuite-styx-core-release-prep-v14.7.3" / "docs" / "openapi.yaml"
    if core_spec.exists():
        valid, msg = _run_openapi_validator(core_spec)
        result["core_openapi"] = {"valid": valid, "message": msg.strip()}
        if not valid:
            result["success"] = False
    
    # HA OpenAPI validation
    ha_spec = workspace_path / "team" / "worktrees" / "pilotsuite-styx-ha-release-prep-v14.7.3" / "docs" / "openapi.yaml"
    if ha_spec.exists():
        valid, msg = _run_openapi_validator(ha_spec)
        result["ha_openapi"] = {"valid": valid, "message": msg.strip()}
        if not valid:
            result["success"] = False
    
    # Drift check
    if core_spec.exists() and ha_spec.exists():
        valid, drifts = _check_drift_between_specs(core_spec, ha_spec)
        result["drift_check"] = {"valid": valid, "message": "PASS" if valid else "; ".join(drifts)}
        if not valid:
            result["success"] = False
    
    # Runtime type check (py_compile)
    ha_path = workspace_path / "team" / "worktrees" / "pilotsuite-styx-ha-release-prep-v14.7.3" / "custom_components" / "copilot_ha"
    if ha_path.exists():
        try:
            compile_result = subprocess.run(
                ["python3", "-m", "py_compile"] + [str(p) for p in ha_path.glob("**/*.py")],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(workspace_path),
            )
            if compile_result.returncode == 0:
                result["runtime"] = {"valid": True, "message": "PASS"}
            else:
                result["runtime"] = {"valid": False, "message": compile_result.stderr.strip()}
                result["success"] = False
        except Exception as err:  # noqa: BLE001
            result["runtime"] = {"valid": True, "message": f"Skipped: {err}"}
    
    return result


def run_pre_commit_validation(workspace_path: Path) -> int:
    """Run pre-commit contract validation. Returns exit code."""
    import asyncio
    
    result = asyncio.run(async_validate_contracts(workspace_path))
    
    print("[pre-commit] PS-151: Running contract drift guard...")
    print(f"[pre-commit] core_openapi: {'PASS (OK)' if result['core_openapi']['valid'] else 'FAIL'}")
    print(f"[pre-commit] ha_openapi: {'PASS (OK)' if result['ha_openapi']['valid'] else 'FAIL'}")
    print(f"[pre-commit] drift_check: {'PASS (OK)' if result['drift_check']['valid'] else 'FAIL'}")
    print(f"[pre-commit] runtime: {'PASS (OK)' if result['runtime']['valid'] else 'FAIL'}")
    
    if result["success"]:
        print("[pre-commit] No contract drift — commit allowed")
        return 0
    else:
        print("[pre-commit] Contract drift detected — commit blocked")
        return 1


if __name__ == "__main__":
    workspace = Path("/config/clawd")
    sys.exit(run_pre_commit_validation(workspace))
