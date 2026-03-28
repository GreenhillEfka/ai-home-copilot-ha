#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FILES=(
  "docs/HA_NEXT_VERSION_REVIEW_HANDOFF_NV_HA_001_2026-03-27.md"
  "docs/HA_NEXT_VERSION_REVIEW_REQUEST_NV_HA_001_2026-03-27.md"
  "docs/HA_NEXT_VERSION_REVIEW_DECISION_TEMPLATE_2026-03-27.md"
  "docs/HA_NEXT_VERSION_REVIEW_DECISION_NV_HA_001_PENDING_2026-03-27.md"
  "scripts/prepare_next_version_review_handoff.sh"
  "scripts/prepare_next_version_review_decision_capture.sh"
)

printf 'HA/HACS next-version review decision capture prep\n'
printf 'Repo: %s\n\n' "$REPO_ROOT"

printf '== review handoff guard ==\n'
./scripts/prepare_next_version_review_handoff.sh >/dev/null
printf 'PASS review handoff inputs are intact\n\n'

printf '== decision capture artifacts ==\n'
for f in "${FILES[@]}"; do
  if [[ -e "$f" ]]; then
    printf 'PASS %s\n' "$f"
  else
    printf 'FAIL missing %s\n' "$f"
    exit 1
  fi
done

if grep -Fq 'accept boundary as proposed' docs/HA_NEXT_VERSION_REVIEW_DECISION_NV_HA_001_2026-03-27.md || grep -Fq 'accept with narrowed boundary' docs/HA_NEXT_VERSION_REVIEW_DECISION_NV_HA_001_2026-03-27.md || grep -Fq 'accept with widened boundary' docs/HA_NEXT_VERSION_REVIEW_DECISION_NV_HA_001_2026-03-27.md || grep -Fq 'reject for now' docs/HA_NEXT_VERSION_REVIEW_DECISION_NV_HA_001_2026-03-27.md; then
  printf '\nPASS reviewer/design decision artifact is captured and usable\n'
else
  printf '\nFAIL reviewer/design decision artifact does not contain an accepted decision shape\n'
  exit 1
fi

printf '\nDecision-capture rule: implementation may only proceed if the decision artifact explicitly authorizes a protected boundary.\n'
