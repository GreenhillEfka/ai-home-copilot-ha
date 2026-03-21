# SLICE 5 REVIEW — Modulkonfiguration + Andreas-Klärung
**Lane:** Design/UX (Stxy)
**Date:** 2026-03-21 19:10
**Based on:** Andreas Direktive, PilotClaw Frage, Code Deep-Dive

---

## Architecture: Was existiert bereits

### Modulkonfiguration Surface (HA) — Schema-Driven ✅

`zone_automation_entities.py` nutzt **Schema-Driven Entity Generation**:

```
Core /module-schemas Endpoint
    ↓ liefert Schema pro Modul (climate, cover, energy, scene, security)
    ↓
HA: create_zone_automation_entities()
    ↓
Dynamische Entities pro Zone:
    - _ZoneModuleSwitch (für bool-Felder)
    - _ZoneModuleNumber (für int/float-Felder)
    ↓
HA Lovelace: Slider, Switches, Selects
```

### Bereits existierende Module-Entities

| Modul | HA Surface | Config-Felder |
|-------|-----------|---------------|
| Licht | ✅ ZoneLightAutoSwitch | brightness, delays |
| Musik | ✅ ZoneMusicAutoSwitch, Volume, Follow | auto, volume, follow |
| Anwesenheit | ✅ ZonePresenceDelayNumber | delays |
| Helligkeit | ✅ ZoneBrightnessTargetNumber | target, dampening |
| Klima | ⚠️ Schema-Driven (dynamic) | per preset |
| Cover | ⚠️ Schema-Driven (dynamic) | open/close |
| Energie | ⚠️ ZoneEnergyDevice (separate) | discovery |
| Szenen | ⚠️ Schema-Driven (dynamic) | presets |
| Sicherheit | ⚠️ Schema-Driven (dynamic) | sensors |

### Zone Automation Mode Select
`ZoneAutomationModeSelect` — 3 Zustände:
- **Aus** (off) — Automation deaktiviert
- **Lernend** (learning) — lernt Verhalten
- **Autonomie** (autonomy) — automatisierte Steuerung

---

## Das fehlt laut Andreas' Anforderung

### A) Module MÜSSEN für jede HabitusZone konfigurierbar sein

**Aktuell:** Module-Schemas kommen von Core → werden als dynamische Entities erstellt.
**Problem:** Wenn `/module-schemas` nicht funktioniert → keine Module-Entities.

**UX-Oberfläche für Module pro Zone:**
- Liste aller 10 Zonen
- Pro Zone: Licht, Musik, Klima, Cover, Energie, Szene, Sicherheit
- Wichtigste Settings: An/Aus, brightness, volume, delay
- Visualization in Lovelace

### B) Wichtigste Einstellungen VISUALISIEREN

**Was der User sehen soll:**
```
Wohnbereich
├── 🌙 Anwesenheit:  [Delay: 5min]  [Mode: Autonomie]
├── 💡 Licht:         [Auto: ON]     [Brightness: 80%]
├── 🎵 Musik:         [Auto: ON]     [Volume: 40%]    [Follow: ON]
├── 🌡️ Klima:         [Preset: Komfort] [21°C]
├── 🪟 Cover:        [Auto: ON]     [Position: 80%]
└── ⚡ Energie:       [Monitoring]
```

**Current Status:**
- `ZoneAutomationModeSelect` → zeigt Mode ✅
- Light/Music Switches → zeigen Auto on/off ✅
- Number Entities → zeigen brightness, delays ✅
- **Aber:** Kein zusammenhängendes UI pro Zone

---

## FREIGABE / BLOCKADE

| Item | Status | Bemerkung |
|------|--------|-----------|
| Schema-Driven Entity Generation | ✅ Funktioniert |Wenn `/module-schemas` funktioniert |
| ZoneAutomationModeSelect | ✅ OK | |
| Zone Module Switches | ✅ OK | |
| Zone Module Numbers | ✅ OK | |
| Lovelace Zone Card UI | ⚠️ Unvollständig | Kein zusammenhängendes UI pro Zone |
| 0 zones in Core | 🔴 BLOCKIERT | sync-definitions fehlt |

---

## UX DESIGN VORSCHLAG: Zone Module Dashboard

**Für v14.9.1 oder v14.10:**

```
Zone Detail Card (Lovelace)
├── Zone Name + Mode Badge (Autonomie/Lernend/Aus)
├── Licht Module:    [Switch] [Slider: Brightness] [Slider: Delay]
├── Musik Module:    [Switch] [Slider: Volume] [Switch: Follow]
├── Klima Module:    [Select: Preset] [Sensor: Current Temp]
├── Cover Module:    [Switch] [Slider: Position]
└── Presence Module: [Slider: Delay]
```

**Das kann mit bestehenden Entities gebaut werden** — kein neues Backend nötig.

---

## NÄCHSTER SCHRITT

1. **PilotClaw:** `/module-schemas` Endpoint in Core → funktioniert er?
2. **HomeClaw:** Area→Zone Verify → zeigt `/module-schemas` Daten?
3. **Stxy:** Zone Lovelace Card UX → Design für Zone Module Dashboard

---

*Stxy — UX Lane — 2026-03-21 19:10*
