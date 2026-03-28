#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FILES=(
  "docs/HA_NEXT_VERSION_DEV_BOUNDARY_2026-03-27.md"
  "docs/HA_NEXT_VERSION_BOUNDARY_CROSSING_TEMPLATE_2026-03-27.md"
  "docs/HA_NEXT_VERSION_BOUNDARY_CROSSING_PROPOSAL_NV_HA_001_2026-03-27.md"
  "docs/HA_NEXT_VERSION_REVIEW_ASK_NV_HA_001_2026-03-27.md"
  "docs/HA_NEXT_VERSION_REVIEW_PACKET_NV_HA_001_2026-03-27.md"
  "docs/HA_NEXT_VERSION_REVIEW_DECISION_TEMPLATE_2026-03-27.md"
  "scripts/prepare_next_version_dev_boundary.sh"
  "scripts/prepare_next_version_boundary_crossing.sh"
  "scripts/prepare_next_version_review_packet.sh"
  "scripts/prepare_next_version_review_decision.sh"
)

printf 'HA/HACS next-version review decision prep\n'
printf 'Repo: %s\n\n' "$REPO_ROOT"

printf '== protected line boundary guard ==\n'
./scripts/prepare_next_version_dev_boundary.sh >/dev/null
printf 'PASS protected 15.2.0 line remains intact before review-decision prep\n\n'

printf '== review packet guard ==\n'
./scripts/prepare_next_version_review_packet.sh >/dev/null
printf 'PASS review packet inputs are intact\n\n'

printf '== review decision artifacts ==\n'
for f in "${FILES[@]}"; do
  if [[ -e "$f" ]]; then
    printf 'PASS %s\n' "$f"
  else
    printf 'FAIL missing %s\n' "$f"
    exit 1
  fi
done

printf '\nReview-decision rule: record reviewer/design output in an explicit artifact before opening any protected-file implementation slice.\n'
