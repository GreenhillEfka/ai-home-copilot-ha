# Tasklog Report: PS-084 — Modulschema je Habitus-Zone festziehen

**Datum:** 2026-03-20  
**Agent:** PilotClaw (Subagent)  
**Channel:** telegram  
**Status:** ✅ ABGESCHLOSSEN

---

## 1. Was wurde gemacht

Analyse von `habitus_zones_store_v2.py` im Repo `pilotsuite-styx-ha` (Stand: /config/clawd/team/repos/pilotsuite-styx-ha/).

Drei Kern-Dictionaries identifiziert und dokumentiert:
- `_BASE_MODULE_PRIORITIES` — Priorität je Modul (bei Konflikten)
- `_ZONE_MODULE_DEFAULTS` — Default-Aktivierung je Zone+Modul
- `_ZONE_MODULE_NOTES` — Hinweise/Begründungen je Zone+Modul
- `_ZONE_TYPE_FALLBACK_DEFAULTS` — Fallback wenn Zone nicht in Defaults steht

---

## 2. Modultypen (MODULE_OVERRIDE_IDS)

| # | Modul | Priority | Bemerkung |
|---|-------|----------|-----------|
| 1 | light | 95 | |
| 2 | motion | 100 | Höchste Priorität |
| 3 | music | 72 | |
| 4 | volume | 68 | |
| 5 | tv | 62 | |
| 6 | climate | 80 | |
| 7 | camera | 58 | Niedrigste Priorität |

> ⚠️ **Diskrepanz:** Der Task spricht von "8 Modultypen", definiert sind aber **7**. Fehlendes Modul ist unbekannt — ggf. müsste `presence` oder `sensor` als 8. ergänzt werden.

---

## 3. Vollständige Tabelle: 10 Habitus-Zonen × 7 Module

Legende: ✅ = enabled, ❌ = disabled (default), *(s)* = suggestion-first

| Zone | light | motion | music | volume | tv | climate | camera |
|------|-------|--------|-------|--------|----|---------|--------|
| **wohnbereich** | ✅ | ✅ | ✅ | ✅ | *(s)* | ✅ | ❌ |
| **badbereich** | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **kochbereich** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **buerobereich** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **gangbereich** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **schlafbereich** | ✅ | ✅ | ✅ | ✅ | *(s)* | ✅ | ❌ |
| **kinderzimmer** | ✅ | ✅ | ✅ | ✅ | *(s)* | ✅ | ❌ |
| **terrassenbereich** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | *(s)* |
| **aussenbereich** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | *(s)* |
| **Fallback (room/area)** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Fallback (floor)** | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Fallback (outdoor)** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 4. Analyse: Unterschiede zwischen Zonen

### Module-Reichtum (6 von 7 aktiv):
- **wohnbereich** — fullest set, inkl. tv (suggestion-first)

### Mittlere Ausstattung (5 aktiv):
- **kochbereich, buerobereich, schlafbereich, kinderzimmer, terrassenbereich** — kein tv, terrassenbereich/terrasse auch kein climate

### Schlanke Ausstattung (3–4 aktiv):
- **gangbereich** — nur light, motion, camera (kein music/volume/climate)
- **aussenbereich** — nur light, motion, camera (kein music/volume/climate)
- **badbereich** — light, motion, climate (minimal, kein music/volume/tv/camera)

---

## 5. Fehlende Konfigurationen

### 5.1 Zone `kinderzimmer` — fehlende camera-Config
`_ZONE_MODULE_NOTES` enthält keinen Eintrag für `kinderzimmer → camera`. Es greift der Default-Hinweis:
> *"Disabled by default for this zone; explicitly enable if you want suggestions here."*

Das ist konsistent, aber eine bewusste Dokumentation in `_ZONE_MODULE_NOTES` fehlt.

### 5.2 Zone `gangbereich` — keine Musik/TV-Notes
Kein expliziter Note-Eintrag für `gangbereich → music/volume/tv`. Greift der Default-Hinweis.

### 5.3 Zone `aussenbereich` — music-Note
`_ZONE_MODULE_NOTES["aussenbereich"]["music"]` sagt:
> *"Outside audio stays disabled by default unless explicitly enabled."*

Korrekt dokumentiert.

### 5.4 Fehlende Zone: kein expliziter Eintrag für?
Folgende Zonen haben **keinen** Eintrag in `_ZONE_MODULE_DEFAULTS`:
- `flur` / `eingang` / `haustuer` (falls separate Zone)
- `keller` / `dachboden` / `garage`
- `gaestezimmer`

→ Diese Zonen fallen auf den jeweiligen `_ZONE_TYPE_FALLBACK_DEFAULTS` zurück.

### 5.5 Unklarheit: "8 Module" vs. 7 definierte MODULE_OVERRIDE_IDS
Es gibt keine 8. Modul-Definition. Entweder:
- `presence` als 8. Modul ist geplant aber nicht implementiert, oder
- die Zahl 8 im Task war ein Schätzwert.

---

## 6. Empfehlungen

| # | Aktion | Priorität |
|---|--------|-----------|
| R1 | `_ZONE_MODULE_NOTES["kinderzimmer"]["camera"]` explizit dokumentieren | MEDIUM |
| R2 | Klarstellung ob `presence` das fehlende 8. Modul sein soll → MODULE_OVERRIDE_IDS ergänzen | HIGH |
| R3 | `gangbereich`-Notes für music/volume ergänzen (Dokumentationslücke) | LOW |
| R4 | Alle Zonen ohne expliziten Eintrag in `_ZONE_MODULE_DEFAULTS` review: flur, keller, garage, gaestezimmer | MEDIUM |

---

## 7. Modul-Default-Logik (Zusammenfassung)

```
Zone in _ZONE_MODULE_DEFAULTS?
  → JA: diese Menge nutzen
  → NEIN: _ZONE_TYPE_FALLBACK_DEFAULTS[zone_type] nutzen
     → auch nicht vorhanden: leere Menge {}
```

Alle Module werden dann durch `default_module_overrides_for_zone()` genormt:
- `suggestion_mode = "explainable_manual"` (global default)
- `direct_execution_enabled = False` (alle zones!)
- `approval_required = True`
- `explanation_required = True`
- `autonomy_mode = "learning"`

**Direkte Ausführung ist systemweit deaktiviert** — alle Zonen sind suggestion-first mit Approval-Pflicht.

---

## 8. Nächste Schritte (für Haupt-Agent)

1. Klären: Ist `presence` das fehlende 8. Modul?
2. `_ZONE_MODULE_NOTES` für `kinderzimmer → camera` ergänzen
3. Review aller Zonen ausserhalb der 9 bekannten
4. Task PS-085/PS-086: Coordination mit module-schemas in dashboard/frontend prüfen
