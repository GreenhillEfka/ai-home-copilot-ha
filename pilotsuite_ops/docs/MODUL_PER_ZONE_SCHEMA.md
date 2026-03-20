# Modul pro Habitus-Zone Schema

## Überblick

Definiert verbindliche und optionale Module für jede Habitus-Zone.

## Modulmatrix

| Zone | Licht | Musik | Klima | Cover | Energie | Szene | Security |
|------|-------|-------|-------|-------|---------|-------|----------|
| **Wohnbereich** (living) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Schlafbereich** (sleeping) | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Kochbereich** (cooking) | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Badbereich** (bathing) | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Gangbereich** (transit) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Bürobereich** (working) | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Außenbereich** (outdoor) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Kellerbereich** (storage) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Kinderzimmer** (child) | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |

## Modulbeschreibungen

| Modul | Beschreibung |
|---|---|
| light | Lichtsteuerung (Schalter, Dimmer, Farbe) |
| audio | Musik / Multiroom-Audio |
| climate | Heizung / Klima |
| cover | Jalousien / Rollläden |
| energy | Energieverbrauch / Smartmeter |
| scene | Szenen / Automatisierungen |
| security | Kamera / Alarmanlage |

## Validierung

`ZONE_MODULE_SCHEMA` in `habitus_module_schema.py` ist die verbindliche Whitelist. Die `ZoneConfig.allowed_module_types`-Validierung nutzt dieses Schema als Referenz.

## Erweiterung

Neue Zone hinzufügen → Eintrag in `ZONE_MODULE_SCHEMA`, `ZONE_DISPLAY_NAMES` und `MODULE_DESCRIPTIONS`. Tests erweitern.
