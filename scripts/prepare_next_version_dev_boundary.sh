#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$REPO_ROOT/docs/HA_15_2_0_RELEASE_ARTIFACT_FINGERPRINTS_2026-03-27.json"

cd "$REPO_ROOT"

printf 'HA/HACS next-version dev boundary prep\n'
printf 'Repo: %s\n\n' "$REPO_ROOT"

printf '== stable release-ready line fingerprint check ==\n'
./scripts/check_15_2_0_release_artifact_fingerprints.sh
printf '\n'

printf '== stable release-ready line readiness chain ==\n'
./scripts/check_15_2_0_release_readiness_chain.sh
printf '\n'

printf '== protected stable artifacts ==\n'
python3 - "$MANIFEST" <<'PY'
import json, pathlib, sys
manifest = pathlib.Path(sys.argv[1])
data = json.loads(manifest.read_text(encoding='utf-8'))
for entry in data.get('artifacts', []):
    print(f" - {entry['path']}")
PY

printf '\nNext-version rule: do not modify the protected stable artifacts above unless provenance/core-ref/reviewer/freeze fields change or a sharp HA blocker requires it.\n'
