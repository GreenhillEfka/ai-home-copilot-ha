#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FILES=(
  "docs/HA_NEXT_VERSION_REVIEW_DECISION_NV_HA_001_2026-03-27.md"
  "docs/HA_NEXT_VERSION_IMPLEMENTATION_SLICE_NV_HA_001_2026-03-27.md"
  "docs/HA_NEXT_VERSION_IMPLEMENTATION_MANIFEST_NV_HA_001_2026-03-27.md"
  "custom_components/copilot_ha/www/styx-card-base.js"
  "custom_components/copilot_ha/www/styx-zone-card.js"
  "scripts/prepare_next_version_implementation_slice.sh"
  "scripts/prepare_next_version_implementation_manifest.sh"
)

printf 'HA/HACS next-version implementation manifest prep\n'
printf 'Repo: %s\n\n' "$REPO_ROOT"

printf '== implementation slice gate ==\n'
./scripts/prepare_next_version_implementation_slice.sh >/dev/null
printf 'PASS implementation slice is open within approved boundary\n\n'

printf '== implementation manifest files ==\n'
for f in "${FILES[@]}"; do
  if [[ -e "$f" ]]; then
    printf 'PASS %s\n' "$f"
  else
    printf 'FAIL missing %s\n' "$f"
    exit 1
  fi
done

printf '\nImplementation-manifest rule: touch only the approved boundary files above for the first protected post-15.2.0 implementation slice.\n'
