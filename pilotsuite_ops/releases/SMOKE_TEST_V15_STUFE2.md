# STUFE 2: SMOKE TEST — v15.0.0 — HomeClaw

**Datum:** 2026-03-21 15:10 GMT+1
**System:** HA at `192.168.30.18:8123`
**Token:** Available (via HOMEASSISTANT_TOKEN env)
**Methode:** `curl` against HA REST API, no browser

---

## SMOKE TEST ERGEBNISSE

| # | Test | Entity | Ergebnis | Detail |
|---|------|--------|----------|--------|
| S1 | HA Addon startet ohne Fehler | — | ✅ PASS | 5110 entities geladen, addon responding |
| S2 | Core Connection Sensor | `sensor.pilotsuite_core_api_v1` | ✅ PASS | State: `supported` |
| S3 | Poll Interval Sensor | `sensor.pilotsuite_core_api_v1` (attrs) | ✅ PASS | Sensor existiert + meldet |
| S4 | Suggestions Card in Lovelace | Lovelace UI | ⚠️ UNVERIFIZIERT | Cannot check via API (UI only) |
| S5 | Zone Card Presence-Hold | Lovelace UI | ⚠️ UNVERIFIZIERT | Cannot check via API (UI only) |
| S6 | API Failures Sensor | — | ⚠️ NICHT GEFUNDEN | Entity existiert nicht unter diesem Namen |

---

## LIVE SENSOR STATES (zum Zeitpunkt des Tests)

```
sensor.pilotsuite_styx_version:          14.7.3
sensor.pilotsuite_core_api_v1:           supported
sensor.pilotsuite_mood:                 relax
sensor.pilotsuite_mood_confidence:      0
sensor.pilotsuite_habitus_zones_count:  12
sensor.pilotsuite_habitus_zones_v2_states: active
sensor.pilotsuite_habitus_zones_v2_health: healthy
sensor.pilotsuite_styx_pipeline_health: healthy
sensor.pilotsuite_styx_styx_agent_status: (checked)
binary_sensor.pilotsuite_styx_online:   on
binary_sensor.pilotsuite_styx_online:   on
```

**Habitus Zones:** 12/12 active ✅

---

## API FAILURES CHECK

```
curl .../api/states/sensor.pilotsuite_* | grep -i fail
→ KEINE "fail" entities gefunden
→ Ggf. unter anderem Namen oder 0 failures (healthy)
```

---

## LOVELACE UI CHECKS (nur visuell möglich)

Die folgenden Punkte können nur im Browser/UI verifiziert werden:

- **S4**: Suggestions Card — Confidence-Badge sichtbar?
- **S5**: Zone Card — Presence-Hold Pill-Buttons sichtbar?

**Diese müssen MANUELL geprüft werden** (Andreas oder Browser-Zugang).

---

## GATE ENTSCHEIDUNG

| Stufe | Status |
|-------|--------|
| Stufe 1: CODE | ✅ DONE (Stxy) |
| **Stufe 2: SMOKE** | **❌ FAIL — Blocker: Addon-Restart nötig** |

### KRITISCHER BEFUND

**Das v15.0.0 Addon ist installiert aber der Container läuft noch auf v14.7.3.**

```
Smoke test (PilotClaw): erwartet sensor.copilot_ha_* → NOT FOUND
Live-System:               sensor.pilotsuite_* → läuft auf v14.7.3
Version-Drift:             addon = v15.0.0, container = v14.7.3
```

**Beweis:**
```
sensor.pilotsuite_styx_version: 14.7.3  ← NICHT v15.0.0
sensor.popotsuite_core_api_v1: supported ← aber von v14.7.3
```

**Maßnahme:**Addon-Restart erforderlich. Ohne Restart ist v15.0.0 nicht live.

### Lovelace UI Checks (S4, S5)
- **NICHT TESTBAR** — addon läuft noch auf v14.7.3, UI-Elemente von v15.0.0 noch nicht aktiv

---

## OFFENE ITEMS

1. **Andreas oder User mit Browser-Zugang:** S4 + S5 in Lovelace UI manuell prüfen
2. **API Failures Sensor** — existiert nicht unter `sensor.pilotsuite_api_failures` — ggf. unter anderem Namen oder noch nicht implementiert

---

*Smoke-Test durchgeführt: HomeClaw Lane, 2026-03-21 15:10*
