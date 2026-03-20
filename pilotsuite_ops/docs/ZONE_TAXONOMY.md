# PilotSuite Zone-Taxonomy

## 10 Habitus-Zielzonen

| zone_id | name_de | icon | Zone-Typ |
|---|---|---|---|
| wohnbereich | Wohnbereich | mdi:sofa | living |
| badbereich | Badbereich | mdi:shower | wet |
| kochbereich | Kochbereich | mdi:silverware-fork-knife | wet |
| buerobereich | Bürobereich | mdi:desk | room |
| gangbereich | Gangbereich | mdi:door | transit |
| schlafbereich | Schlafbereich | mdi:bed | room |
| kellerbereich | Kellerbereich | mdi:home-floor-negative-1 | room |
| zimmer_mira | Zimmer Mira | mdi:bed-single-outline | room |
| zimmer_paul | Zimmer Paul | mdi:bed-single-outline | room |
| aussenbereich | Außenbereich | mdi:tree | outdoor |

## Keyword-Mapping

### wohnbereich
Deutsch: wohn, wohnzimmer, esszimmer, ess, gast, living, dining, lounge, loft, entspannung, sofa, fernseher, tv, fernseh, sitzecke

### badbereich
Deutsch: bad, badezimmer, toilette, wc, dusche; Englisch: bath, bathroom, shower

### kochbereich
Deutsch: koch, küche, kueche, speis, vorrat; Englisch: kitchen, pantry

### buerobereich
Deutsch: büro, buero, arbeit, homeoffice; Englisch: office, studio, werkstatt

### gangbereich
Deutsch: gang, flur, diele, eingang, vorraum, vorzimmer; Englisch: hall, corridor, entry, hallway, stairs

### schlafbereich
Deutsch: schlaf, schlafzimmer; Englisch: bedroom

### kellerbereich
Deutsch: keller, speicher; Englisch: basement, cellar

### zimmer_mira
Deutsch: mira, zimmer mira, maras zimmer

### zimmer_paul
Deutsch: paul, zimmer paul, zimmer pauli, pauls zimmer

### aussenbereich
Deutsch: aussen, garten, garage, carport, hof, parkplatz, terrasse, terrass, balkon, loggia, veranda, patio, wintergarten; Englisch: outdoor, garden

## N:1-Aggregationen

| Quell-Area | Ziel | Begründung |
|---|---|---|
| esszimmer, dining | wohnbereich | Funktionale Einheit |
| terrasse, balkon, loggia | aussenbereich | Außenbereich |
| garten, hof, garage | aussenbereich | Außenbereich |

## zone:ungeordnet

| Property | Wert |
|---|---|
| zone_id | zone:ungeordnet |
| name_de | Ungeordnet |
| icon | mdi:help-circle-outline |
| zone_type | undefined |

Alle nicht-mappbaren Areas/Entities landen hier. Keine aktiven Module.

## zone_type Semantik — Core vs. HA (D-01 Drift!)

**Core (ZoneType Enum):** `living`, `kitchen`, `bath`, `bedroom`, `office`, `transit`, `outdoor`
**HA (physische Hierarchie):** `room`, `area`, `outdoor`, `wet`, `transit`

Orthogonal — nicht dasselbe Feld!

## Modul-Per-Zone (Default)

| Zone | Licht | Bewegung | Audio | Klima | Cover | Energie | Szene | Sicherheit |
|---|---|---|---|---|---|---|---|---|
| wohnbereich | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| badbereich | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| kochbereich | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| buerobereich | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| gangbereich | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| schlafbereich | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |
| kellerbereich | ✅(F) | ✅(F) | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| zimmer_mira | ✅ | ✅ | ✅(F) | ✅ | ✅(F) | ❌ | ✅ | ❌ |
| zimmer_paul | ✅ | ✅ | ✅(F) | ✅ | ✅(F) | ❌ | ✅ | ❌ |
| aussenbereich | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| ungeordnet | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

(F) = fehlende Konfiguration in `_ZONE_MODULE_DEFAULTS`

## Offene Fragen

- Sollen zimmer_mira/zimmer_paul als eigene Zonen bestehen?
- kellerbereich — eigene Zone oder ungeordnet?
- D-03-Aggregationen — expliziter Contract oder implizite Heuristik?
- presence-Modul — 7 oder 8 Module? presence als overridable?
