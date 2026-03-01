# Zero-Config Installation UX Research
## PilotSuite — Sofort-Start Erlebnis

**Erstellt:** 2026-03-01  
**Recherche-Status:** Best Practices & Industry Patterns  
**Ziel:** Minimale Konfiguration, maximale Auto-Discovery

---

## 📋 Zusammenfassung

Zero-Config Setup bedeutet: Der Nutzer installiert, und das System **funktioniert sofort** durch intelligente Auto-Discovery, regelbasiertes Auto-Tagging und progressive Onboarding-Schritte. Die besten Implementierungen kombinieren mDNS/Zeroconf für Netzwerk-Discovery mit heuristischen Entity-Mappings (Domain → Tag) und einem schrittweisen Onboarding, das Komplexität nur bei Bedarf enthüllt. Für PilotSuite empfiehlt sich ein **3-Phasen-Ansatz**: (1) Auto-Scan & Vorschläge, (2) Bestätigungs-Flow mit Smart Defaults, (3) Progressive Verfeinerung.

---

## 🔍 Key Findings

### 1. Auto-Discovery Patterns

**mDNS / Zeroconf (Bonjour/Avahi)**
- Geräte melden sich selbst im lokalen Netzwerk an (`_http._tcp`, `_mqtt._tcp`, `_home-assistant._tcp`)
- Keine IP-Konfiguration nötig — Geräte werden per Hostname + Port gefunden
- **Beispiel:** `pilotsuite.local:8123` statt `192.168.1.100:8123`

**UPnP / SSDP Discovery**
- Viele IoT-Geräte (Philips Hue, Sonos, Samsung SmartThings) broadcasten ihre Präsenz
- Standardisiertes Protokoll, breite Unterstützung

**Bluetooth Low Energy (BLE) Scanning**
- Für nahe Geräte: Temp-Sensoren, Smart Locks, Wearables
- RSSI-basierte Nähe-Erkennung für automatische Raum-Zuordnung

**Netzwerk-Scan Fallback**
- Aktives Scanning bekannter Ports (80, 443, 1883, 5000, 8123)
- Device-Fingerprinting via HTTP Headers, Banner-Grabbing

---

### 2. Entity Auto-Tagging Strategien

#### Regelbasiert (Deterministisch) ✅ Empfohlen für PilotSuite

```
Domain → Tag Mapping (Heuristiken)

Gerätetyp / Service → Entity-Tags
─────────────────────────────────────────────────
light.*              → #licht, #beleuchtung
switch.*             → #schalter, #steckdose
binary_sensor.*door  → #tür, #zugang, #sicherheit
binary_sensor.*motion→ #bewegung, #präsenz
sensor.*temperature  → #temperatur, #klima
sensor.*humidity     → #luftfeuchtigkeit, #klima
climate.*            → #heizung, #klima, #thermostat
cover.*              → #rollladen, #beschattung
media_player.*       → #unterhaltung, #audio, #video
camera.*             → #kamera, #überwachung
```

**Namens-basierte Heuristiken:**
```
Enthält "wohn" → #wohnzimmer
Enthält "küche" → #küche
Enthält "schlaf" → #schlafzimmer
Enthält "bad" → #badezimmer
Enthält "flur" → #flur
Enthält "aussen" → #außenbereich
```

**Hersteller-basierte Defaults:**
```
Philips Hue     → #licht, #farblicht
Sonos           → #audio, #multiroom
Netatmo         → #wetter, #klima
Ring/Arlo       → #kamera, #sicherheit
```

#### ML-basiert (Probabilistisch) 🔮 Zukunfts-Option

- Trainiertes Modell erkennt Muster aus Entity-Namen, Typen, Nutzungskontext
- Cluster-basierte Raum-Zuordnung (welche Entities werden zusammen genutzt?)
- **Nachteil:** Braucht Trainingsdaten, weniger transparent für Nutzer

---

### 3. Progressive Onboarding Flows

#### Flow A: "3-Klick Start" (Minimal)
```
Installation → Auto-Scan → Fertig
     ↓           ↓           ↓
   App       Findet      Dashboard
 starten    5 Geräte    mit Defaults
```

