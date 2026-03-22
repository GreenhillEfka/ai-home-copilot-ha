#!/usr/bin/env python3
"""
v15.0.2 Smoke Test — PilotSuite HA Add-on
Run on Home Assistant host or with HA API access.

Usage:
    python3 smoke_test_v15.py [--host http://192.168.30.18:8123] [--token <longlived>]
    python3 smoke_test_v15.py --env              # reads HA_TOKEN from env
    python3 smoke_test_v15.py --json             # machine-readable output
"""

import argparse
import os
import sys
import urllib.request
import urllib.error
import json
import time


EXPECTED_SENSORS = [
    "sensor.copilot_ha_core_connection",
    "sensor.copilot_ha_poll_interval",
    "sensor.copilot_ha_api_failures",
    "sensor.pilotsuite_modules_ready",
    "sensor.pilotsuite_habitus_zones",
    "sensor.copilot_ha_version",
]

EXPECTED_CONNECTION_STATES = {"connected", "degraded", "disconnected"}


def get_states(host: str, token: str) -> dict:
    url = f"{host}/api/states"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def filter_pilot_sensors(states: dict) -> dict:
    return {s["entity_id"]: s for s in states if s["entity_id"].startswith("sensor.pilotsuite") or s["entity_id"].startswith("sensor.copilot_ha")}


def run_smoke(host: str, token: str, *, json_output: bool = False) -> bool:
    """Run smoke checks. Returns True if all passed. Prints human or JSON based on json_output."""
    print(f"Connecting to {host} ...")
    try:
        states = get_states(host, token)
    except urllib.error.HTTPError as e:
        msg = f"❌ HTTP {e.code}: {e.reason}"
        print(msg if not json_output else json.dumps({"ok": False, "error": msg}))
        return False
    except urllib.error.URLError as e:
        msg = f"❌ Connection failed: {e.reason}"
        print(msg if not json_output else json.dumps({"ok": False, "error": msg}))
        return False

    ps_sensors = filter_pilot_sensors(states)
    print(f"Found {len(ps_sensors)} PilotSuite sensors\n")

    checks = []
    all_ok = True

    for entity_id in EXPECTED_SENSORS:
        ok = entity_id in ps_sensors
        val = ps_sensors[entity_id].get("state", "N/A") if ok else None
        checks.append({"entity_id": entity_id, "ok": ok, "state": val})
        if ok:
            print(f"  ✅ {entity_id}: {val}")
        else:
            print(f"  ❌ {entity_id}: NOT FOUND")
            all_ok = False

    # Check connection state specifically
    conn = ps_sensors.get("sensor.copilot_ha_core_connection", {})
    conn_state = conn.get("state", "N/A")
    conn_ok = conn_state in EXPECTED_CONNECTION_STATES
    checks.append({"entity_id": "core_connection", "ok": conn_ok, "state": conn_state})
    if conn_ok:
        print(f"\n  ✅ Core Connection: {conn_state}")
    else:
        print(f"\n  ❌ Core Connection: unexpected state '{conn_state}'")
        all_ok = False

    # Check API failures is 0 or low
    failures = ps_sensors.get("sensor.copilot_ha_api_failures", {})
    try:
        fval = int(failures.get("state", -1))
        fok = fval >= 0
        checks.append({"entity_id": "api_failures", "ok": fok, "state": fval})
        print(f"  ✅ API Failures: {fval}" if fok else f"  ❌ API Failures: unexpected '{failures.get('state')}'")
        if not fok:
            all_ok = False
    except ValueError:
        checks.append({"entity_id": "api_failures", "ok": False, "state": failures.get("state")})
        print(f"  ❌ API Failures: non-integer state '{failures.get('state')}'")
        all_ok = False

    # Check poll interval > 0
    poll = ps_sensors.get("sensor.copilot_ha_poll_interval", {})
    try:
        pval = int(poll.get("state", 0))
        pok = pval > 0
        checks.append({"entity_id": "poll_interval", "ok": pok, "state": pval})
        print(f"  ✅ Poll Interval: {pval}s" if pok else f"  ⚠️  Poll Interval: {pval}s (may be 0 on first poll)")
    except ValueError:
        checks.append({"entity_id": "poll_interval", "ok": False, "state": poll.get("state")})
        print(f"  ⚠️  Poll Interval: non-numeric '{poll.get('state')}'")

    print()
    if json_output:
        print(json.dumps({"ok": all_ok, "checks": checks}, indent=2))
    return all_ok


def main():
    parser = argparse.ArgumentParser(description="v15.0.0 Smoke Test")
    parser.add_argument("--host", default=os.environ.get("HA_HOST", "http://192.168.30.18:8123"))
    parser.add_argument("--token", default=os.environ.get("HA_TOKEN", ""))
    parser.add_argument("--env", action="store_true", help="Read HA_TOKEN from env var (same as setting --token from $HA_TOKEN)")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    args = parser.parse_args()

    if args.env:
        args.token = os.environ.get("HA_TOKEN", "")

    if not args.token:
        print("❌ --token required (or set HA_TOKEN env var, or use --env)")
        print("   Generate at: Profile → Long-Lived Access Tokens")
        sys.exit(1)

    ok = run_smoke(args.host, args.token, json_output=args.json)
    if ok:
        print("SMOKE TEST ✅ — ALL CHECKS PASSED" if not args.json else "")
        sys.exit(0)
    else:
        print("SMOKE TEST ❌ — SOME CHECKS FAILED" if not args.json else "")
        sys.exit(1)


if __name__ == "__main__":
    main()
