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
  "docs/HA_NEXT_VERSION_BOUNDARY_CROSSING_PROPOSAL_NV_HA_001_2026-03-27.md"
  "docs/HA_NEXT_VERSION_REVIEW_ASK_NV_HA_001_2026-03-27.md"
  "docs/HA_NEXT_VERSION_REVIEW_PACKET_NV_HA_001_2026-03-27.md"
  "scripts/prepare_next_version_dev_boundary.sh"
  "scripts/prepare_next_version_slice.sh"
  "scripts/prepare_next_version_boundary_crossing.sh"
  "scripts/prepare_next_version_review_packet.sh"
)

printf 'HA/HACS next-version review packet prep\n'
printf 'Repo: %s\n\n' "$REPO_ROOT"

printf '== protected line boundary guard ==\n'
./scripts/prepare_next_version_dev_boundary.sh >/dev/null
printf 'PASS protected 15.2.0 line remains intact before review-packet work\n\n'

printf '== next-version boundary-crossing guard ==\n'
./scripts/prepare_next_version_boundary_crossing.sh >/dev/null
printf 'PASS next-version boundary-crossing packet inputs are intact\n\n'

printf '== review packet artifacts ==\n'
for f in "${FILES[@]}"; do
  if [[ -e "$f" ]]; then
    printf 'PASS %s\n' "$f"
  else
    printf 'FAIL missing %s\n' "$f"
    exit 1
  fi
done

printf '\nReview-packet rule: request the reviewer/design boundary decision before touching protected 15.2.0 files.\n'