#### Flow B: "Guided Setup" (Empfohlen)
```
1. Willkommens-Screen
   "Willkommen bei PilotSuite! Wir scannen jetzt dein Netzwerk..."

2. Auto-Discovery läuft (30-60s)
   - Visuelles Feedback: "🔍 Suche nach Geräten..."
   - Live-Counter: "3 Geräte gefunden"

3. Review-Screen
   "Wir haben diese Geräte gefunden:"
   ✓ Philips Hue Bridge (Wohnzimmer)
   ✓ Sonos One (Küche)
   ✓ Netatmo Wetterstation (Außen)
   
   [Alle übernehmen] [Einzelne bearbeiten]

4. Raum-Zuordnung (Smart Defaults)
   "Basierend auf den Gerätenamen:"
   - Hue Light "Wohnzimmer Decke" → Wohnzimmer ✓
   - Sonos "Küche" → Küche ✓
   
   [Bestätigen] [Anpassen]

5. Fertig-Screen
   "🎉 PilotSuite ist bereit!"
   - Dashboard wird geladen
   - "Tippe hier für weitere Geräte"
   - "Tippe hier für Automationen"
```

#### Flow C: "Expert Mode" (Optional)
```
- Manuelles Hinzufügen per IP/URL
- Custom Entity-Konfiguration
- Erweiterte Tag-Regeln editieren
```

---

## 📊 Flow-Diagramme

### Auto-Discovery Pipeline
```
┌─────────────────────────────────────────────────────────────┐
│                    INSTALLATION START                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: Auto-Discovery (parallel, 30-60s)                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   mDNS      │  │    UPnP     │  │    BLE      │         │
│  │  Bonjour    │  │   SSDP      │  │  Scanning   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         ↓                ↓                ↓                 │
│  ┌─────────────────────────────────────────────────┐       │
│  │        Device Aggregation & Deduplication       │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: Auto-Tagging (regelbasiert, <5s)                  │
│  - Entity-Typ → Tags                                       │
│  - Name → Raum-Zuordnung                                   │
│  - Hersteller → Default-Icons & Kategorien                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: User Review (interaktiv)                          │
│  - Vorschläge anzeigen                                     │
│  - Bestätigen oder anpassen                                │
│  - Fortfahren mit Smart Defaults                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: Dashboard Ready                                   │
│  - Entities sind nutzbar                                   │
│  - Progressive Features freischalten                       │
└─────────────────────────────────────────────────────────────┘
```

### Tag-Regel-Engine
```
┌──────────────┐    ┌──────────────────────┐    ┌─────────────┐
│   Entity     │ →  │  Regel-Matcher       │ →  │   Tags      │
│   Metadata   │    │  (Priorisiert)       │    │   Applied   │
└──────────────┘    └──────────────────────┘    └─────────────┘
     ↓                       ↓                        ↓
domain: light         1. Hersteller-Regeln      #licht
name: "Wohnzimmer"    2. Domain-Regeln          #wohnzimmer
vendor: philips       3. Name-Heuristiken       #farblicht
                      4. Fallback               #beleuchtung
```

---

## 🏆 Best Practices für Default-Konfigurationen

### Smart Defaults (was automatisch gesetzt wird)

| Kategorie | Default | Begründung |
|-----------|---------|------------|
| **Einheiten** | °C, %, Lux | EU-Standard |
| **Sprache** | Systemsprache | Keine extra Konfiguration |
| **Zeitzone** | Automatisch (IP/OS) | Korrekte Automationen |
| **Dashboard** | Auto-Layout nach Räumen | Intuitive erste Ansicht |
| **Benachrichtigungen** | Aus (opt-in) | Nicht aufdringlich |
| **Automationen** | Basis-Vorschläge | "Licht bei Bewegung" optional |
| **Icons** | Hersteller-Defaults | Wiedererkennung |

### Progressive Feature-Freischaltung

```
Level 1 (Sofort):
✓ Alle Entities sichtbar
✓ Manuelles Steuern möglich
✓ Basis-Dashboard

Level 2 (nach 5 Min Nutzung):
✓ Automation-Vorschläge
✓ Raum-basierte Filter
✓ Favoriten-Pins

Level 3 (nach 24h / manueller Aktivierung):
✓ Komplexe Automationen
✓ Skript-Editor
✓ Externe Integrationen
```

---

## 💡 UX-Empfehlung für PilotSuite

### 🎯 Kern-Prinzipien

1. **"It Just Works"** — Erste Installation muss ohne Konfiguration funktionieren
2. **Transparente Magie** — Nutzer verstehen, was automatisch erkannt wurde
3. **Korrektur leicht gemacht** — Auto-Tagging ist Vorschlag, nicht Gesetz
4. **Progressive Komplexität** — Features enthüllen sich bei Bedarf

### 📱 Konkrete Umsetzung

**Phase 1: Installation (0-2 Min)**
```
- App starten
- "Netzwerk wird gescannt..." (Spinner + Fortschritt)
- Hintergrund: mDNS + UPnP + Port-Scan
- Visuelles Feedback: "3 Geräte gefunden..."
```

