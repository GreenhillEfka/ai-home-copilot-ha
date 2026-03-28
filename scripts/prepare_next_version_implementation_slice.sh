#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DECISION_FILE="docs/HA_NEXT_VERSION_REVIEW_DECISION_NV_HA_001_2026-03-27.md"
SLICE_FILE="docs/HA_NEXT_VERSION_IMPLEMENTATION_SLICE_NV_HA_001_2026-03-27.md"

printf 'HA/HACS next-version implementation slice prep\n'
printf 'Repo: %s\n\n' "$REPO_ROOT"

printf '== boundary and review guards ==\n'
./scripts/prepare_next_version_dev_boundary.sh >/dev/null
./scripts/prepare_next_version_boundary_crossing.sh >/dev/null
./scripts/prepare_next_version_review_packet.sh >/dev/null
./scripts/prepare_next_version_review_decision_capture.sh >/dev/null
printf 'PASS pre-implementation guards are intact\n\n'

printf '== implementation slice scaffold ==\n'
if [[ -f "$SLICE_FILE" ]]; then
  printf 'PASS %s\n' "$SLICE_FILE"
else
  printf 'FAIL missing %s\n' "$SLICE_FILE"
  exit 1
fi

printf '\n== decision gate state ==\n'
if [[ ! -f "$DECISION_FILE" ]]; then
  printf 'FAIL missing approved decision artifact %s\n' "$DECISION_FILE"
  exit 1
fi

if grep -Fq 'accept boundary as proposed' "$DECISION_FILE" || grep -Fq 'accept with narrowed boundary' "$DECISION_FILE" || grep -Fq 'accept with widened boundary' "$DECISION_FILE"; then
  printf 'OPEN reviewer/design decision captured in %s\n' "$DECISION_FILE"
  printf 'Implementation slice may proceed within the approved boundary.\n'
  exit 0
fi

printf 'LOCKED reviewer/design decision does not authorize implementation yet in %s\n' "$DECISION_FILE"
exit 1
