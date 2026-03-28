#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FILES=(
  "VERSION"
  "custom_components/copilot_ha/VERSION"
  "custom_components/copilot_ha/manifest.json"
  "hacs.json"
  "custom_components/copilot_ha/www/styx-card-base.js"
  "custom_components/copilot_ha/www/styx-zone-card.js"
  "custom_components/copilot_ha/www/styx-mood-card.js"
  "custom_components/copilot_ha/www/styx-household-card.js"
  "custom_components/copilot_ha/www/styx-neural-card.js"
  "custom_components/copilot_ha/www/styx-chat-card.js"
  "custom_components/copilot_ha/www/styx-error-card.js"
  "custom_components/copilot_ha/www/styx-suggestions-card.js"
  "custom_components/copilot_ha/www/styx-brain-card.js"
  "custom_components/copilot_ha/www/styx-habitus-card.js"
  "docs/HA_15_2_0_RELEASE_ARTIFACT_FINGERPRINTS_2026-03-27.json"
  "scripts/release_review_gate.sh"
  "scripts/release_handoff_summary.sh"
  "scripts/check_15_2_0_core_pairing_anchor.sh"
  "scripts/check_15_2_0_release_artifact_fingerprints.sh"
  "scripts/check_15_2_0_release_readiness_chain.sh"
)

usage() {
  cat <<'EOF'
prepare_15_2_0_review_slice.sh

Default: print the exact 15.2.0 candidate review slice and current git status.

Options:
  --apply   stage the exact review-slice file set with git add
  --check   verify every expected file exists
  --help    show this help
EOF
}

print_list() {
  printf '15.2.0 candidate review slice files:\n'
  printf ' - %s\n' "${FILES[@]}"
}

check_files() {
  local missing=0
  for f in "${FILES[@]}"; do
    if [[ ! -e "$f" ]]; then
      printf 'MISSING %s\n' "$f" >&2
      missing=1
    fi
  done
  return "$missing"
}

show_status() {
  printf '\nCurrent git status for review-slice files:\n'
  git status --short -- "${FILES[@]}" || true
}

mode="print"
case "${1:-}" in
  --apply) mode="apply" ;;
  --check) mode="check" ;;
  --help|-h) usage; exit 0 ;;
  "") ;;
  *) usage >&2; exit 1 ;;
esac

check_files

case "$mode" in
  print)
    print_list
    show_status
    ;;
  check)
    print_list
    printf '\nAll review-slice files are present.\n'
    show_status
    ;;
  apply)
    git add -- "${FILES[@]}"
    printf 'Staged 15.2.0 review slice:\n'
    git diff --cached --name-only -- "${FILES[@]}"
    ;;
esac