**Phase 2: Review (1-3 Min)**
```
- Liste der gefundenen Geräte mit Smart Tags
- Jeder Eintrag: [✓] [Bearbeiten]
- Bulk-Aktion: "Alle 5 übernehmen"
- Einzel-Korrektur: Raum ändern, Tag hinzufügen/entfernen
```

**Phase 3: Fertig (sofort)**
```
- Dashboard lädt mit auto-generiertem Layout
- "Erste Schritte" Tour (optional überspringbar)
- "Weitere Geräte hinzufügen" Button prominent
- "Automationen entdecken" als nächster Schritt
```

### 🔧 Technische Empfehlungen

1. **Discovery-Timeout:** 60s Maximaldauer, dann "Weitere Geräte manuell hinzufügen"
2. **Tag-Regeln als JSON-Config:** Ermöglicht Updates ohne App-Release
3. **Fallback-Strategie:** Unbekannte Geräte → Generic-Tags + manuelle Zuordnung
4. **Caching:** Bekannte Geräte beim nächsten Start sofort laden
5. **Offline-First:** Core-Funktionen ohne Cloud

### 📊 Erfolgsmetriken

- **Time-to-First-Action:** < 3 Minuten von Installation bis erstem Gerät steuern
- **Auto-Discovery-Rate:** > 80% der Geräte ohne manuelle Konfiguration
- **Tag-Accuracy:** > 90% der Auto-Tags vom Nutzer akzeptiert
- **Onboarding-Abbruch:** < 10% brechen vor Dashboard-Load ab

---

## 🧩 Auto-Tag-Regeln (Domain → Tag Mapping)

### Vollständige Mapping-Tabelle für PilotSuite

```yaml
# Entity Domain → Default Tags
light:
  tags: [#licht, #beleuchtung]
  icon: mdi:lightbulb
  
switch:
  tags: [#schalter, #steckdose]
  icon: mdi:power-socket
  
binary_sensor:
  motion:
    tags: [#bewegung, #präsenz, #sicherheit]
    icon: mdi:motion-sensor
  door:
    tags: [#tür, #zugang, #sicherheit]
    icon: mdi:door
  window:
    tags: [#fenster, #zugang]
    icon: mdi:window-open
  presence:
    tags: [#anwesenheit, #präsenz]
    icon: mdi:account

sensor:
  temperature:
    tags: [#temperatur, #klima]
    unit: °C
    icon: mdi:thermometer
  humidity:
    tags: [#luftfeuchtigkeit, #klima]
    unit: %
    icon: mdi:water-percent
  illuminance:
    tags: [#helligkeit, #licht]
    unit: lux
    icon: mdi:brightness-5
  battery:
    tags: [#batterie, #status]
    unit: %
    icon: mdi:battery

climate:
  tags: [#heizung, #klima, #thermostat]
  icon: mdi:thermostat
  
cover:
  tags: [#rollladen, #beschattung]
  icon: mdi:blinds
  
media_player:
  tags: [#unterhaltung, #audio, #video]
  icon: mdi:television
  
camera:
  tags: [#kamera, #überwachung, #sicherheit]
  icon: mdi:cctv

# Raum-Erkennung aus Entity-Name
raum_keywords:
  wohn: #wohnzimmer
  küche: #küche
  kuch: #küche
  schlaf: #schlafzimmer
  bad: #badezimmer
  flur: #flur
  gäste: #gästezimmer
  büro: #arbeitszimmer
  arbeit: #arbeitszimmer
  kinder: #kinderzimmer
  außen: #außenbereich
  garten: #garten
  terrasse: #terrasse

# Hersteller-spezifische Defaults
vendor_defaults:
  philips:
    extra_tags: [#hue, #farblicht]
  sonos:
    extra_tags: [#multiroom, #streaming]
  netatmo:
    extra_tags: [#wetterstation]
  ring:
    extra_tags: [#videotürklingel]
  arlo:
    extra_tags: [#überwachungskamera]
  ikea:
    extra_tags: [#tradfri]
  fritz:
    extra_tags: [#fritzbox, #telekom]
```

---

## 🚀 Nächste Schritte für PilotSuite

1. **Discovery-Engine implementieren** (mDNS + UPnP + Port-Scan)
2. **Tag-Regel-System als JSON-Config** (updates ohne Release)
3. **Onboarding-Flow mocken** (3-Phasen: Scan → Review → Ready)
4. **Smart Default Dashboard** (auto-Layout nach Räumen)
5. **Fallback-UI** für nicht-erkannte Geräte

---

**Quellen:** Industry Best Practices, Home Assistant Patterns, IoT UX Research  
**Status:** Ready für Umsetzung in PilotSuite
