#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FILES=(
  "docs/HA_NEXT_VERSION_DEV_BOUNDARY_2026-03-27.md"
  "docs/HA_NEXT_VERSION_SLICE_2026-03-27.md"
  "docs/HA_NEXT_VERSION_BACKLOG_2026-03-27.md"
  "docs/HA_NEXT_VERSION_INDEX_2026-03-27.md"
  "scripts/prepare_next_version_dev_boundary.sh"
  "scripts/prepare_next_version_slice.sh"
)

printf 'HA/HACS next-version slice prep\n'
printf 'Repo: %s\n' "$REPO_ROOT"

printf '\nChecking boundary guard first...\n'
./scripts/prepare_next_version_dev_boundary.sh >/dev/null
printf 'PASS protected 15.2.0 line remains intact before next-version slice work\n'

printf '\nNext-version slice files:\n'
for f in "${FILES[@]}"; do
  if [[ -e "$f" ]]; then
    printf 'PASS %s\n' "$f"
  else
    printf 'FAIL missing %s\n' "$f"
    exit 1
  fi
done

printf '\nCurrent git status for next-version slice files:\n'
git status --short -- "${FILES[@]}" || true
