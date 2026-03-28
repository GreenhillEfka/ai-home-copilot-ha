#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

EXPECTED_HA_SOURCE="/config/clawd/team/repos/pilotsuite-styx-ha"
EXPECTED_CORE_REF="8b017a74"
EXPECTED_VERSION="15.2.0"

DOCS=(
  "docs/HA_15_2_0_BUILDER_HANDOFF_2026-03-27.md"
  "docs/HA_15_2_0_REVIEW_SLICE_2026-03-27.md"
  "docs/HA_15_2_0_REVIEW_SLICE_MANIFEST_2026-03-27.md"
  "docs/HA_15_2_0_RELEASER_PREP_POINTER_2026-03-27.md"
  "docs/HA_15_2_0_SYNC_ANCHOR_2026-03-27.md"
  "docs/HA_15_2_0_BLOCKER_REGISTER_2026-03-27.md"
  "docs/HA_15_2_0_RUNTIME_BOUNDARY_2026-03-27.md"
)

failures=0

printf 'HA/HACS 15.2.0 sync-anchor consistency check\n'
printf 'Repo: %s\n' "$REPO_ROOT"

actual_version="$(tr -d '[:space:]' < VERSION)"
if [[ "$actual_version" == "$EXPECTED_VERSION" ]]; then
  printf 'PASS version=%s\n' "$actual_version"
else
  printf 'FAIL expected version %s, got %s\n' "$EXPECTED_VERSION" "$actual_version"
  failures=$((failures + 1))
fi

for doc in "${DOCS[@]}"; do
  if [[ ! -f "$doc" ]]; then
    printf 'FAIL missing %s\n' "$doc"
    failures=$((failures + 1))
    continue
  fi

  if grep -Fq "$EXPECTED_HA_SOURCE" "$doc"; then
    printf 'PASS %s authoritative source\n' "$doc"
  else
    printf 'FAIL %s missing authoritative source\n' "$doc"
    failures=$((failures + 1))
  fi

done

CORE_REF_DOCS=(
  "docs/HA_15_2_0_BUILDER_HANDOFF_2026-03-27.md"
  "docs/HA_15_2_0_REVIEW_SLICE_2026-03-27.md"
  "docs/HA_15_2_0_REVIEW_SLICE_MANIFEST_2026-03-27.md"
  "docs/HA_15_2_0_RELEASER_PREP_POINTER_2026-03-27.md"
  "docs/HA_15_2_0_SYNC_ANCHOR_2026-03-27.md"
  "docs/HA_15_2_0_BLOCKER_REGISTER_2026-03-27.md"
  "docs/HA_15_2_0_RUNTIME_BOUNDARY_2026-03-27.md"
)

for doc in "${CORE_REF_DOCS[@]}"; do
  if grep -Fq "$EXPECTED_CORE_REF" "$doc"; then
    printf 'PASS %s core-ref=%s\n' "$doc" "$EXPECTED_CORE_REF"
  else
    printf 'FAIL %s missing core-ref %s\n' "$doc" "$EXPECTED_CORE_REF"
    failures=$((failures + 1))
  fi
done

if [[ "$failures" -ne 0 ]]; then
  exit 1
fi
