#!/usr/bin/env python3
"""
PilotSuite Agent — Health Check + Reporter
Läuft auf HA, checked alle Systeme, posted zu GitHub.

Usage:
    python3 health_check.py [--fix] [--report]
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

GITHUB_REPO = "GreenhillEfka/pilotsuite-styx-ha"
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "")

HA_URL = os.environ.get("HA_URL", "http://supervisor/core/api")
HA_TOKEN = os.environ.get("HA_TOKEN", "")
CORE_URL = os.environ.get("CORE_URL", "http://localhost:8909")

@dataclass
class HealthResult:
    system: str
    status: str  # ok | warn | fail
    details: dict
    timestamp: str

def gh_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def http_get(url: str, headers: dict = None) -> Optional[dict]:
    import urllib.request
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return None


def extract_zone_ids(raw) -> list[str]:
    """Normalize HA/Core zone payloads into plain zone_id strings."""
    if isinstance(raw, dict):
        return [str(k) for k in raw.keys() if k]
    if not isinstance(raw, list):
        return []

    result: list[str] = []
    for item in raw:
        if isinstance(item, str) and item:
            result.append(item)
            continue
        if isinstance(item, dict):
            zone_id = item.get("zone_id") or item.get("id")
            if zone_id:
                result.append(str(zone_id))
    return result


def check_core_health() -> HealthResult:
    """Check Core addon health."""
    data = http_get(f"{CORE_URL}/health")
    if not data:
        return HealthResult("core", "fail", {"error": "unreachable"}, timestamp())
    
    version = data.get("version", "?")
    return HealthResult(
        "core", "ok" if version.startswith("15.") else "warn",
        {"version": version, "services": data.get("services", {})},
        timestamp()
    )

def check_ha_integration() -> HealthResult:
    """Check HA addon integration state."""
    headers = {"Authorization": f"Bearer {HA_TOKEN}"}
    data = http_get(f"{HA_URL}/states/sensor.copilot_ha_habitus_zones", headers)
    if not data:
        return HealthResult("ha_integration", "fail", {"error": "sensor not reachable"}, timestamp())
    
    state = data.get("state", "unknown")
    attrs = data.get("attributes", {})
    zones = attrs.get("zones", [])
    return HealthResult(
        "ha_integration", "ok",
        {"state": state, "zones_count": len(zones), "entities": list(attrs.keys())},
        timestamp()
    )

def check_zone_sync() -> HealthResult:
    """Check if zones are synced between HA and Core."""
    headers = {"Authorization": f"Bearer {HA_TOKEN}"}

    # HA zones
    ha_data = http_get(f"{HA_URL}/states/sensor.copilot_ha_habitus_zones", headers)
    ha_zones = extract_zone_ids(ha_data.get("attributes", {}).get("zones", [])) if ha_data else []

    # Core zones
    core_data = http_get(f"{CORE_URL}/api/v1/zone-automation/dashboard")
    core_zones = extract_zone_ids(core_data.get("zones", [])) if core_data else []

    synced = sorted(set(ha_zones) & set(core_zones))
    missing = sorted(set(ha_zones) - set(core_zones))

    status = "ok" if not missing else "warn"
    return HealthResult(
        "zone_sync", status,
        {"ha_zones": ha_zones, "core_zones": core_zones,
         "synced": synced, "missing": missing},
        timestamp()
    )

def check_module_schemas() -> HealthResult:
    """Check if module schemas are loaded."""
    data = http_get(f"{CORE_URL}/api/v1/zone-automation/module-schemas")
    if not data:
        return HealthResult("module_schemas", "fail", {"error": "unreachable"}, timestamp())
    
    schemas = data.get("schemas", {})
    total_fields = sum(len(v.get("fields", [])) for v in schemas.values())
    return HealthResult(
        "module_schemas", "ok",
        {"modules": list(schemas.keys()), "total_fields": total_fields},
        timestamp()
    )

def timestamp():
    return datetime.now().isoformat()

def run_all_checks() -> list[HealthResult]:
    """Run all health checks."""
    results = []
    for check_fn in [check_core_health, check_ha_integration, check_zone_sync, check_module_schemas]:
        try:
            results.append(check_fn())
        except Exception as e:
            results.append(HealthResult(check_fn.__name__, "fail", {"error": str(e)}, timestamp()))
    return results

def format_markdown(results: list[HealthResult]) -> str:
    """Format results as GitHub-compatible markdown."""
    md = f"## PilotSuite Health Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    for r in results:
        icon = {"ok": "✅", "warn": "⚠️", "fail": "❌"}.get(r.status, "?")
        md += f"### {icon} {r.system.upper()}\n"
        md += f"- Status: `{r.status}`\n"
        md += f"- Timestamp: `{r.timestamp}`\n"
        for k, v in r.details.items():
            md += f"- {k}: `{v}`\n"
        md += "\n"
    
    failed = [r for r in results if r.status == "fail"]
    warn = [r for r in results if r.status == "warn"]
    
    md += f"**Summary:** {len(results) - len(failed) - len(warn)} OK, {len(warn)} warn, {len(failed)} fail\n"
    
    if failed:
        md += "\n## Action Required\n"
        for r in failed:
            md += f"- **{r.system}** is failing: {r.details.get('error', 'unknown error')}\n"
    
    return md

def create_github_issue(title: str, body: str, labels: list = None) -> Optional[int]:
    """Create GitHub issue and return issue number."""
    if not GITHUB_TOKEN:
        print("GH_TOKEN not set, skipping GitHub issue")
        return None
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    data = json.dumps({"title": title, "body": body, "labels": labels or []}).encode()
    req = urllib.request.Request(url, data=data, headers=gh_headers())
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()).get("number")
    except Exception as e:
        print(f"Failed to create issue: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="PilotSuite Health Check")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix detected issues")
    parser.add_argument("--report", action="store_true", help="Post report as GitHub issue")
    parser.add_argument("--dry-run", action="store_true", help="Don't post to GitHub")
    args = parser.parse_args()
    
    print("Running PilotSuite health checks...")
    results = run_all_checks()
    
    md = format_markdown(results)
    print(md)
    
    if args.report and not args.dry_run:
        failed = [r for r in results if r.status in ("fail", "warn")]
        if failed:
            title = f"⚠️ Health Alert: {len(failed)} issue(s) — {datetime.now().strftime('%Y-%m-%d')}"
            issue_no = create_github_issue(title, md, labels=["health", "auto-reported"])
            if issue_no:
                print(f"Created GitHub issue #{issue_no}")
    
    # Exit code
    failed = [r for r in results if r.status == "fail"]
    sys.exit(0 if not failed else 1)

if __name__ == "__main__":
    main()
