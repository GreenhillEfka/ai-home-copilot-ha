# Home Assistant Instanz Analyse

**Datum:** 2026-03-01  
**Instanz:** http://localhost:8123  
**Status:** ✅ Erreichbar

---

## 📊 Executive Summary

Diese Analyse bietet einen umfassenden Überblick über die Home Assistant Instanz als Basis für UX/Frontend-Entscheidungen und ein Auto-Tag-System.

### Key Metrics
- **Gesamt-Entities:** 4.374
- **Automationen:** 110
- **Zonen:** 10
- **Räume mit Automatisierung:** 14+

---

## 1. Entity-Verteilung nach Domain

| Domain | Count | % |
|--------|-------|---|
| sensor | 1.652 | 37,8% |
| switch | 551 | 12,6% |
| binary_sensor | 457 | 10,5% |
| button | 350 | 8,0% |
| update | 266 | 6,1% |
| light | 176 | 4,0% |
| scene | 160 | 3,7% |
| device_tracker | 142 | 3,2% |
| **automation** | **110** | **2,5%** |
| select | 95 | 2,2% |
| number | 81 | 1,9% |
| input_number | 78 | 1,8% |
| input_boolean | 75 | 1,7% |
| event | 72 | 1,6% |
| media_player | 51 | 1,2% |
| calendar | 37 | 0,8% |

**Weitere Domains:** text (18), input_text (18), image (16), script (11), zone (10), remote (10), counter (9), climate (8), person (7), fan (7), camera (6), weather (6), uvm.

---

## 2. Raum-Analyse (Entities nach Raum)

### Top-Räume nach Entity-Count

| Raum | Entities | Automationen | Lights | Sensors | Switches |
|------|----------|--------------|--------|---------|----------|
| **wohnzimmer** | 312 | 7 | 10 | 79 | 78 |
| **gang** | 168 | 5 | 12 | 46 | 18 |
| **loft** | 166 | 5 | 4 | 50 | 57 |
| **arbeitszimmer** | 159 | 1 | 6 | 49 | 41 |
| **schlafzimmer** | 127 | 2 | 2 | 42 | 6 |
| **zimmer_mira** | 92 | 3 | 5 | 33 | 4 |
| **bad** | 81 | 6 | 7 | 20 | 7 |
| **terrasse** | 77 | 3 | 4 | 33 | 3 |
| **kuche** | 74 | 5 | 5 | 18 | 4 |
| **toilette** | 73 | 3 | 7 | 22 | 7 |
| **vordereingang** | 39 | 5 | 4 | 8 | 4 |
| **erdkeller** | 39 | 2 | 3 | 11 | 1 |
| **hintereingang** | 34 | 2 | 2 | 10 | - |
| **speisekammer** | 14 | 2 | - | 4 | - |

### Raum-Übersicht mit Domains

Die Analyse zeigt eine **klare Raumstruktur** mit folgenden Schwerpunkten:

- **Wohnzimmer:** Medien-Hub (78 Switches, 79 Sensors, 5 Media Player)
- **Gang:** Verteilung & Durchgang (12 Lights, 25 Scenes)
- **Loft:** Technik-Zentrum (57 Switches, 29 Buttons)
- **Arbeitszimmer:** Büro-Automation (41 Switches, 6 Device Tracker)
- **Schlafzimmer:** Komfort & Ambiente (18 Scenes, 11 Input Numbers)

---

## 3. Zonen-Übersicht

| Zone | Entity ID | Radius (m) |
|------|-----------|------------|
| SmartHome (Home) | zone.home | - |
| Arbeit Ranshofen | zone.arbeit_ranshofen | 1.013 |
| Arbeit Braunau | zone.arbeit_braunau | 250 |
| Realschule Simbach | zone.realschule_simbach | 498 |
| Oma Leni und Opa Herbert | zone.oma_leni_und_opa_herbert | 26 |
| Oma Käthe und Opa Gustl | zone.oma_kathe_und_opa_gustl | - |
| Butze Bachi | zone.butze_bachi | 29 |
| Cafe Lazy Cat | zone.cafe_lazy_cat | - |
| Cafe Il2 | zone.cafe_il2 | - |
| Stadtkern Parrkirchen | zone.stadtkern_parrkirchen | - |

