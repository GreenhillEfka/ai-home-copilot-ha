#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$REPO_ROOT/docs/HA_15_2_0_RELEASE_ARTIFACT_FINGERPRINTS_2026-03-27.json"

if [[ ! -f "$MANIFEST" ]]; then
  echo "FAIL missing manifest: $MANIFEST" >&2
  exit 1
fi

python3 - "$MANIFEST" <<'PY'
import hashlib
import json
import pathlib
import sys

manifest_path = pathlib.Path(sys.argv[1])
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
failures = 0

print('HA/HACS 15.2.0 release-artifact fingerprint check')
print(f"Manifest: {manifest_path}")

for entry in manifest.get('artifacts', []):
    path = pathlib.Path(entry['path'])
    expected = entry['sha256']
    if not path.exists():
        print(f"FAIL missing {path}")
        failures += 1
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual == expected:
        print(f"PASS {path}")
    else:
        print(f"FAIL {path} sha256 {actual} != {expected}")
        failures += 1

if failures:
    sys.exit(1)
PY
