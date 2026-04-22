# PILOTSUITE_PROGRESS_LEDGER.md
## Stand: 2026-04-22 21:45 MESZ

### Shared truth locations
- Core worktree: `/config/clawd/team/worktrees/pilotsuite-styx-core-current/`
- Core remote: `origin/main` → `https://github.com/GreenhillEfka/pilotsuite-styx-core.git`
- HA worktree: `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/`
- HA remote: `origin/main` → `https://github.com/GreenhillEfka/pilotsuite-styx-ha.git`
- PilotClaw agent dir: `/config/clawd/agents/pilotclaw/`
- Shared handoffs: `/config/clawd/team/shared/handoffs/`

---

## CORE — CLOSED (2026-04-22)
- CORE-NEURON-201 ✅
- CORE-HABITUS-202 ✅
- CORE-AUTO-203 ✅ (A: Zone/Habitus → notification)
- CORE-HARDEN-204 ✅ (RuleMatcher save/load) — `2de60597`
- CORE-HARDEN-205 ✅ (ha_module API 22 tests) — `df7b1122`
- CORE-HARDEN-206 ✅ (notifications API 28 tests) — `89118bc4`
- CORE-HARDEN-207 ✅ (autonomy API 19 tests) — `d77683d1`

## CORE — CURRENT
- HEAD: `d77683d1` (autonomy API contract, 19 tests)
- Suite: 85 tests green (76 new since HARDEN-204)
- Mode: systematic fast dev, idle gaps = zero

## HA — CURRENT
- HA-E2E-303 ✅ file-backed closed (`7e6eb892`)
- HA-559: in progress (HomeClaw lane)
- HA-E2E-303 → CORE-HARDEN-204-NAMING → CORE-HARDEN-204 (queue gate resolved)

## Queue truth (2026-04-22 23:10)
1. **Recommended next Core path (Option A):** `HARDEN-208` (sensors API) -> `HARDEN-209` (state API) -> `AUTO-203-B` (notification delivery)
2. HomeClaw runs in parallel only on the active truthful HA seam: finish `HA-559` if still active, otherwise prepare the exact HA consumer seam behind the next Core delivery landing
3. DesignClaw remains support-only and may only shape exact unblock packets behind the active builder pull

## New lead plan
- File-backed acceleration plan landed: `/config/clawd/team/shared/handoffs/2026-04-22_ORAKEL_CORE_ACCELERATION_EXECUTION_PLAN.md`
- Goal: faster systematic Core development with bounded research, prepared next-pull packets, zero idle gaps, and HA pulled along only on real consumer seams
- Broad route: Core spine hardening -> automation delivery extension -> HA consumer follow-through -> visible E2E consolidation -> release gate

## Operating mode
- Systematic fast dev: hard builder loop, idle gaps at zero
- topic:1 only: landing / real blocker / next exact pull
- CORE advances autonomous
- HA owns HA seams

## Test suite snapshot
```
tests/test_autonomy_api_contract.py         19 passed
tests/test_notifications_api_contract.py    28 passed
tests/test_ha_module_api_contract.py         22 passed
tests/test_rule_persistence_contract.py       7 passed
tests/test_core_auto_203_a_contract.py       9 passed (inherited)
Total:                                      85 passed
```

## Systematic fast dev — 4 landungen in ~100 min
| Item         | Time  | Tests | Status |
|-------------|-------|-------|--------|
| HARDEN-204  | 20:22 | 7     | ✅     |
| HARDEN-205  | 20:40 | 22    | ✅     |
| HARDEN-206  | 21:00 | 28    | ✅     |
| HARDEN-207  | 21:45 | 19    | ✅     |
