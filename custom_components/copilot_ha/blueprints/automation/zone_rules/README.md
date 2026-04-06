# Zone-spezifische Rules Blueprints

Dieses Verzeichnis enthält Home Assistant Automations-Blueprints für zonenbasierte Regeln.

## Verfügbare Regeln

### Time-based Rules (`time_based_rules.yaml`)
- **Nachtmodus** - Aktiviert Nachtmodus basierend auf Uhrzeit (dimmt Lichter, reduziert Heizung)
- **Home Mode** - Aktiviert Komfort-Modus bei Anwesenheit
- **Away Mode** - Aktiviert Energiesparmodus bei Abwesenheit
- **Morgenroutine** - Sanftes Aufwachen mit Licht, Heizung, Jalousien

### Weather-based Rules (`weather_based_rules.yaml`)
- **Sonnenschutz** - Beschattet Fenster bei starker Sonneneinstrahlung
- **Regenschutz** - Schließt Fenster/Markisen bei Regen
- **Frostschutz** - Aktiviert Frostschutz bei niedrigen Temperaturen

### Occupancy-based Rules (`occupancy_based_rules.yaml`)
- **Zonen-Anwesenheit** - Auto-Licht ein/aus basierend auf Bewegungsmelder

## Verwendung

1. Blueprints in Home Assistant importieren (Settings > Automations > Blueprints)
2. Blueprint auswählen und Instanz erstellen
3. Gewünschte Zone und Entitäten zuweisen

## Unterstützte Zonen

- `zone:wohnbereich` - Wohnzimmer
- `zone:kochbereich` - Küche
- `zone:gangbereich` - Flur
- `zone:badbereich` - Bad
- `zone:schlafbereich` - Schlafzimmer
- `zone:terassenbereich` - Terrasse/Garten

## PilotSuite Integration

Diese Blueprints sind optimiert für die PilotSuite Zone-Konfiguration und nutzen:
- Zone-basierte Entity-Attribute
- Bereichs-basierte Aktionen
- Kontext-abhängige Automationen