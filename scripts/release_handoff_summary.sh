#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

root_version="$(tr -d '[:space:]' < VERSION 2>/dev/null || true)"
component_version="$(tr -d '[:space:]' < custom_components/copilot_ha/VERSION 2>/dev/null || true)"
manifest_version="$(node -e "const fs=require('fs'); console.log(JSON.parse(fs.readFileSync('custom_components/copilot_ha/manifest.json','utf8')).version)" 2>/dev/null || true)"
commit="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
core_target_json=""
core_target_commit=""
core_target_repo=""

for candidate in \
  "$REPO_ROOT/team/workspaces/pilotsuite-stxy-sandbox/handoff/core_workspace_target.json" \
  "$REPO_ROOT/../../workspaces/pilotsuite-stxy-sandbox/handoff/core_workspace_target.json" \
  "/config/clawd/team/workspaces/pilotsuite-stxy-sandbox/handoff/core_workspace_target.json"
do
  if [[ -f "$candidate" ]]; then
    core_target_json="$candidate"
    break
  fi
done

if [[ -n "$core_target_json" ]]; then
  core_target_commit="$(node -e "const fs=require('fs'); const p=process.argv[1]; const d=JSON.parse(fs.readFileSync(p,'utf8')); console.log(d.head_commit || '')" "$core_target_json" 2>/dev/null || true)"
  core_target_repo="$(node -e "const fs=require('fs'); const p=process.argv[1]; const d=JSON.parse(fs.readFileSync(p,'utf8')); console.log(d.repo || '')" "$core_target_json" 2>/dev/null || true)"
fi

if git diff --quiet --ignore-submodules HEAD -- 2>/dev/null; then
  git_state="SAUBER"
else
  git_state="VERUNREINIGT"
fi

if [[ -n "$root_version" && "$root_version" == "$component_version" && "$root_version" == "$manifest_version" ]]; then
  version_note="aligned"
else
  version_note="mismatch: root=$root_version component=$component_version manifest=$manifest_version"
fi

cat <<EOF
HA/HACS: v${root_version:-unknown}  ❌
Core/Add-on: getrennt führen
Git: ${git_state} — ${commit}
live verifiziert: NEIN

Problem: Live-Integration lädt nicht; Release-Readiness muss über Repo-Gate + reviewer handoff abgesichert werden.
Nächster Schritt: Builder arbeitet gegen docs/FRONTEND_EDITOR_HANDOFF.md, danach angekündigt scripts/release_review_gate.sh laufen lassen.

Artifacts:
- scripts/release_review_gate.sh
- scripts/release_handoff_summary.sh
- docs/HACS_RELEASE_REVIEW_GATE.md
- docs/FRONTEND_EDITOR_HANDOFF.md
- version status: ${version_note}
- paired Core workspace target: ${core_target_commit:-unknown} (${core_target_repo:-not-set})
- paired Core target artifact: ${core_target_json}
EOF
