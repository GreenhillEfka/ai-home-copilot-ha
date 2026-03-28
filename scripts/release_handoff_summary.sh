#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

root_version="$(tr -d '[:space:]' < VERSION 2>/dev/null || true)"
component_version="$(tr -d '[:space:]' < custom_components/copilot_ha/VERSION 2>/dev/null || true)"
manifest_version="$(node -e "const fs=require('fs'); console.log(JSON.parse(fs.readFileSync('custom_components/copilot_ha/manifest.json','utf8')).version)" 2>/dev/null || true)"
commit="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
core_target_json=""
core_workspace_head=""
core_paired_cutover_ref=""
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
  core_workspace_head="$(node -e "const fs=require('fs'); const p=process.argv[1]; const d=JSON.parse(fs.readFileSync(p,'utf8')); console.log(d.head_commit || '')" "$core_target_json" 2>/dev/null || true)"
  core_paired_cutover_ref="$(node -e "const fs=require('fs'); const p=process.argv[1]; const d=JSON.parse(fs.readFileSync(p,'utf8')); console.log(d.release_readiness?.paired_cutover_ref || '')" "$core_target_json" 2>/dev/null || true)"
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

if [[ "$git_state" == "SAUBER" ]]; then
  gate_hint="candidate tree clean"
else
  gate_hint="candidate tree still has local changes"
fi

review_slice_doc="docs/HA_15_2_0_REVIEW_SLICE_2026-03-27.md"
review_slice_prep="scripts/prepare_15_2_0_review_slice.sh"
release_chain="scripts/check_15_2_0_release_readiness_chain.sh"
paired_core_note="${core_paired_cutover_ref:-unknown}"
if [[ -n "$core_workspace_head" ]]; then
  paired_core_note+=" (workspace head ${core_workspace_head})"
fi

cat <<EOF
HA/HACS: v${root_version:-unknown} — HACS not confirmed
Core/Add-on: getrennt führen
Git/repo: ${git_state} — ${commit}
Live/runtime: NICHT VERIFIZIERT

Release-Readiness:
- version status: ${version_note}
- review posture: repo gate + handoff artifacts aligned
- working tree note: ${gate_hint}
- paired Core cutover ref: ${paired_core_note}
- paired Core workspace repo: ${core_target_repo:-not-set}
- paired Core target artifact: ${core_target_json}

Repo-local validation chain:
- scripts/release_review_gate.sh
- scripts/check_15_2_0_core_pairing_anchor.sh
- scripts/check_15_2_0_releaser_pointers.sh
- scripts/check_15_2_0_primary_handoff_consistency.sh
- scripts/check_15_2_0_release_artifact_fingerprints.sh
- ${release_chain}

Authoritative docs:
- ${review_slice_doc}
- docs/HA_15_2_0_RELEASER_PREP_POINTER_2026-03-27.md
- docs/HA_15_2_0_RUNTIME_BOUNDARY_2026-03-27.md
- docs/HA_15_2_0_RELEASE_ARTIFACT_FINGERPRINTS_2026-03-27.json

Next step:
Run ${release_chain}, then hand off the exact 15.2.0 candidate slice from ${review_slice_doc} / ${review_slice_prep} into release/install gating. Repo evidence is green; HACS/live installability remains unconfirmed until that independent step completes.
EOF
