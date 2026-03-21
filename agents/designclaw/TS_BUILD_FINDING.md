# TS BUILD FINDING — CRITICAL RECONCILIATION ITEM
**Date:** 2026-03-21
**Status:** ADDENDUM TO UX_LANE_CONVERGENCE.md

---

## FINDING: pilotstack-zone-cards.mjs ist ein ARCHIVE, kein aktiver Build

### Was existiert

```
dashboard/static/cards/
├── index.ts                    ← Exportiert 3 Card-Typen
├── styx-zone-creator-card.ts   ← 561 lines, PS-199
├── habitus-brain-card.ts       ← 446 lines, PS-200
└── zone-module-editor-card.ts  ← 335 lines, PS-198

Build: dashboard/build.mjs
Output: custom_components/copilot_ha/www/pilotstack-zone-cards.mjs (52698 bytes, Mar 21 14:43)
```

### Registriert aber ungenutzt

- `card_assets.py:23` → `"pilotstack-zone-cards.mjs": "www/pilotstack-zone-cards.mjs"`
- `lovelace_resources.py:37` → `# TS zone cards bundle (PS-198/199/200)`
- **Aber:** 0 Referenzen in Lovelace YAML, 0 Imports in Python, 0 Usage anywhere

### Die 3 Card-Typen

| Card | PS | Zeilen | Lovelace Usage |
|------|----|--------|----------------|
| `StyxZoneCreatorCard` | PS-199 | 561 | **0** ❌ |
| `HabitusBrainCard` | PS-200 | 446 | **0** ❌ |
| `ZoneModuleEditorCard` | PS-198 | 335 | **0** ❌ |

### Architecture-Verstoß

Die Zone Creator Cards sind **unvollendete Features** die als Build+B und Registry ausgeliefert werden, aber in keiner Lovelace Config existieren. Das verletzt das "keine toten Artefakte" Prinzip.

### Decision: Was tun?

**Option A:** Alles belassen wie es ist (Status Quo)
- Pro: Build funktioniert, Cards könnten eines Tages aktiviert werden
- Con: Verwirrung, tote Features im Build

**Option B:** Build + TS-Source entfernen, Bundle in `www/` behalten aber ohne Build-System
- Pro: Weniger Verwirrung, Bundle bleibt nutzbar
- Con: Bundle wird nie aktualisiert wenn TS-Source wegfällt

**Option C:** Alles entfernen bis Zone Creator Feature fertig ist (RECOMMENDED)
- Bundle + TS-Source + Build-System komplett entfernen
- PS-198/199/200 als Feature-Branch wenn nötig
- Pro: Sauber, keine toten Features im Build
- Con: Muss bei Fertigstellung neu gebaut werden

---

## RECOMMENDATION

**Option C** — alle 3 TS Cards + Build-System gehören in den Reconciliation-Schnitt entfernt, nicht in den nächsten Release:

```
ENTFERNEN:
- dashboard/static/cards/          (TS Card Sources)
- dashboard/build.mjs              (Build Script)
- package.json (falls nur für build)
- card_assets.py: "pilotstack-zone-cards.mjs" registry
- lovelace_resources.py: pilotstack-zone-cards.mjs comment
```

**BEHALTEN:**
- Die 10 JS Lovelace Cards in `www/` (alle aktiv)
- `zone_card_yaml.md` (Dokumentation)

---

*Stxy — UX Lane — 2026-03-21 17:55*
