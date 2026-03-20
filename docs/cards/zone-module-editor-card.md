# Zone Module Editor Card

## Zweck
`zone-module-editor` dient zur Konfiguration eines einzelnen Moduls innerhalb einer Zone. Die Karte legt fest, zu welchem **Module-Typ** die Zone gehört und welche passende Zone-/Filter-Entity dafür verwendet wird.

## Konfigurationsfelder

| Feld | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `zone_id` | string | ✅ | – (z. B. `zone_living`) | Zone-ID aus dem Core/Zone-Store |
| `zone_name` | string | ❌ | – | Optionaler Anzeigename der Zone |
| `module_type` | `LIGHT` `AUDIO` `CLIMATE` `COVER` `ENERGY` `SCENE` `SECURITY` | ✅ | `LIGHT` | Aktivierter Modultyp |
| `light_entity` | entity (`light`) | ❌ | – | Licht-Entity für diesen Zone-Modultyp |
| `audio_entity` | entity (`media_player`, device_class `speaker`) | ❌ | – | Audio-/Media-Player-Entity |
| `climate_entity` | entity (`climate`) | ❌ | – | Klima-Entity |
| `cover_entity` | entity (`cover`) | ❌ | – | Cover-/Rolladen-Entity |
| `energy_entity` | entity (`sensor`, device_class `power`/`energy`) | ❌ | – | Energie-/Stromsensor |
| `scene_entity` | entity (`scene`) | ❌ | – | Szene-Entity |
| `security_entity` | entity (`alarm_control_panel`,`binary_sensor`,`sensor`; device_class `motion`/`opening`/`smoke`/`gas`) | ❌ | – | Sicherheits-/Sensor-Entity |
| `light_filter_entity` | entity (`input_boolean`,`binary_sensor`) | ❌ | – | Optionaler Filter für Lichtauswahl |
| `climate_filter_entity` | entity (`input_boolean`,`binary_sensor`,`sensor`) | ❌ | – | Optionaler Filter für Klima-Auswahl |
| `cover_filter_entity` | entity (`input_boolean`,`binary_sensor`) | ❌ | – | Optionaler Filter für Cover-Auswahl |
| `show_grid` | boolean | ❌ | true | Formular/Grid anzeigen |
| `compact_mode` | boolean | ❌ | false | Kompakter Editor-Style |

## Minimalbeispiel

```yaml
type: zone-module-editor
zone_id: zone_living
zone_name: Wohnzimmer
module_type: LIGHT
light_entity: light.wohnzimmer_deckenlicht
light_filter_entity: input_boolean.allow_zone_lights
show_grid: true
compact_mode: false
```

## Bekannte Grenzen

- Die Karte validiert derzeit nur den `module_type`; es gibt **keine** harte Durchsetzung, dass die zugehörige Entity-Feldgruppe wirklich gesetzt ist.
- Andere Modulfelder bleiben optional, solange der Typ nicht gesetzt ist oder kein passendes Entity-Feld befüllt wurde.
- `module_type` ist fest auf die 7 Werte `LIGHT`, `AUDIO`, `CLIMATE`, `COVER`, `ENERGY`, `SCENE`, `SECURITY` limitiert (Großbuchstaben).
- `zone_id` muss bereits existieren; es findet kein automatisches Anlegen oder Normalisieren statt.
