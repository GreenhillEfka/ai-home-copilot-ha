# HANDOFF — HA/HACS Recovery Basis for `copilot_ha`

**Status:** REVIEW REQUIRED (PilotClaw)
**Date:** 2026-03-22
**Lane:** A — HA/HACS repair
**Worktree:** `/config/clawd/team/worktrees/pilotsuite-styx-ha-current`
**Scope boundary:** HA/HACS surface only. No Core/Add-on changes proposed here.

---

## Recommendation

Use **`eb04fb51` (`v14.8.1`) as the recover basis** for the live HA/HACS surface.

### Why this is the safest basis

1. **It is the last tagged HA release point** in the current history.
   - `eb04fb51 (tag: v14.8.1) Release v14.8.1: sync HA zone presence contract`
2. **Current HEAD is untagged feature work** on top of that release basis.
   - `e8e9a19d feat: add schemas/ and habitus_entity_sorting.py to copilot_ha`
   - `37cede50 feat(habitus-zones): full WS API surface with copilot_core contract`
   - `e8e68f48 chore: align HA version files for PR #167 release hygiene`
3. **The post-tag delta is not minimal.**
   - Diff from `v14.8.1` to `HEAD` touches **17 files**, with **1466 insertions / 128 deletions**.
   - Main additions are new Habitus schema files, `habitus_entity_sorting.py`, expanded `habitus_zones_api.py`, JS card changes, and release/version metadata drift.
4. **The only direct setup-path change after `v14.8.1` is additive and unreviewed.**
   - `custom_components/copilot_ha/__init__.py` at HEAD newly registers `async_register_habitus_zone_api(hass)` during `async_setup_entry`.
   - This is absent in `v14.8.1` setup flow.
5. **Manifest metadata drift exists after the tag.**
   - `custom_components/copilot_ha/manifest.json`
     - `v14.8.1`: version `14.8.1`
     - `HEAD`: version `14.9.0` and added `"code": ["copilot_core>=1.0.0"]`
   - `VERSION` and `custom_components/copilot_ha/VERSION` were also bumped to `14.9.0`.

---

## Evidence gathered

### Git evidence

- Last tagged release in recent HA history:
  - `eb04fb51 (tag: v14.8.1)`
- Post-tag commits affecting HA surface:
  - `07e864fc docs: add v14.9.0 changelog entry — 390 files, 108K+ lines`
  - `e8e9a19d feat: add schemas/ and habitus_entity_sorting.py to copilot_ha`
  - `37cede50 feat(habitus-zones): full WS API surface with copilot_core contract`
  - `e8e68f48 chore: align HA version files for PR #167 release hygiene`

### File-level diff evidence vs `v14.8.1`

Changed files most relevant to HA/HACS recovery:
- `custom_components/copilot_ha/__init__.py`
- `custom_components/copilot_ha/habitus_zones_api.py`
- `custom_components/copilot_ha/habitus_entity_sorting.py`
- `custom_components/copilot_ha/schemas/*`
- `custom_components/copilot_ha/www/styx-zone-card.js`
- `custom_components/copilot_ha/manifest.json`
- `VERSION`
- `custom_components/copilot_ha/VERSION`
- `CHANGELOG.md`

### Validation evidence

- Syntax-only compile of the newly changed HA files succeeds (`py_compile` on changed Python files).
- Repo test baseline is noisy both at HEAD and at `v14.8.1`, so **the test suite does not provide a clean discriminating signal** for recovery selection.
- Because tests are not a strong tie-breaker here, the safer operational heuristic is:
  - **prefer the last tagged, smaller, previously released HA basis** over the untagged feature branch.

---

## Smallest safe recover/fix plan

### Plan A — preferred (live recovery)

1. **Recover HA/HACS to `v14.8.1` (`eb04fb51`)** as the live custom integration basis.
2. Confirm only HA-side files are part of the recovery:
   - `custom_components/copilot_ha/**`
   - root `hacs.json`
   - root `VERSION`
   - integration `manifest.json`
3. Restart/reload HA integration and verify success signals:
   - config entry present for domain `copilot_ha`
   - `copilot_ha` entities present
   - no import/setup failure on restart
4. Only after the live HA surface is stable, review whether any post-`v14.8.1` change is needed as a **small, separately reviewed cherry-pick**.

### Plan B — if reviewer insists on forward-fixing instead of recovery

Keep the live recovery target at `v14.8.1`, then review/cherry-pick post-tag changes one by one, starting with metadata-only changes last.

**Do not promote current HEAD wholesale** for live recovery.

---

## What changed in this lane

No HA integration code was changed in this worktree during this recovery analysis.

### Files changed by this lane
- `docs/HANDOFF-2026-03-22-HA-HACS-RECOVERY.md` (this handoff note)

---

## Reviewer handoff

### What changed
- No runtime code changes were applied.
- This lane produced an evidence-based recovery recommendation and separated:
  - HA/HACS repo state
  - release/tag history
  - setup-path deltas
  - validation limitations

### Why
- Current HEAD is an untagged feature state with extra HA surface changes beyond the last release.
- The task goal is safe restoration of the live `copilot_ha` surface, not feature continuation.

### Success signal
After reviewer-approved recovery to `v14.8.1`:
1. Home Assistant keeps a valid `copilot_ha` config entry
2. `copilot_ha` entities are created/present
3. restart/reload shows no import/setup failure for the integration

### Risks
- **If current HEAD is released as-is:** medium risk of shipping unrelated, unreviewed HA feature surface while trying to do a recovery.
- **If recovery mixes Core/Add-on assumptions into HA validation:** medium risk of false diagnosis.
- **If post-tag changes are cherry-picked without separation:** medium risk of recreating the unstable live state.

### Reviewer recommendation
**GO for review of a `v14.8.1`-based HA/HACS recovery.**
**NO-GO for releasing current HEAD as the HA recovery basis without a separate review pass.**
