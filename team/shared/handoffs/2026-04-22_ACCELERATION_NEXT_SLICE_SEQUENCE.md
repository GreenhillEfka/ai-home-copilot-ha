# 2026-04-22 Bound next slice sequence after Andreas approval

**Stand:** 2026-04-22 23:16 Europe/Berlin
**Trigger:** Andreas approved the acceleration route with `Sehr gut`.
**Lead effect:** this is now the bound execution sequence until a real blocker or real decision appears.

## Operating rules for every slice
Before code:
1. read current seam file
2. read current proof/test ring
3. read one supporting handoff/doc only if needed

Then run the hard loop:
`exact pull -> implement -> focused proof -> commit -> checkpoint -> next exact pull`

## Exact sequence now

**Fresh truth correction:** `CORE-HARDEN-208` has already landed on fresh queue truth while this packet was being cut. The active forward sequence therefore starts at `CORE-HARDEN-209`.

### HA-GATE-CHECK — HomeClaw truth check before parallel HA motion
**Owner:** HomeClaw
**Task:** verify whether `HA-559` is genuinely still the active truthful HA seam.
**Allowed outcomes only:**
- `HA-559` is active -> continue and close it with one bounded proof ring
- `HA-559` is stale -> do not reopen it; instead prepare the exact next HA consumer seam behind the next Core delivery landing
- real blocker -> surface once

**Non-goal:** no speculative HA side work

---

### CORE-HARDEN-208 — sensors API
**Status:** already landed on fresh queue truth (`ba4af24e`, `22 passed`)

---

### CORE-HARDEN-209 — dominant remaining state API seam
**Owner:** PilotClaw
**Task type:** one bounded naming + implementation packet fixed from fresh repo truth immediately after `CORE-HARDEN-208`

**Packet rule:**
The owner must pin, before code:
- exact `/state` surface chosen
- exact target file(s)
- exact proof ring
- exact success signal

**Current honest framing:**
- `HARDEN-209` remains the next state-surface hardening item
- the exact state seam must be fixed from fresh post-`HARDEN-208` repo truth, not guessed early here

**Non-goal:**
- do not bundle multiple unrelated state endpoints

---

### CORE-AUTO-203-B — notification delivery
**Owner:** PilotClaw
**Exact seam:** existing proactive notification delivery path only
**Target files:**
- `addons/pilotsuite/app/copilot_core/proactive_engine.py`
- `tests/test_core_auto_203_b_notification_delivery_contract.py`

**Focused proof ring:**
- `python3 -m py_compile addons/pilotsuite/app/copilot_core/proactive_engine.py`
- `pytest -q tests/test_core_auto_203_b_notification_delivery_contract.py`

**Success signal:**
- delivery stays on the canonical notification seam only
- no-token failure, bearer-auth delivery, request-failure path, and HTTP-failure path stay green
- HA gets one exact consumer seam behind this landing

**Non-goals:**
- no MQTT widening
- no dashboard widening
- no second action family beyond notification delivery

---

### HA-FOLLOW-DELIVERY — exact HA consumer seam behind Core delivery
**Owner:** HomeClaw
**Task:** mirror only the real consumer seam produced by `CORE-AUTO-203-B`
**Examples allowed:**
- visible notification confirmation
- exact dashboard/status projection tied to the landed delivery seam
- exact automation-visible consumer bind

**Non-goals:**
- no unrelated configuration detours
- no speculative UI work detached from the delivery seam

---

### E2E-CONSOLIDATION-01 — first stronger visible automation path
**Owners:** PilotClaw + HomeClaw, each on own seam
**Target shape:**
- Zone/Habitus state
- Core decision/rule
- notification delivery
- HA-visible confirmation

**Success signal:** one truthful visible end-to-end automation path is provable without prose-only claims.

## Queue rule
- active forward order from fresh truth is now: `HA-GATE-CHECK -> CORE-HARDEN-209 -> CORE-AUTO-203-B -> HA-FOLLOW-DELIVERY -> E2E-CONSOLIDATION-01`
- `topic:1` stays result-only: landing / real blocker / next exact pull
- Orakel must keep the next two packets ahead of the active builder
- DesignClaw stays support-only behind exact unblock asks
