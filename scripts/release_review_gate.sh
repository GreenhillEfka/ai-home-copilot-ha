#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

errors=0
warns=0

pass() {
  printf 'PASS %s\n' "$1"
}

warn() {
  warns=$((warns + 1))
  printf 'WARN %s\n' "$1"
}

fail() {
  errors=$((errors + 1))
  printf 'FAIL %s\n' "$1"
}

require_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    pass "file present: $path"
  else
    fail "missing required file: $path"
  fi
}

read_json_field() {
  local path="$1"
  local field="$2"
  node -e "const fs=require('fs'); const data=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); const v=data[process.argv[2]]; if (v===undefined) process.exit(2); if (typeof v==='object') console.log(JSON.stringify(v)); else console.log(String(v));" "$path" "$field"
}

printf '== PilotSuite HA/HACS release review gate ==\n'
printf 'Repo: %s\n' "$REPO_ROOT"

require_file "VERSION"
require_file "hacs.json"
require_file "custom_components/copilot_ha/VERSION"
require_file "custom_components/copilot_ha/manifest.json"
require_file "custom_components/copilot_ha/__init__.py"
require_file "custom_components/copilot_ha/config_flow.py"
require_file "custom_components/copilot_ha/www/styx-card-base.js"
require_file "custom_components/copilot_ha/www/styx-zone-card.js"

root_version="$(tr -d '[:space:]' < VERSION)"
component_version="$(tr -d '[:space:]' < custom_components/copilot_ha/VERSION)"
manifest_version="$(read_json_field custom_components/copilot_ha/manifest.json version || true)"

if [[ -n "$root_version" && "$root_version" == "$component_version" && "$root_version" == "$manifest_version" ]]; then
  pass "version alignment root/component/manifest = $root_version"
else
  fail "version mismatch root=$root_version component=$component_version manifest=$manifest_version"
fi

hacs_name="$(read_json_field hacs.json name || true)"
hacs_zip_release="$(read_json_field hacs.json zip_release || true)"
hacs_content_in_root="$(read_json_field hacs.json content_in_root || true)"
hacs_filename="$(read_json_field hacs.json filename || true)"
manifest_domain="$(read_json_field custom_components/copilot_ha/manifest.json domain || true)"
manifest_name="$(read_json_field custom_components/copilot_ha/manifest.json name || true)"
manifest_config_flow="$(read_json_field custom_components/copilot_ha/manifest.json config_flow || true)"

[[ "$hacs_name" == "PilotSuite" ]] \
  && pass 'hacs.json name = PilotSuite' \
  || fail "unexpected hacs.json name: $hacs_name"

[[ "$hacs_zip_release" == "true" ]] \
  && pass 'hacs.json zip_release = true' \
  || fail "zip_release must be true, got: $hacs_zip_release"

[[ "$hacs_content_in_root" == "false" ]] \
  && pass 'hacs.json content_in_root = false' \
  || fail "content_in_root must be false, got: $hacs_content_in_root"

[[ "$hacs_filename" == "pilotsuite-styx-ha.zip" ]] \
  && pass 'hacs.json filename = pilotsuite-styx-ha.zip' \
  || fail "unexpected hacs filename: $hacs_filename"

[[ "$manifest_domain" == "copilot_ha" ]] \
  && pass 'manifest domain = copilot_ha' \
  || fail "unexpected manifest domain: $manifest_domain"

[[ "$manifest_name" == "PilotSuite" ]] \
  && pass 'manifest name = PilotSuite' \
  || fail "unexpected manifest name: $manifest_name"

[[ "$manifest_config_flow" == "true" ]] \
  && pass 'manifest config_flow = true' \
  || fail "config_flow must be true, got: $manifest_config_flow"

frontend_count="$(find custom_components/copilot_ha/www -maxdepth 1 -type f -name 'styx-*.js' | wc -l | tr -d '[:space:]')"
if [[ "$frontend_count" -ge 8 ]]; then
  pass "frontend card asset count looks complete ($frontend_count styx-*.js files)"
else
  fail "frontend card asset count too low ($frontend_count)"
fi

tracked_debug="$({
  git ls-files -- \
    ':(exclude)archive/**' \
    ':(exclude)team/**' \
    ':(exclude).venv/**' \
    ':(exclude)node_modules/**' \
    ':(exclude).pytest_cache/**' \
    | grep -E '(^|/)(\.coverage|__pycache__/|coverage\.json$|.*\.pyc$)' || true
} )"
if [[ -z "$tracked_debug" ]]; then
  pass 'no tracked debug artifacts detected'
else
  fail "tracked debug artifacts detected:\n$tracked_debug"
fi

tracked_non_hacs_surface="$({
  git ls-files -- \
    ':(exclude)archive/**' \
    ':(exclude)team/**' \
    ':(exclude).venv/**' \
    ':(exclude)node_modules/**' \
    ':(exclude).pytest_cache/**' \
    | grep -E '^dashboard/' || true
} )"
if [[ -z "$tracked_non_hacs_surface" ]]; then
  pass 'no tracked repo-root dashboard surface detected'
else
  warn "tracked repo-root dashboard surface present (non-HACS advisory only):\n$tracked_non_hacs_surface"
fi

if git diff --quiet --ignore-submodules HEAD --; then
  pass 'working tree clean'
else
  warn 'working tree has local changes (review before release)'
fi

printf '\nSummary: %s fail / %s warn\n' "$errors" "$warns"

if [[ "$errors" -gt 0 ]]; then
  exit 1
fi
