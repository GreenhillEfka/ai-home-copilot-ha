# Frontend Zone Chain — Analyse & Konsolidierung

**Stand:** 2026-03-21 23:50
**Lane:** Vision/UX/Frontend/Habitus-Zonen-Darstellung

---

## Live-System-Stand (VERIFIZIERT via API)

| System | Version | Status |
|--------|---------|--------|
| HA/HACS (git) | v15.0.3 | ✅ code deployed |
| HA live sensor | `sensor.copilot_ha_habitus_zones` state=None | ⚠️ Integration nicht reloaded |
| Core live | v14.7.3 | ⚠️ addon restart ausstehend |
| Core dashboard | 12 zones, alle `zone_name=""` | ❌ name_de sync bug |

---

## Zone Flow — Wo was passiert

```
[HA Areas]
    ↓ (area_id, name, icon)
[HabitusZoneV2] ← zone_auto_setup.py Templates
    ↓ z.name (= HA are name, correct)
[sensor.copilot_ha_habitus_zones] ← HA Sensor mit zone.name
    ↓ Lovelace Card liest
[styx-zone-card.js] ← zone.name → angezeigt als zoneName
    ↓
[Core /dashboard] ← zone_name aus Core
```

**Kritischer Pfad:**
1. HA Area → `HabitusZoneV2.name` ✅ (lokal korrekt)
2. HA Sensor → `state.attributes.zones[].name` ✅ (HA Seite korrekt)
3. **Core sync**: `"name_de": z.name` → Core interpretiert falsch → `zone_name=""`
4. **Lovelace**: liest HA sensor (lokal) nicht Core → sollte ✅ anzeigen

---

## Zone Card JS — Korrekte Lese-Syntax

```javascript
// styx-zone-card.js — Zone name aus HA sensor
const zoneName = zone.name || zoneId;
// ← Das ist korrekt! HA sensor hat zone.name aus HabitusZoneV2

// Die Zone Card zeigt was in HA sensor.attributes.zones[] steht
// NICHT das Core /dashboard
```

---

## Sync-Problem (BEHOBEN, noch nicht live)

| Datei | Problem | Fix | Status |
|-------|---------|-----|--------|
| `coordinator.py` | sendet `"name": z.name` | → `"name_de": z.name` | PR #162 ✅ |
| `styx-zone-card.js` | liest `sensor.pilotsuite_habitus_zones` | → `sensor.copilot_ha_habitus_zones` | PR #163 ✅ |

---

## Zone Matching — Wo?

** falsch:** `entity_zone_sorter.py`, `habitus_entity_sorting.py` in HA — **keine prod refs**
**korrekt:** `zone_matcher.py` in **Core** (brain/)

```
HA: sensor.copilot_ha_habitus_zones → Zones mit entity_ids
    ↓ (entity_ids)
Core: zone_matcher.py → ordnet entity_ids → zones zu
```

---

## UX-Kette Habitus-Zonen (Ziel-Zustand)

```
User öffnet Lovelace
    ↓
styx-zone-card.js → sensor.copilot_ha_habitus_zones
    ↓
Zeigt pro Zone:
  - zone_name (aus HA sensor, local correct)
  - presence state (auto/force_on/force_off) ← Hold-Pill
  - mood indicator
  - module states
  - health score
    ↓
Bei Hold-Pill Klick:
  → socket.emit('presence_hold', {zone_id, hold})
  → coordinator.py → Core API POST /presence/zone/presence/{id}/hold
  → Core bestätigt → socket.once('presence_hold_result')
  → UI updated (optimistic + server confirm)
```

---

## Modul-Konfiguration — Ziel-Zustand

```
Core Modul-Schemas (/api/v1/zone-automation/module-schemas)
  ↓ (39 fields across 7 modules)
HA Config Flow Step "Module" → zeigt alle Module mit override-Feldern
  ↓
Bei Zone-Erstellung: Template-basiert + manuelle Overrides
  → /api/v1/zone-automation/zones/{id}/modules/{id} POST
```

---

## Offene UX-Probleme (zu lösen)

| # | Problem | Impact | Owner |
|---|---------|--------|-------|
| 1 | HA Integration reloaden → `_first_zone_sync()` muss laufen | zones in Core | Andreas |
| 2 | Core addon restart → v14.7.3 → v15.0.3 | Alle zone-automation features | Andreas |
| 3 | Lovelace Zone Card: sensor name noch nicht gefixt | Card zeigt nichts | Andreas (nach reload) |
| 4 | Module Config UI: kein dedicated Config-Flow Step | Kein Override pro Zone | UX Lane |
| 5 | Zone Creator Card (TS): ungenutzt, 1342 lines | Technische Schuld | UX Lane |

---

## Sofort-Aufgaben UX Lane

1. ** Lovelace Zone Card**: Nach Integration-Reload prüfen ob zones angezeigt
2. **Hold-Pill UX testen**: presence_hold socket flow komplett durchtesten
3. **Module Config Flow**: Bestehende Config-Flow Steps analysieren → Lücke für Module-Override identifizieren
4. **Zone Editor Doc**: Veraltete Zone-Editor-Doku (Phase 6) → mit aktueller Zone-Automation API abgleichen

---

## Veraltete Dokumente (Markieren/Archivieren)

| Datei | Problem |
|-------|---------|
| `docs/ZONE_EDITOR.md` (worktree) | Veraltet — Zone Automation API hat `/zone-automation/` nicht `/habitus/zones/` |
| `habitus_entity_sorting.py` | Orphan — keine prod refs, 337 lines |
| `entity_zone_sorter.py` | Stale — keine prod refs, 184 lines |
| `dashboard/static/cards/*.ts` | Ungenutzte TS Cards, 1342 lines |
| `pilotstack-zone-cards.mjs` | Wird gebaut aber nie referenziert |

---

*Erstellt: 2026-03-21 | Lane: Vision/UX/Frontend*
