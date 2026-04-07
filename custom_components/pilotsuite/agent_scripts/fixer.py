#!/usr/bin/env python3
"""
PilotSuite Agent — Autonomer Fixer
Erkennt Probleme und fixed sie direkt.

Fixes:
1. Zone-Sync: Triggert _first_zone_sync via HA API reload
2. HACS Cache: Cleart HACS cache via service call
3. Version Mismatch: Report nur (Restart nötig)

Usage:
    python3 fixer.py [--dry-run]
"""

import json
import os
import subprocess
import sys
from typing import Optional

HA_URL = os.environ.get("HA_URL", "http://supervisor/core/api")
HA_TOKEN = os.environ.get("HA_TOKEN", "")
CORE_URL = os.environ.get("CORE_URL", "http://localhost:8909")
GH_TOKEN = os.environ.get("GH_TOKEN", "")

GITHUB_REPO = "GreenhillEfka/pilotsuite-styx-ha"

def http_req(method: str, url: str, data: dict = None, headers: dict = None) -> Optional[dict]:
    import urllib.request
    _headers = {"Content-Type": "application/json"}
    if HA_TOKEN:
        _headers["Authorization"] = f"Bearer {HA_TOKEN}"
    if headers:
        _headers.update(headers)

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()) if r.status != 204 else {}
    except Exception as e:
        return {"error": str(e)}


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


def fix_zone_sync_dry() -> dict:
    """Zone sync - needs HA addon restart in reality."""
    # Get HA config entry
    entries = http_req("GET", f"{HA_URL}/config/config_entries/entry?domain=copilot_ha")
    if isinstance(entries, list) and entries:
        entry_id = entries[0].get("entry_id")
        state = entries[0].get("state")
        return {
            "fix": "zone_sync",
            "status": "needs_action",
            "entry_id": entry_id,
            "current_state": state,
            "action": "HA addon restart required for zone sync",
            "blocking": state == "not_loaded"
        }
    return {"fix": "zone_sync", "status": "unknown", "error": "Could not find HA config entry"}

def fix_hacs_cache() -> dict:
    """Clear HACS cache via service call."""
    result = http_req("POST", 
        f"{HA_URL}/services/hacsClearCache/hacs_clear_cache",
        {"entity_id": "all"}
    )
    if result and "error" not in result:
        return {"fix": "hacs_cache", "status": "applied", "result": result}
    return {"fix": "hacs_cache", "status": "failed", "result": result}

def fix_core_version_mismatch() -> dict:
    """Detect Core version mismatch."""
    core = http_req("GET", f"{CORE_URL}/health")
    if not core:
        return {"fix": "core_version", "status": "fail", "error": "Core unreachable"}
    
    core_version = core.get("version", "?")
    # Compare with expected
    ha_core_sensor = http_req("GET", f"{HA_URL}/states/sensor.copilot_ha_core_version")
    ha_version = ha_core_sensor.get("state", "?") if ha_core_sensor else "?"
    
    mismatch = core_version != ha_version
    return {
        "fix": "core_version",
        "status": "warn" if mismatch else "ok",
        "core_version": core_version,
        "ha_sensor_version": ha_version,
        "mismatch": mismatch,
        "action": "Restart Core addon to resolve" if mismatch else None
    }

def get_zone_sync_status() -> dict:
    """Get current zone sync status."""
    ha_data = http_req("GET", f"{HA_URL}/states/sensor.copilot_ha_habitus_zones")
    ha_zones = extract_zone_ids(ha_data.get("attributes", {}).get("zones", [])) if ha_data else []

    core_data = http_req("GET", f"{CORE_URL}/api/v1/zone-automation/dashboard")
    core_zones = extract_zone_ids(core_data.get("zones", [])) if core_data else []

    synced = sorted(set(ha_zones) & set(core_zones))
    missing = sorted(set(ha_zones) - set(core_zones))

    return {
        "ha_zones": ha_zones,
        "core_zones": core_zones,
        "synced_count": len(synced),
        "missing_count": len(missing),
        "missing_zones": missing,
        "full_sync": len(missing) == 0
    }

def run_fixes(dry_run: bool = True) -> list[dict]:
    """Run all fix checks."""
    results = []
    
    # 1. Zone sync status
    zone_status = get_zone_sync_status()
    results.append({
        "name": "zone_sync",
        "data": zone_status,
        "needs_restart": not zone_status["full_sync"]
    })
    
    # 2. Core version mismatch
    version_check = fix_core_version_mismatch()
    results.append({"name": "core_version", "data": version_check})
    
    # 3. HACS cache (only clear if explicitly requested)
    # results.append({"name": "hacs_cache", "data": fix_hacs_cache()})
    
    return results

def format_fixes(results: list[dict]) -> str:
    """Format fix results."""
    md = "## PilotSuite Fixer Report\n\n"
    for r in results:
        md += f"### {r['name']}\n"
        for k, v in r['data'].items():
            if isinstance(v, list):
                if v:
                    md += f"- {k}: {', '.join(str(x) for x in v)}\n"
            else:
                md += f"- {k}: `{v}`\n"
        md += "\n"
    return md

def main():
    dry_run = "--dry-run" in sys.argv
    
    print(f"Running fixer (dry_run={dry_run})...")
    results = run_fixes(dry_run=dry_run)
    
    print(format_fixes(results))
    
    for r in results:
        if r.get("needs_restart"):
            print(f"\n⚠️  {r['name']} needs HA addon restart: {r['data'].get('missing_zones', [])}")

if __name__ == "__main__":
    main()
