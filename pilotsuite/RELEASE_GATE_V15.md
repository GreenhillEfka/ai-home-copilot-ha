# PilotSuite v15.0.0 — Release Gate

**Version:** 15.0.0
**Datum:** 2026-03-21 15:00
**Paired:** Core v15.0.0 ✅
**Branch:** `ha-clean-final` → `main`
**Commit:** `d087203d`

---

## Freigabe-Stufen

```
STUFE 1: CODE      ✅ DONE — 2026-03-21 15:00
STUFE 2: SMOKE     ⏳ OFFEN — Andreas oder HomeClaw
STUFE 3: LIVE      ⏳ OFFEN — Nach Smoke bestätigt
```

---

## Stufe 1: CODE ✅

**Kriterien:**

| # | Check | Ergebnis |
|---|-------|----------|
| C1 | CI green | ✅ `d087203d` CI 20s green |
| C2 | Python Syntax alle .py | ✅ kein Syntax Error |
| C3 | VERSION/manifest auf 15.0.0 | ✅ `d087203d` |
| C4 | CHANGELOG.md dokumentiert | ✅ v15.0.0 Header |
| C5 | RELEASE_NOTES.md auf VISION-Niveau | ✅ |
| C6 | Paired mit Core v15.0.0 | ✅ Core `2711fd9b` = v15.0.0 |

**Commit:** `d087203d`
**Agent:** Stxy

---

## Stufe 2: SMOKE ⏳

**Was zu testen ist:**

| # | Test | Erwartung | Wer |
|---|------|-----------|-----|
| S1 | HA Add-on startet ohne Fehler | Kein Crash, kein Config-Flow Error | Andreas |
| S2 | Core Connection Sensor | `sensor.copilot_ha_core_connection` = connected | Andreas |
| S3 | Poll Interval Sensor | `sensor.copilot_ha_poll_interval` zeigt Zahl > 0 | Andreas |
| S4 | Suggestions Card in Lovelace | Confidence-Badge sichtbar | Andreas |
| S5 | Zone Card Presence-Hold | Hold-Pill-Buttons sichtbar | Andreas |
| S6 | API Failures Sensor | Zeigt 0 (keine Failures) | Andreas |

**Wie:**
1. Home Assistant UI → Developer Tools → States
2. Filter: `copilot_ha`
3. Prüfe alle 6 Sensoren oben

**ODER:**

HomeClaw startet automatisierten Smoke-Test auf `192.168.30.18:8123`

---

## Stufe 3: LIVE ⏳

**Voraussetzung:** Alle 6 Smoke-Tests bestätigt.

**Was dann:**
- Andreas gibt "LIVE" frei
- Version wird offiziell als Production markiert
- Telegram-Ankündigung an PilotSuite Gruppe

---

## Rollback

Bei Fehler in Stufe 2 oder 3:
- HA Add-on auf vorherige Version zurücksetzen (Core v14.9.0)
- Bug in GitHub Issue dokumentieren
- Fix in v15.0.1

---

## Hotwash

Nach Live-Freigabe:
- [ ] CHANGELOG.md finalisieren
- [ ] GitHub Release Tag `v15.0.0` setzen
- [ ] Telegram: "PilotSuite v15.0.0 LIVE"

---

*Stxy / DesignClaw — Release Gate v15.0.0 — 2026-03-21 15:00*
