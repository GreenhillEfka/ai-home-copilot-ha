#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FILES=(
  "docs/HA_NEXT_VERSION_DEV_BOUNDARY_2026-03-27.md"
  "docs/HA_NEXT_VERSION_BOUNDARY_CROSSING_PROPOSAL_NV_HA_001_2026-03-27.md"
  "docs/HA_NEXT_VERSION_REVIEW_ASK_NV_HA_001_2026-03-27.md"
  "docs/HA_NEXT_VERSION_REVIEW_PACKET_NV_HA_001_2026-03-27.md"
  "docs/HA_NEXT_VERSION_REVIEW_DECISION_TEMPLATE_2026-03-27.md"
  "docs/HA_NEXT_VERSION_REVIEW_HANDOFF_NV_HA_001_2026-03-27.md"
  "scripts/prepare_next_version_dev_boundary.sh"
  "scripts/prepare_next_version_boundary_crossing.sh"
  "scripts/prepare_next_version_review_packet.sh"
  "scripts/prepare_next_version_review_decision.sh"
  "scripts/prepare_next_version_review_handoff.sh"
)

printf 'HA/HACS next-version review handoff prep\n'
printf 'Repo: %s\n\n' "$REPO_ROOT"

printf '== protected line boundary guard ==\n'
./scripts/prepare_next_version_dev_boundary.sh >/dev/null
printf 'PASS protected 15.2.0 line remains intact before review-handoff prep\n\n'

printf '== review decision guard ==\n'
./scripts/prepare_next_version_review_decision.sh >/dev/null
printf 'PASS review decision inputs are intact\n\n'

printf '== review handoff artifacts ==\n'
for f in "${FILES[@]}"; do
  if [[ -e "$f" ]]; then
    printf 'PASS %s\n' "$f"
  else
    printf 'FAIL missing %s\n' "$f"
    exit 1
  fi
done

printf '\nReview-handoff rule: route reviewer/design through the single review handoff note and capture the answer in a decision artifact before any protected-file implementation work begins.\n'
