#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FILES=(
  "docs/HA_NEXT_VERSION_DEV_BOUNDARY_2026-03-27.md"
  "docs/HA_NEXT_VERSION_SLICE_2026-03-27.md"
  "docs/HA_NEXT_VERSION_BACKLOG_2026-03-27.md"
  "docs/HA_NEXT_VERSION_INDEX_2026-03-27.md"
  "docs/HA_NEXT_VERSION_BOUNDARY_CROSSING_TEMPLATE_2026-03-27.md"
  "scripts/prepare_next_version_dev_boundary.sh"
  "scripts/prepare_next_version_slice.sh"
  "scripts/prepare_next_version_boundary_crossing.sh"
)

printf 'HA/HACS next-version boundary-crossing prep\n'
printf 'Repo: %s\n\n' "$REPO_ROOT"

printf '== protected line boundary guard ==\n'
./scripts/prepare_next_version_dev_boundary.sh >/dev/null
printf 'PASS protected 15.2.0 line remains intact before any boundary-crossing proposal\n\n'

printf '== next-version slice guard ==\n'
./scripts/prepare_next_version_slice.sh >/dev/null
printf 'PASS current next-version planning slice is intact\n\n'

printf '== boundary-crossing proposal artifacts ==\n'
for f in "${FILES[@]}"; do
  if [[ -e "$f" ]]; then
    printf 'PASS %s\n' "$f"
  else
    printf 'FAIL missing %s\n' "$f"
    exit 1
  fi
done

printf '\nBoundary-crossing rule: do not touch protected 15.2.0 files until a reviewed proposal based on the template exists.\n'