---

## 4. Automation-Analyse

### 4.1 Automation-Count nach Modus

| Modus | Count | Beschreibung |
|-------|-------|--------------|
| single | 58 | Standard: Ein Durchlauf, Warteschlange |
| restart | 42 | Bei neuer Auslösung: vorherige stoppen |
| parallel | 1 | Mehrere Durchläufe gleichzeitig |
| - | 9 | Kein Modus definiert (legacy) |

**Gesamt:** 110 Automationen

### 4.2 Automation-Kategorien (nach Name)

#### Anwesenheits-Automationen
- `*_automatisierung_anwesenheit` - Raum-basierte Anwesenheitserkennung
- Räume: Wohnzimmer, Gang, Küche, Bad, Schlafzimmer, Terrasse, Erdkeller, etc.

#### Licht-Automationen
- `*_automatisierung_licht` - Helligkeits- und Bewegungs-gesteuert
- `*_licht_*` - Spezifische Lichtsteuerungen

#### Musik & Sound
- `sonos_*` - Sonos Multiroom, Auto-Play, Volume Management
- `*_musik_cloud_automatisierung` - Cloud-Musik Integration
- `sound_syncronisation_detection` - Sound Sync

#### TTS (Text-to-Speech)
- `tts_*` - Sprachansagen (Kaffeemaschine, Kühlschrank, Müll, etc.)
- `tts_neutralizer` - TTS Optimierung

#### Sicherheit & Zugang
- `nfc_*` - NFC Unlock (Vorder-/Hintereingang)
- `automation_handzeichen` - Handgesten-Steuerung
- `automation_magic_cube` - Magic Cube Events

#### Spezial-Automationen
- `kaffee_*` - Kaffee-Ökosystem (Zähler, Reset, Synchronisation)
- `gaszahler` - Gaszähler Monitoring
- `netatmo_welcome_*` - Personenerkennung (24 Personen!)

### 4.3 Trigger-Analyse (Beispiele aus Attributes)

**Häufige Trigger-Typen:**
- `state` - Entity Statusänderungen
- `time` - Zeitbasierte Trigger (Sonnenaufgang/-untergang)
- `event` - Events (Taster, Gesten, NFC)
- `numeric_state` - Schwellenwerte (Helligkeit, Temperatur)

### 4.4 Potenzielle Issues

#### ✅ Keine kritischen Fehler erkannt

**Beobachtungen:**
1. **9 Automationen ohne Modus** - Legacy Automationen, sollten überprüft werden
2. **Hohe Anzahl restart-Modus** (42) - Kann zu unerwartetem Verhalten führen bei schnellen Trigger-Folgen
3. **Doppelte Trigger möglich** bei:
   - Raum-Übergreifenden Anwesenheits-Automationen
   - Mehrfachen Licht-Automationen pro Raum

---

## 5. Device-Tracker & Personen

### Personen (7)
- andreas, efka, gustav, katharina, mira, pauli, steffi

### Device-Tracker (142)
- **Alexa Devices:** 8+ (Küche, Schlafzimmer, Wohnzimmer, etc.)
- **UniFi Devices:** 15+ (APs, Switches, Clients)
- **Mobile Devices:** iPhones, iPads, MacBooks
- **Spezial-Tracker:** Watch, Xbox, Nintendo Switch

---

## 6. Empfehlungen für Auto-Tag-System

### 6.1 Tag-Hierarchie Vorschlag

