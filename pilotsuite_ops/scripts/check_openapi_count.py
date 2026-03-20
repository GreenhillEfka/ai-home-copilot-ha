#!/usr/bin/env python3
"""
check_openapi_count.py — Release-Gate: OpenAPI Path-Count Verifier

Compares path counts between HA OpenAPI and Core OpenAPI specs.
Fails the gate if counts differ or if paths are not 100% in sync.

Usage:
    python3 check_openapi_count.py [--ha <path>] [--core <path>] [--verbose]

Exit codes:
    0  = all good (counts match, paths in sync)
    1  = count mismatch
    2  = path drift detected
    3  = file not found
"""

import argparse
import os
import re
import sys

HA_DEFAULT = "docs/openapi.yaml"
CORE_DEFAULT = "copilot_core/docs/openapi.yaml"


def extract_unique_paths(filepath: str) -> set[str]:
    """Extract top-level path keys from an OpenAPI YAML file."""
    paths = set()
    with open(filepath, "r", encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^  (/[^:]+):", line)
            if m:
                paths.add(m.group(1))
    return paths


def load_paths(ha_path: str, core_path: str) -> tuple[set[str], set[str]]:
    """Load paths from both OpenAPI files. Errors on missing files."""
    if not os.path.exists(ha_path):
        print(f"ERROR: HA OpenAPI not found: {ha_path}", file=sys.stderr)
        sys.exit(3)
    if not os.path.exists(core_path):
        print(f"ERROR: Core OpenAPI not found: {core_path}", file=sys.stderr)
        sys.exit(3)

    ha_paths = extract_unique_paths(ha_path)
    core_paths = extract_unique_paths(core_path)
    return ha_paths, core_paths


def build_report(ha_path: str, core_path: str, ha_paths: set, core_paths: set, verbose: bool) -> str:
    ha_count = len(ha_paths)
    core_count = len(core_paths)
    synced = ha_count == core_count and ha_paths == core_paths

    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"  OpenAPI Path-Count Gate")
    lines.append(f"{'='*60}")
    lines.append(f"  HA version file : {get_version(ha_path)}")
    lines.append(f"  Core version file: {get_version(core_path)}")
    lines.append(f"")
    lines.append(f"  HA OpenAPI   : {ha_path}")
    lines.append(f"  Core OpenAPI : {core_path}")
    lines.append(f"")
    lines.append(f"  HA unique paths  : {ha_count}")
    lines.append(f"  Core unique paths: {core_count}")
    lines.append(f"")

    status = "✅ PASS — 100% synced" if synced else "❌ FAIL — drift detected"
    lines.append(f"  Result: {status}")
    lines.append(f"{'='*60}")

    if verbose or not synced:
        only_ha = sorted(ha_paths - core_paths)
        only_core = sorted(core_paths - ha_paths)
        if only_ha:
            lines.append(f"\n  Paths only in HA ({len(only_ha)}):")
            for p in only_ha[:20]:
                lines.append(f"    + {p}")
            if len(only_ha) > 20:
                lines.append(f"    ... and {len(only_ha)-20} more")
        if only_core:
            lines.append(f"\n  Paths only in Core ({len(only_core)}):")
            for p in only_core[:20]:
                lines.append(f"    - {p}")
            if len(only_core) > 20:
                lines.append(f"    ... and {len(only_core)-20} more")

    return "\n".join(lines)


def get_version(openapi_path: str) -> str:
    """Try to read a sibling VERSION file adjacent to the OpenAPI spec."""
    dirpath = os.path.dirname(openapi_path)
    for name in ("VERSION", "version.txt", ".version"):
        vpath = os.path.join(dirpath, name)
        if os.path.exists(vpath):
            with open(vpath, "r") as f:
                return f.read().strip()
    # Walk up to find VERSION
    for parent in (dirpath, os.path.dirname(dirpath), os.path.dirname(os.path.dirname(dirpath))):
        vpath = os.path.join(parent, "VERSION")
        if os.path.exists(vpath):
            with open(vpath, "r") as f:
                return f.read().strip()
    return "unknown"


def main():
    parser = argparse.ArgumentParser(description="Check OpenAPI path-count sync between HA and Core")
    parser.add_argument("--ha", default=HA_DEFAULT, help=f"Path to HA openapi.yaml (default: {HA_DEFAULT})")
    parser.add_argument("--core", default=CORE_DEFAULT, help=f"Path to Core openapi.yaml (default: {CORE_DEFAULT})")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show diff details even when passing")
    parser.add_argument("--cwd", default=os.getcwd(), help="Working directory for relative paths")
    args = parser.parse_args()

    # Resolve relative paths against cwd
    ha_abs = os.path.abspath(os.path.join(args.cwd, args.ha))
    core_abs = os.path.abspath(os.path.join(args.cwd, args.core))

    ha_paths, core_paths = load_paths(ha_abs, core_abs)

    ha_count = len(ha_paths)
    core_count = len(core_paths)
    synced = ha_count == core_count and ha_paths == core_paths

    report = build_report(ha_abs, core_abs, ha_paths, core_paths, args.verbose)
    print(report)

    if ha_count != core_count:
        print(f"\nGATE FAILED: count mismatch ({ha_count} vs {core_count})", file=sys.stderr)
        sys.exit(1)
    if not synced:
        print(f"\nGATE FAILED: path drift detected", file=sys.stderr)
        sys.exit(2)

    print(f"\nGate PASSED — {ha_count}/{core_count} paths, 100% synced")
    sys.exit(0)


if __name__ == "__main__":
    main()
