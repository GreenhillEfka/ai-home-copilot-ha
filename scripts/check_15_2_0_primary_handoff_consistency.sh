#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PRIMARY="/config/clawd/team/workspaces/pilotsuite-stxy-sandbox/handoff/2026-03-27_hacs_releaser_prep_package.md"
CUTOVER="/config/clawd/team/workspaces/pilotsuite-stxy-sandbox/handoff/2026-03-27_hacs_releaser_cutover_input.md"
QUEUE="/config/clawd/team/workspaces/pilotsuite-stxy-sandbox/handoff/2026-03-27_release_queue_status_homeclaw_update.md"
CORE_REF="8b017a74"
HA_SOURCE="/config/clawd/team/repos/pilotsuite-styx-ha"

failures=0

check_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    printf 'PASS file %s\n' "$path"
  else
    printf 'FAIL missing %s\n' "$path"
    failures=$((failures + 1))
  fi
}

check_contains() {
  local path="$1"
  local needle="$2"
  local label="$3"
  if grep -Fq "$needle" "$path"; then
    printf 'PASS %s\n' "$label"
  else
    printf 'FAIL %s\n' "$label"
    failures=$((failures + 1))
  fi
}

printf 'HA/HACS 15.2.0 primary handoff consistency check\n'
printf 'Repo: %s\n' "$REPO_ROOT"

check_file "$PRIMARY"
check_file "$CUTOVER"
check_file "$QUEUE"

if [[ -f "$PRIMARY" ]]; then
  check_contains "$PRIMARY" "$HA_SOURCE" "primary handoff cites authoritative HA source"
  check_contains "$PRIMARY" "$CORE_REF" "primary handoff cites paired Core ref $CORE_REF"
  check_contains "$PRIMARY" "single primary HA/HACS releaser handoff artifact" "primary handoff declares single-primary role"
fi

if [[ -f "$CUTOVER" ]]; then
  check_contains "$CUTOVER" "$PRIMARY" "cutover input points to primary handoff"
  check_contains "$CUTOVER" "$CORE_REF" "cutover input cites paired Core ref $CORE_REF"
fi

if [[ -f "$QUEUE" ]]; then
  check_contains "$QUEUE" "$PRIMARY" "queue update points to primary handoff"
  check_contains "$QUEUE" "$CORE_REF" "queue update cites paired Core ref $CORE_REF"
fi

if [[ "$failures" -ne 0 ]]; then
  exit 1
fi