```
📍 location/
  ├── indoor/
  │   ├── wohnzimmer
  │   ├── gang
  │   ├── loft
  │   ├── arbeitszimmer
  │   ├── schlafzimmer
  │   ├── zimmer_mira
  │   ├── bad
  │   ├── kuche
  │   ├── toiletten
  │   ├── terrasse
  │   ├── erdkeller
  │   ├── vordereingang
  │   ├── hintereingang
  │   └── speisekammer
  └── outdoor/
      ├── garten
      └── grillplatz

🏷️ function/
  ├── lighting
  ├── climate
  ├── security
  ├── media
  ├── presence
  ├── energy
  └── notification

👥 occupancy/
  ├── high (wohnzimmer, kuche, gang)
  ├── medium (arbeitszimmer, bad, zimmer_mira)
  └── low (erdkeller, speisekammer, toiletten)

⚡ automation_level/
  ├── full (wohnzimmer, gang, bad, kuche)
  ├── partial (schlafzimmer, terrasse, arbeitszimmer)
  └── basic (erdkeller, speisekammer)
```

### 6.2 Auto-Tag-Regeln

**Basierend auf Entity-Patterns:**

```yaml
# Licht-Entities
light.* → tags: [function/lighting, location/{room}]

# Präsenz-Sensoren
binary_sensor.*anwesenheit* → tags: [function/presence, location/{room}]
binary_sensor.*bewegung* → tags: [function/presence, location/{room}]

# Automationen
automation.*anwesenheit* → tags: [function/presence, automation/trigger]
automation.*licht* → tags: [function/lighting, automation/action]
automation.*tts* → tags: [function/notification, automation/action]

# Medien
media_player.* → tags: [function/media, location/{room}]
scene.* → tags: [function/scene, location/{room}]
```

### 6.3 UX-Empfehlungen

1. **Raum-basierte Navigation** als Primary View
   - 14 klar definierte Räume
   - Wohnzimmer als Hauptfokus (312 Entities)

2. **Funktion-Filter** als Secondary View
   - Lighting (176 Lights + Scenes)
   - Climate (8 Climate Entities)
   - Media (51 Media Players)
   - Security (Alarm Panels, Cameras)

3. **Automation Dashboard**
   - 110 Automationen nach Kategorie gruppieren
   - Status-Übersicht (last_triggered, mode)
   - Quick-Enable/Disable pro Raum

4. **Person-Tracking View**
   - 7 Personen + 142 Device-Tracker
   - Anwesenheits-Heatmap pro Raum

---

## 7. Technische Details

### API-Zugriff
- **URL:** `http://localhost:8123`
- **Auth:** Bearer Token (aus ENV: `HOMEASSISTANT_TOKEN`)
- **Status:** ✅ Verfügbar

### Besondere Integrationen
- **UniFi Network:** Umfangreiches Device-Tracking
- **Sonos:** Multiroom-Audio mit 10+ Speakern
- **Hue:** 37 Hue-spezifische Lights
- **Zigbee2MQTT:** Bridge + Mesh-Status
- **Z-Wave:** Mesh-Netzwerk
- **Netatmo:** Welcome & Presence Cameras
- **AI Home Copilot:** Diverse AI-Buttons und Sensoren

---

## 8. Zusammenfassung

Diese Home Assistant Instanz ist eine **ausgereifte, produktive Installation** mit:

- ✅ **Klarer Raumstruktur** (14+ Räume)
- ✅ **Umfangreicher Automatisierung** (110 Automationen)
- ✅ **Vielfältiger Hardware** (4.374 Entities)
- ✅ **Guter Organisation** (Zonen, Personen, Scenes)

**Empfohlene nächste Schritte:**
1. Auto-Tag-System implementieren (siehe 6.1)
2. Legacy Automationen (9 ohne Modus) überprüfen
3. UX-Dashboard nach Raum-Struktur aufbauen
4. Automation-Dokumentation erweitern

---

*Analyse erstellt am 2026-03-01 für PilotSuite Styx UX/Frontend Entwicklung*
