#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

printf 'HA/HACS 15.2.0 release-readiness chain\n'
printf 'Repo: %s\n\n' "$REPO_ROOT"

run_step() {
  local label="$1"
  shift
  printf '== %s ==\n' "$label"
  "$@"
  printf '\n'
}

run_step "review gate" ./scripts/release_review_gate.sh
run_step "review slice presence" ./scripts/prepare_15_2_0_review_slice.sh --check
run_step "sync-anchor consistency" ./scripts/check_15_2_0_sync_anchor_consistency.sh
run_step "core-pairing anchor" ./scripts/check_15_2_0_core_pairing_anchor.sh
run_step "releaser-pointer existence" ./scripts/check_15_2_0_releaser_pointers.sh
run_step "primary handoff consistency" ./scripts/check_15_2_0_primary_handoff_consistency.sh
run_step "release-artifact fingerprints" ./scripts/check_15_2_0_release_artifact_fingerprints.sh

printf 'HA/HACS 15.2.0 release-readiness chain: PASS\n'
