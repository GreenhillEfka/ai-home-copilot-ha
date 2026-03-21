# PilotSuite v15.0 — UX / Explainability / Governance Gate

**Lane:** Stxy / DesignClaw
**Stand:** 2026-03-21 14:45
**Release:** v15.0 (geplant)

---

## 1. UX-Audit — Was funktioniert

| Komponente | Status | Notes |
|---|---|---|
| styx-zone-card.js Hold-Pill (Auto/An/Aus) | ✅ | Presence-Hold funktioniert, CSS vollständig |
| styx-zone-card.js show_presence_hold toggle | ✅ | default true |
| styx-suggestions-card accept/snooze/reject | ✅ | Buttons vorhanden, disabled wenn offline |
| Suggestion confidence Badge (%) | ✅ | _confidenceBadge() zeigt %, farbcodiert |
| Suggestion description | ✅ | s.description wird angezeigt |
| Suggestion category + risk tags | ✅ | Kategorie-Farben + Risiko-Badge |
| Governance off/learning/autonomy | ❓ | Wo in HA sichtbar? |
| Core Connection Status | ❌ | Kein Sensor sichtbar |

---

## 2. UX-Lücken — Must-Fix vor v15.0

### Lücke 1: Suggestions — Kein Pattern/Lift sichtbar (KRITISCH)

**Problem:** Card zeigt confidence % aber nicht das zugrundeliegende Pattern (z.B. "Licht Küche an → Kaffee-Maschine an") und nicht den Lift/Korrelation.

**Daten im Backend (suggestion_panel.py):**
```python
pattern  = "light.kitchen:on → switch.coffee:on"   # ✅ existiert
confidence = 0.89   # ✅ als Badge angezeigt
lift     = 3.2     # ❌ nicht angezeigt
reasoning = "In 47 von 52 Fällen..."  # ❌ kein reasoning_freitext Feld
```

**VISION-Anforderung:**
> "Jede Entscheidung ist nachvollziehbar."
> "Begruendung: In den letzten 7 Tagen haben Sie 47 Mal..."

**Fix-Vorschlag (UX-only):**
```html
<details class="sg-reasoning">
  <summary>Warum dieser Vorschlag?</summary>
  <div class="reasoning-body">
    <span class="pattern">🔗 Licht Küche → Kaffee-Maschine</span>
    <span class="lift">📈 Lift: 3.2× (starke Korrelation)</span>
    <span class="confidence">✓ Confidence: 89%</span>
  </div>
</details>
```

**Aufwand:** ~20 Zeilen JS + CSS. Kein Backend-Call. PilotClaw oder Stxy kann das umsetzen.

---

### Lücke 2: Governance-Modi unsichtbar (KRITISCH)

**Problem:** Das 3-Phasen-Modell (active/learning/off) ist nicht in HA sichtbar. Nutzer kann nicht sehen in welchem Modus das System gerade ist.

**VISION:**
> "Phase 1: BEOBACHTUNG (off) — System beobachtet, keine Aktionen"
> "Phase 2: VORSCHLAEGE (learning) — Nutzer entscheidet"
> "Phase 3: AUTONOMIE (autonomy) — System handelt selbst"

**Aktueller Stand:**
- `sensor.pilotsuite_autonomie_status` existiert ✅
- Aber: Was sind die States? Welcher Modus gerade?

---

### Lücke 3: Core Connection Status fehlt (HOCH)

**Problem:** Andreas kann nicht auf einen Blick sehen ob Core erreichbar ist.

**VISION:**
> "Alles lokal, keine Cloud" — Aber: ist Core überhaupt erreichbar?

**Must-Have:** `sensor.copilot_ha_core_connection` (connected/degraded/disconnected)
→ System_Status_Sensors.py (bereits in Bearbeitung, PR folgt)

---

## 3. Zustandsklarheit — Was muss sichtbar sein

```
Zone Presence:
  Zone XY — Anwesenheit: AUTO / AN / AUS (Hold-Pill) ✅
  Confidence: 89% (Badge) ✅

Suggestions:
  Title: "Kaffee-Maschine um 7:12 einschalten" ✅
  Description: "Morgens wenn Bewegung in der Küche..." ✅
  Confidence: 89% ✅
  Pattern: "Licht Küche → Kaffee-Maschine" ❌ MISSING
  Lift: 3.2× ❌ MISSING
  Reasoning: "In 47 von 52 Fällen..." ❌ MISSING

System:
  Core: verbundet ✅ / degradiert ❌ / getrennt ❌  (fehlt)
  Autonomie: BEOBACHTEN ❌ / LERNEN ❌ / AUTONOM ❌  (unsichtbar)
```

---

## 4. Release-Verify-Matrix v15.0

### Must-Have (Blocker)

| # | Kriterium | Status | Wer |
|---|-----------|--------|-----|
| M1 | CI green (500+ passed) | ✅ | PilotClaw |
| M2 | styx-suggestions-card zeigt Pattern + Lift | ❌ OPEN | PilotClaw/Stxy |
| M3 | Governance-Modus sichtbar in HA | ❌ OPEN | PilotClaw |
| M4 | Core Connection Sensor in HA | ❌ OPEN | PilotClaw |
| M5 | VERSION/Core/HA alle auf v15.0 | ❌ OPEN | PilotClaw |

### Should-Have

| # | Kriterium | Status | Wer |
|---|-----------|--------|-----|
| S1 | Smoke Test auf Live HA | ❌ OPEN | HomeClaw |
| S2 | Presence-Hold E2E Test | ❌ OPEN | HomeClaw |
| S3 | Lovelace Dashboard Darstellung | ❌ OPEN | Stxy |

### Nice-to-Have

| # | Kriterium | Status | Wer |
|---|-----------|--------|-----|
| N1 | Reasoning-Text in Suggestions | ❌ OPEN | PilotClaw |
| N2 | Multi-User Awareness | ❌ OPEN | PilotClaw |

---

## 5. Freigabe-Empfehlung (Stxy Lane)

**v15.0 kann NICHT freigegeben werden bevor:**
1. M2 + M3 + M4 implementiert sind (max 2h Arbeit)
2. Live-Smoke-Test (HomeClaw) erfolgreich war

**Wenn Andreas früher freigeben will:**
→ RC-Chanel: "v15.0-RC1 — NOCH NICHT FÜR PRODUKTION"
→ Nur für Andreas' Entwicklungsumgebung

---

*Stxy / DesignClaw — v15.0 UX Gate — 2026-03-21 14:45*
