#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

EXPECTED_CORE_REF="8b017a74"
DEPRECATED_CORE_REFS=("998f6beb" "a6eba8a2" "f1243375" "bcdef4a7" "a84742a5" "7728b93e" "ee91d09c" "88d3e8ce" "081ddb5d" "1d4fc18f")

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

printf 'HA/HACS 15.2.0 core-pairing anchor check\n'
printf 'Repo: %s\n' "$REPO_ROOT"

for doc in "${DOCS[@]}"; do
  if [[ ! -f "$doc" ]]; then
    printf 'FAIL missing %s\n' "$doc"
    failures=$((failures + 1))
    continue
  fi

  deprecated_hit=0
  for deprecated in "${DEPRECATED_CORE_REFS[@]}"; do
    if grep -Fq "$deprecated" "$doc"; then
      printf 'FAIL %s still references deprecated core ref %s\n' "$doc" "$deprecated"
      failures=$((failures + 1))
      deprecated_hit=1
    fi
  done
  if [[ "$deprecated_hit" -eq 0 ]]; then
    printf 'PASS %s has no deprecated core refs\n' "$doc"
  fi

  if grep -Fq "$EXPECTED_CORE_REF" "$doc"; then
    printf 'PASS %s uses expected core ref %s\n' "$doc" "$EXPECTED_CORE_REF"
  else
    printf 'FAIL %s missing expected core ref %s\n' "$doc" "$EXPECTED_CORE_REF"
    failures=$((failures + 1))
  fi

done

if [[ "$failures" -ne 0 ]]; then
  exit 1
fi
