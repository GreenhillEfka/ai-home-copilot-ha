# HANDOFF-SPEC: Zone Presence Hold — Lovelace UI Visibility

**Status:** DONE (Stxy, bc205384)  
**Date:** 2026-03-21  
**Branch:** `main` (HA)  
**Ticket:** PS-202 (implied)  
**Priority:** P2 (Live-Test-Blocking)

---

## DONE / ✅ COMMITTED

### Commit bc205384 — "fix(ux): zone icon map for German zone IDs + partial/error states"

Files:
- `custom_components/copilot_ha/www/styx-zone-card.js` (+46 -5 lines)

Changes:
1. **ZONE_ICON_MAP** now includes German zone IDs → fixes missing icons for `wohn_bereich`, `badbereich`, `kochbereich`, etc.
2. **Zone status "Daten fehlen"** when no `sensor.pilotsuite_brain_graph_nodes` data
3. **Health badge "—"** when no zone health score
4. **CSS states** `.zone-status.unavailable`, `.zone-card.data-unavailable`, `.health-badge.unavailable`

---

## OPEN / HANDOFF TO PILOTCLAW

### Issue: `presence_hold` not visible in Lovelace cards

**Current state:**
- `dashboard/static/css/dashboard.css` (commit 669a9e66): `.hold-pill` CSS classes exist ✅
- `dashboard/static/js/zone_cards.js` (commit 669a9e66): `_updateHoldPills()` + socket event `presence_hold` exists ✅
- `coordinator.py`: `async_set_zone_presence_hold()` calls Core API ✅ (path verified: `/api/v1/presence/zone/presence/{zone_id}/hold`)
- **Lovelace cards (`www/styx-zone-card.js`)**: NO hold-pill UI rendering

**Root cause:** The hold-pill UI only exists in `dashboard/static/js/zone_cards.js` (old dashboard). The Lovelace custom card `styx-zone-card.js` has no hold UI section.

---

### FILES

| File | Action | Owner |
|------|--------|-------|
| `custom_components/copilot_ha/www/styx-zone-card.js` | ADD hold-pill HTML + `_buildHoldPills()` method | PilotClaw |
| `custom_components/copilot_ha/coordinator.py` (lines 508-517) | Already implemented, no changes needed | — |
| `dashboard/static/js/zone_cards.js` | Legacy dashboard, no changes needed | — |

---

### ACCEPTANCE CRITERIA

1. Each zone card in `styx-zone-card.js` shows a **hold control row** with three pills: `Auto` / `Anwesend` / `Abwesend`
2. Active pill matches the zone's current `presence_hold` state from `sensor.pilotsuite_zone_X_presence` or `sensor.pilotsuite_brain_graph_nodes` attributes
3. Clicking a pill calls `coordinator.async_set_zone_presence_hold(zone_id, hold_value)` via the API
4. When Core is unreachable, hold state is set locally and shows a toast/indicator "Lokaler Modus"
5. CSS: use existing `.hold-pill` classes from `dashboard/static/css/dashboard.css` (import or copy)

**Verification:** After PR merge:
1. Open HA Lovelace dashboard → Zone tab
2. Each zone card should show hold pills below the status row
3. Click "Anwesend" → sensor should update → pill should activate
4. Disconnect Core → should show "Lokaler Modus" indicator

---

### SMALLEST BUILD-SLICE

Only `styx-zone-card.js` changes. No contract/API changes. No new sensors needed.

Steps:
1. Read current `_buildZoneCard()` method in `styx-zone-card.js`
2. Add `_getHoldState(zoneId)` helper — reads from `sensor.pilotsuite_brain_graph_nodes` attributes or zone entity state
3. Add `_buildHoldPills(zoneId, holdState)` method — returns HTML string with three `.hold-pill` elements
4. Insert hold-pill HTML into `_buildZoneCard()` return template, after the status row
5. Add click handlers via `this._config.hass` → call `window.dispatchEvent` or direct API
6. Import/copy `.hold-pill` CSS from `dashboard/static/css/dashboard.css` lines 724-780 into `styx-zone-card.js` shadow DOM `<style>`

**Risk:** MEDIUM (UI-only, no backend changes, no breaking changes)  
**Fallback if Core API fails:** UI shows error toast, pill stays in previous state  
**Test:** Manual only, no existing automated test coverage for this UI path

---

### RISK

- **Breaking:** No — purely additive UI
- **Contract drift:** No — no API or sensor changes
- **Performance:** Minimal — one extra sensor read per zone render cycle

---

### NEXT (if Handoff accepted)

PilotClaw picks up the implementation. Notify @A.Betz when PR is ready for live testing.
