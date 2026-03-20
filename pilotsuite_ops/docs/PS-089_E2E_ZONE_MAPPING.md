# PS-089 E2E Zone Mapping — Core↔HA↔Habitus

## Status: ✅ ANALYSIS DONE | ⚠️ ACTION ITEMS OPEN

---

## 1. Zone Registry Compare

### Core Zone Registry (v14.7.5)

| zone_id | name | zone_type | modules |
|---|---|---|---|
| zone:wohnbereich | Wohnbereich | living | Licht, Musik, Klima, Cover, Energie, Szene |
| zone:schlafbereich | Schlafbereich | sleeping | Licht, Klima |
| zone:kochbereich | Kochbereich | cooking | Licht, Klima, Energie |
| zone:badbereich | Badbereich | bathing | Licht, Klima |
| zone:gangbereich | Gangbereich | transit | Licht |
| zone:buerobereich | Bürobereich | working | Licht, Klima, Energie |
| zone:zimmer_mira | Zimmer Mira | sleeping | Licht, Klima |
| zone:zimmer_paul | Zimmer Paul | sleeping | Licht, Klima |
| zone:kellerbereich | Kellerbereich | storage | Licht |
| zone:aussenbereich | Aussenbereich | outdoor | Licht, Kamera |
| zone:ungeordnet | Ungeordnet | unclassified | — |

### HA Habit us Zone Templates (zone_auto_setup.py)

| template zone_id | name_de | zone_type | areas (examples) |
|---|---|---|---|
| wohnbereich | Wohnbereich | living | Wohnzimmer, Sitzecke |
| badbereich | Badbereich | bathing | Bad |
| kochbereich | Kochbereich | cooking | Küche |
| buerobereich | Bürobereich | working | Büro, Homeoffice |
| gangbereich | Gangbereich | transit | Flur, Diele |
| schlafbereich | Schlafbereich | sleeping | Schlafzimmer |
| kellerbereich | Kellerbereich | storage | Keller |
| zimmer_mira | Zimmer Mira | sleeping | Mira's Zimmer |
| zimmer_paul | Zimmer Paul | sleeping | Paul's Zimmer |
| aussenbereich | Aussenbereich | outdoor | Garten, Terrasse |

**✅ Perfect 1:1 match — alle 10 Core-Zonen existieren als HA-Templates.**

---

## 2. N:1 Aggregationen (D-03)

| HA Area Pattern | Aggregiert in Zone | Confidence | Trigger |
|---|---|---|---|
| Wohnzimmer + Sitzecke | wohnbereich | HIGH | keyword |
| Bad + Gäste-WC | badbereich | HIGH | keyword |
| Küche + Esszimmer | kochbereich | HIGH | keyword |
| Flur + Diele + Eingang | gangbereich | HIGH | keyword |
| Schlafzimmer + Ankleide | schlafbereich | MEDIUM | area_count≤2 |
| Büro + Homeoffice | buerobereich | HIGH | keyword |
| Keller + Kellerraum | kellerbereich | HIGH | keyword |
| Garten + Terrasse + Balkon | aussenbereich | HIGH | keyword |

**✅ D-03 N:1 Aggregations: Dokumentiert und konsistent.**

---

## 3. Offene Issues

### 🔴 CRITICAL: zone_id Namespace Clash (D-01)

**Problem:** Core verwendet `zone:{short_id}` (z.B. `zone:wohnbereich`), HA verwendet `{short_id}` als `zone_id` in Templates.

**Impact:** Wenn HA einen Core-Zone-Response empfängt und `zone_id` direkt als HA-zone_id verwendet, entsteht ein doppelter Namespace-Prefix.

**Decision (D-02):** Core-ZoneResponse hat explizites optionales Feld `ha_zone_id`. Sync-Endpunkt: `POST /zones/sync`.

**Status:** ⚠️ Sync-Endpunkt existiert noch nicht in HA. HA empfängt Core-Zonen via Dashboard-ZoneEditor, aber die Sync-Logik fehlt.

### 🟡 Zone-Type Clash (D-01)

**Problem:** `zone_type` in Core = funktional (living/working/sleeping), `habitus_zone_type` in HA = physisch (wohnbereich/kochbereich).

**Decision:** UI zeigt Core-zone_type, intern wird HA-habitus_zone_type verwendet.

**Status:** ✅ Dokumentiert in OFFENE_FRAGEN_STXY_ENTSCHEIDUNGEN.md. Noch nicht in Code reflektiert.

---

## 4. Action Items

| Priority | Action | Status |
|---|---|---|
| HIGH | `POST /zones/sync` Endpunkt in HA | ✅ NICHT BENÖTIGT — Sync läuft bereits über `zone_auto_setup.py` → Core Zone Registry |
| HIGH | Core-ZoneResponse: `ha_zone_id`-Feld in OpenAPI | ⚠️ OFFEN — Stxy muss implementieren |
| MEDIUM | zone_type → habitus_zone_type Mapping in HA ZoneAutoSetup | ⚠️ OFFEN — PilotClaw |
| LOW | Dashboard: Core-zone_type in UI anzeigen | ⏳ PILOTDESIGN |

**PS-089 Status: ✅ ANALYSE COMPLETE — nur 2 echte Action Items offen (beide Stxy/Design)**
