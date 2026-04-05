# Changelog

## [15.4.0] - 2026-04-05

### Added
- Projection-Contract-Testsuite: 25 Testdateien, ~291 parametrized Cases.
- 44 Sensoren als Pure Projection-Shells auf Core-API verifiziert.
- 3 Sensoren als Coordinator-basierte Integration getestet.

### Sensors verified as pure Projection-Shells
habitus_zone, mood, autonomy, brain_activity, hub_dashboard, presence_intelligence,
system_integration, notification_intelligence, agent_status, scene_intelligence,
battery_optimizer, comfort_index, regional_context, tariff, energy_advisor,
light_intelligence, weather_optimizer, media_follow, energy_cost, energy_forecast,
energy_insights, zone_mode, demand_response, notification, proactive_alert,
weather_warning, anomaly_alert, fuel, gas_meter, heat_pump, ev_charging,
energy_sankey, energy_schedule, energy_report, area_presence (Core-sync),
appliance_fingerprint, automation_suggestion, automation_template, cross_dependency,
predictive_maintenance, brain_architecture, onboarding, anomaly_detection,
activity_sensors, zone_presence_trigger

### Fixed
- MRO-Konflikt in module_integration.py (CoordinatorEntity + SensorEntity).
- Testlogik-Bugs in HA-19/20 (410/410 green nach Fix).
- UNLOAD_IN_PROGRESS Guard in async_unload_entry.

### Release Gate
- Alle 32 Commits sind test-only (kein Produktivcode).
- Branch: `release/v15.3.40-testimprovement` auf Origin.
- PS-151 drift guards: alle grün auf jedem Commit.
- Kein Live-/Install-/Restart-Schritt bis PR-Merge.

## [15.3.39] - 2026-04-05

### Changed
- Release-/Version-Surfaces auf eine frische, unrecycelte Zielversion oberhalb von `15.3.38` konsolidiert.
- `VERSION`, `custom_components/copilot_ha/VERSION` und `custom_components/copilot_ha/manifest.json` berichten jetzt einheitlich `15.3.39`.
- README-Release-Block von stale `v15.3.0` auf den aktuellen Release-Prep-Stand `v15.3.39` umgestellt.

### Fixed
- Drift zwischen Manifest, Repo-Version, komponenteninterner VERSION und Doku entfernt.
- Doppelte konkurrierende `15.3.38`-Blöcke bereinigt.
- Stale Release-Claims (`v15.3.0`, `READY FOR PRODUCTION`, veraltete Kompatibilitätsbehauptungen) aus dem aktiven Release-Pfad entfernt.

### Release Gate
- Dieser Stand ist **release-vorbereitet**, aber noch **nicht** getaggt und **nicht** veröffentlicht.
- Nächster separater Schritt nach Review: Tag `v15.3.39` auf genau diesen Release-Commit setzen und danach erst GitHub-Release mit `pilotsuite-styx-ha.zip` anlegen.

## [15.3.38] - 2026-04-02

### Updated
- Core-Version auf `v15.3.38` angehoben.
- README und CHANGELOG als Release-Doku für den damaligen Stand ergänzt.
- Main-basierte `voice_context`-Wahrheit entstand erst **nach** dem existierenden Tag `v15.3.38`; der alte Tag bleibt daher historisch und wird nicht recycelt.

## [v15.3.0] - 2026-04-01

### Added
- Zone Sync zwischen Core und Home Assistant.
- Tag-System für automatische Zone-/Entity-Zuordnung.
- Module-State-Steuerung pro Zone.
- Vorbereitete Lovelace-Cards und zugehörige Services.

## [v15.2.10] - 2026-03-31

### Added
- Habitus Zones API.
- Zone Auto-Setup.
- Entity Mapping.
- Module Sensors Batch 1-5.

### Changed
- ZoneType Enum als Single Source of Truth.
- Modul-Konfiguration pro Zone.

### Fixed
- Zone↔Entity-Mapping konsolidiert.
- HA↔Core-Sync verbessert.
