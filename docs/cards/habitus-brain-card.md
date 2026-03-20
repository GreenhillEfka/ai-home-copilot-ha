# Habitus Brain Card

## Zweck
`habitus-brain` zeigt im Dashboard eine **Brain-View**: Zone-Aggregate, Modulstatus, Moods und Live-Metadaten in einem Blick.

## Konfigurationsfelder

| Feld | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `title` | string | ✅ | `Brain View` | Kartenüberschrift |
| `subtitle` | string | ❌ | – | Optionaler Untertitel |
| `show_zone_aggregation` | boolean | ❌ | `true` | Aggregierte Zone-Zustände anzeigen |
| `zones` | string | ❌ | – | Zone-Filter (z. B. kommagetrennt) |
| `aggregation_window` | `5s`, `30s`, `5m` | ❌ | `30s` | Aggregationsfenster für Updates |
| `show_stale_indicator` | boolean | ❌ | `true` | Warnung bei veralteten Daten anzeigen |
| `stale_threshold_seconds` | number | ❌ | `60` | Altersschwelle für „stale“-Status |
| `show_module_status` | boolean | ❌ | `true` | Modul-Chips anzeigen |
| `monitored_modules` | string[] | ❌ | `['light','climate','music','security']` | Überwachte Modulgruppen |
| `show_module_health` | boolean | ❌ | `true` | Modul-Health/Consistency anzeigen |
| `show_module_confidence` | boolean | ❌ | `true` | Konfidenz je Modul anzeigen |
| `enable_mood_panel` | boolean | ❌ | `true` | Mood-Panel aktivieren |
| `mood_panel_position` | `top`, `bottom`, `sidebar` | ❌ | `top` | Position des Mood-Panels |
| `show_mood_valence` | boolean | ❌ | `true` | Valenz-Anzeige |
| `show_mood_activation` | boolean | ❌ | `true` | Aktivierungslevel anzeigen |
| `show_mood_stability` | boolean | ❌ | `true` | Stabilität anzeigen |
| `show_mood_history` | boolean | ❌ | `true` | Historie anzeigen |
| `show_mood_factors` | boolean | ❌ | `true` | Haupttreiber der Stimmung anzeigen |
| `mood_history_hours` | number | ❌ | `24` | Historie-Intervall in Stunden |
| `view_mode` | `live`, `trend`, `drift` | ❌ | `live` | Darstellungsmodus |
| `show_predictions` | boolean | ❌ | `false` | Vorhersage-Overlays anzeigen |
| `show_causal_breadcrumbs` | boolean | ❌ | `true` | Kausalketten anzeigen |
| `incident_lens_mode` | boolean | ❌ | `false` | Fokusmodus bei Incidents |
| `show_data_freshness` | boolean | ❌ | `true` | Datenfrische anzeigen |
| `show_uncertainty_fog` | boolean | ❌ | `true` | Unsicherheitsvisualisierung |
| `batch_updates` | boolean | ❌ | `true` | Stapelweise UI-Updates |
| `show_zone_match` | boolean | ❌ | `false` | Heat-Layer für Zone-Matching |
| `compact_mode` | boolean | ❌ | `false` | Kompakter Modus |
| `show_actions` | boolean | ❌ | `true` | Quick-Action-Buttons anzeigen |

## Minimalbeispiel

```yaml
type: habitus-brain
title: Brain View
show_zone_aggregation: true
show_module_status: true
enable_mood_panel: true
aggregation_window: 30s
view_mode: live
```

## Bekannte Grenzen

- Wertebereiche sind teilweise nicht hart validiert; falsche Strings werden je nach UI-Pfad nicht automatisch korrigiert.
- `stale_threshold_seconds` und `mood_history_hours` sind in der Form-UI als Textfelder dargestellt (statt eigentlicher Zahlenpicker).
- Ohne passende Zone-/Metrikdaten bleiben Abschnitte ggf. leer.
- `monitored_modules` ist als Liste konfiguriert; bei direkter Form-Bearbeitung auf string-basierte Eingaben achten.
