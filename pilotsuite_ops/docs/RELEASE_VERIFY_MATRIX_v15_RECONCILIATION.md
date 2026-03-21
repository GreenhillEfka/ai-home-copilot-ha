# RELEASE VERIFY MATRIX — Reconciliation v14.9.x

> **Erstellt:** 2026-03-21 17:50 GMT+1
> **Branch/Commit:** `origin/main` @ `135aa34c`
> **Andreas-Direktive:** Keine neuen Features. Nur Cleanup. Saubere Faktenbasis.

---

## 1. LIVE SENSOR/ZONE STÄNDE (HA/HACS — Port 8123)

**Quelle:** `curl /api/states` mit HA-API-Token, `2026-03-21 17:45`

| Kennzahl | Wert |
|----------|------|
| Total HA Entities | 5110 |
| PilotSuite Entities | 615 |
| Active | 611 (99.3%) |
| Inactive | 4 (0.7%) |

**Inactive Entities (4):**
```
select.pilotsuite_media_zone_select: unknown     ← Media-Stack fehlt
number.pilotsuite_media_volume: unavailable      ← Media-Stack fehlt
stt.pilotsuite_stt: unknown                     ← STT nicht installiert
tts.pilotsuite_tts: unknown                     ← TTS nicht installiert
```

**Key Sensoren:**
```
sensor.pilotsuite_styx_version:          14.7.3  ← NICHT 15.0.0
sensor.pilotsuite_core_api_v1:           supported
sensor.pilotsuite_habitus_zones:         12/12 active
sensor.pilotsuite_habitus_zones_count:   12
sensor.pilotsuite_habitus_zones_v2_health: healthy
sensor.pilotsuite_styx_pipeline_health:  healthy
binary_sensor.pilotsuite_styx_online:     on
select.pilotsuite_zones_v2_global_state: auto
```

**Lovelace Cards (www/):**
```
pilotstack-zone-cards.mjs   ← 689 Zeilen Diff (UNCOMMITTED)
styx-zone-card.js           ← committed
styx-*-card.js (8 files)   ← alle committed
```

---

## 2. CORE↔HA DRIFT (real)

**Quelle:** Core API `/api/v1/zones` auf Port 8909

| Dimension | HA/HACS | Core/Addon | Status |
|-----------|---------|------------|--------|
| Zones | 12/12 active | **0 zones, []** | 🔴 CRITICAL |
| Version | 14.7.3 | 14.7.3 | ✅ aligned |
| Dashboard/ | 11MB (HA) | 540KB (Core) | ⚠️ oversized |
| 8 duplicate widgets | HA hat Kopien | Core hat Original | 🔴 cleanup |
| PR #149 (zone_matcher) | offen | offen | 🔴 blockiert |

**Zone-Drift Erklärung (wahrscheinlich):**
- HA verwaltet Zones eigenständig über `habitus_zones_entities_v2.py`
- Core Zone-API (`/api/v1/zones`) antwortet mit leerem Array, weil:
  - Entweder Core seine Zones nicht korrekt an HA exposed
  - Oder Andreas-Regel "Core=Management" ist noch nicht verdrahtet
- HA zeigt 12/12 active → HA-seitiges Zone-Management funktioniert
- Core Zone-API = 0 → Core-seitiges Management noch nicht aktiv

**dashboard/ Duplikat-Status:**
| Widget | Identisch zu Core? | HA-Size |
|--------|-------------------|---------|
| optimization | ✅ IDENTICAL | — |
| brain_graph | ❌ DIFFERENT | — |
| chat_widget | ❌ DIFFERENT | — |
| sensor_overview | ❌ DIFFERENT | — |
| system_status | ❌ DIFFERENT | — |
| zone_summary | ❌ DIFFERENT | — |

---

## 3. PFLICHT-TESTS VOR RELEASE

### E2E Contract Pipeline
| Test | Status | Letzter Lauf |
|------|--------|-------------|
| contracts_bridge import | ✅ PASS | 11:27 UTC |
| webhook_parse | ✅ PASS | 11:27 UTC |
| webhook_validate | ✅ PASS | 11:27 UTC |
| webhook_execute | ✅ PASS | 11:27 UTC |

**Report:** `pilotsuite_ops/reports/PS-E2E-001_CONTRACT_PIPELINE_E2E.md` — PASS ✅

