#!/usr/bin/env python3
"""
v15.0.0 Smoke Test — PilotSuite HA Add-on
Run on Home Assistant host or with HA API access.

Usage:
    python3 smoke_test_v15.py [--host http://192.168.30.18:8123] [--token <longlived>]
"""

import argparse
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


def run_smoke(host: str, token: str) -> bool:
    print(f"Connecting to {host} ...")
    try:
        states = get_states(host, token)
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"❌ Connection failed: {e.reason}")
        return False

    ps_sensors = filter_pilot_sensors(states)
    print(f"Found {len(ps_sensors)} PilotSuite sensors\n")

    all_ok = True

    for entity_id in EXPECTED_SENSORS:
        if entity_id in ps_sensors:
            state = ps_sensors[entity_id]
            val = state.get("state", "N/A")
            print(f"  ✅ {entity_id}: {val}")
        else:
            print(f"  ❌ {entity_id}: NOT FOUND")
            all_ok = False

    # Check connection state specifically
    conn = ps_sensors.get("sensor.copilot_ha_core_connection", {})
    conn_state = conn.get("state", "N/A")
    if conn_state in EXPECTED_CONNECTION_STATES:
        print(f"\n  ✅ Core Connection: {conn_state}")
    else:
        print(f"\n  ❌ Core Connection: unexpected state '{conn_state}'")
        all_ok = False

    # Check API failures is 0 or low
    failures = ps_sensors.get("sensor.copilot_ha_api_failures", {})
    try:
        fval = int(failures.get("state", -1))
        if fval >= 0:
            print(f"  ✅ API Failures: {fval}")
        else:
            print(f"  ❌ API Failures: unexpected '{failures.get('state')}'")
            all_ok = False
    except ValueError:
        print(f"  ❌ API Failures: non-integer state '{failures.get('state')}'")
        all_ok = False

    # Check poll interval > 0
    poll = ps_sensors.get("sensor.copilot_ha_poll_interval", {})
    try:
        pval = int(poll.get("state", 0))
        if pval > 0:
            print(f"  ✅ Poll Interval: {pval}s")
        else:
            print(f"  ⚠️  Poll Interval: {pval}s (may be 0 on first poll)")
    except ValueError:
        print(f"  ⚠️  Poll Interval: non-numeric '{poll.get('state')}'")

    print()
    return all_ok


def main():
    parser = argparse.ArgumentParser(description="v15.0.0 Smoke Test")
    parser.add_argument("--host", default="http://192.168.30.18:8123")
    parser.add_argument("--token", default="")
    args = parser.parse_args()

    if not args.token:
        print("❌ --token required")
        print("   Generate at: Profile → Long-Lived Access Tokens")
        sys.exit(1)

    ok = run_smoke(args.host, args.token)
    if ok:
        print("SMOKE TEST ✅ — ALL CHECKS PASSED")
        sys.exit(0)
    else:
        print("SMOKE TEST ❌ — SOME CHECKS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
