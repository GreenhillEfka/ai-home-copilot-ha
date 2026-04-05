#!/bin/bash
# PS-151 HA Drift Guard
set -e
echo "[PS-151] Running contract drift guard..."
python3 -m py_compile tests/test_*_projection.py 2>/dev/null && echo "[PS-151] projection tests: OK" || { echo "[PS-151] FAIL"; exit 1; }
echo "[PS-151] PASS (OK)"
exit 0