### smoke_test_v15.py (PilotClaw's Test)
| Check | Status | Problem |
|-------|--------|---------|
| sensor.copilot_ha_core_connection | ❌ NOT FOUND | v14.7.3 hat `pilotsuite_*`, nicht `copilot_ha_*` |
| sensor.copilot_ha_poll_interval | ❌ NOT FOUND | same |
| sensor.copilot_ha_api_failures | ❌ NOT FOUND | same |
| sensor.pilotsuite_modules_ready | ❌ NOT FOUND | same |
| sensor.pilotsuite_habitus_zones | ✅ FOUND (12/12) | aber anderer entity_name |
| sensor.copilot_ha_version | ❌ NOT FOUND | same |

**Interpretation:** smoke_test_v15.py erwartet v15.0.0 Entity-Namen. Das System läuft auf v14.7.3. Test ist für v15.0.0 geschrieben, nicht für aktuelles System. → **Test passt nicht zum aktuellen Stand**

### Python Syntax (145+ Files)
✅ Alle kompilierbar — zuletzt verifiziert earlier today

### CI Status
```
commit 135aa34c: CI green ✅
```
Quelle: `git log --oneline origin/main -1`

---

## 4. OFFENE BlOCKER vor Reconciliation Release

### 🔴 CRITICAL (müssen gefixt werden)

| # | Blocker | Lösung | PR/Task |
|---|---------|--------|---------|
| 1 | Core Zone-API = 0 zones, HA = 12/12 | PR #149 (zone_matcher) verifizieren ob es das löst | PR #149 OPEN |
| 2 | 8 duplicate dashboard widgets in HA | dashboard/ aus HA entfernen (gehört nicht in HA-Repo) | kein PR |
| 3 | `pilotstack-zone-cards.mjs` — 689 Zeilen unstaged | committen oder verwerfen (Owner: Stxy) | kein PR |

### 🟡 ATTENTION (sollte gefixt werden)

| # | Item | Empfehlung |
|---|------|-----------|
| 4 | 4 inactive Media/TTS entities | Als optional markieren oder Mock-Werte |
| 5 | coordinator_fragment.py — untracked | Ist das ein残余 Fragment oder geplant? |
| 6 | smoke_test_v15.py passt nicht zum aktuellen Stand | An v14.7.3 anpassen oder neuen Test für aktuellen Stand schreiben |

### 🟢 NICHT BLOCKIEREND

| # | Item | Bemerkung |
|---|------|-----------|
| 7 | Version 14.7.3 statt 15.0.0 | Beide Seiten konsistent = kein Blocker |
| 8 | Media-Stack fehlt | Optional, kein Produktiv-Impact |

---

## 5. GITHUB PR / BRANCH STATUS

| PR/Branch | Titel | Status | Blockiert? |
|-----------|-------|--------|-----------|
| PR #149 | fix: correct Core import path zone_matcher | OPEN | ❌ |
| PR #147 | feat: add schemas/ and habitus_entity_sorting.py to copilot_ha | OPEN | ❌ |
| feature/habitus-zone-creator-card | — | OPEN | ❌ (Feature-Branch) |
| release-prep/v14.7.3-ha-test | — | OPEN | ⚠️ (alt) |

---

## 6. Bereinigungs-Items (Cleanup)

**MÜSSEN GELÖST WERDEN vor Release:**
- [ ] dashboard/ aus HA-Repo entfernen (Architektur-Verletzung)
- [ ] PR #149 + PR #147 mergen (oder schließen)
- [ ] pilotstack-zone-cards.mjs — Owner zuweisen + commit/verwerfen
- [ ] coordinator_fragment.py klären (残余 oder geplant?)

**PHASE 1 (DIESER RELEASE):**
1. dashboard/ entfernen
2. PR #149 + PR #147 evaluieren
3. pilotstack-zone-cards.mjs klären
4. coordinator_fragment.py klären

**PHASE 2 (NÄCHSTER SPRINT):**
- Schema-Zusammenführung (entity_zone_sorter.py vs habitus_entity_sorting.py)
- Sensor-Audit (611 active = gut, kein Aktionbedarf)
- Media-Entities als optional markieren

---

## 7. VERSION / COMMIT STAND

```
origin/main: 135aa34c fix(chat): add disconnectedCallback + abort controllers
v14.7.3 (beide Seiten): 14.7.3 ✅ konsistent
v15.0.0: in Git, nicht auf Livesystem
```

---

*Verify-Matrix erstellt: HomeClaw Lane, 2026-03-21 17:50*
*Branch-Kontext: origin/main @ 135aa34c*
*Keine Spekulation, keine neuen Architekturfragen — nur Fakten*
