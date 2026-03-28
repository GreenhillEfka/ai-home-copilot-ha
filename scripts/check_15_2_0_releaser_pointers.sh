#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HANDOFF_DIR_CANDIDATES=(
  "$REPO_ROOT/../../workspaces/pilotsuite-stxy-sandbox/handoff"
  "/config/clawd/team/workspaces/pilotsuite-stxy-sandbox/handoff"
)

HANDOFF_DIR=""
for candidate in "${HANDOFF_DIR_CANDIDATES[@]}"; do
  if [[ -d "$candidate" ]]; then
    HANDOFF_DIR="$candidate"
    break
  fi
done

if [[ -z "$HANDOFF_DIR" ]]; then
  echo "FAIL handoff directory not found" >&2
  exit 1
fi

ARTIFACTS=(
  "2026-03-27_hacs_releaser_prep_package.md"
  "2026-03-27_hacs_releaser_cutover_input.md"
  "2026-03-27_release_queue_status_homeclaw_update.md"
  "2026-03-27_hacs_rc_evidence_bundle.md"
  "2026-03-27_hacs_rc_candidate_freeze.md"
  "2026-03-27_hacs_rc_candidate_snapshot.tar.gz"
  "2026-03-27_hacs_rc_candidate_snapshot_manifest.json"
  "2026-03-27_hacs_rc_reviewer_acceptance_refresh.md"
  "2026-03-27_core_cutover_anchor_update.md"
)

missing=0
printf 'HA/HACS 15.2.0 releaser-pointer check\n'
printf 'Repo: %s\n' "$REPO_ROOT"
printf 'Handoff dir: %s\n' "$HANDOFF_DIR"

for rel in "${ARTIFACTS[@]}"; do
  path="$HANDOFF_DIR/$rel"
  if [[ -e "$path" ]]; then
    printf 'PASS %s\n' "$path"
  else
    printf 'FAIL %s\n' "$path"
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  exit 1
fi
