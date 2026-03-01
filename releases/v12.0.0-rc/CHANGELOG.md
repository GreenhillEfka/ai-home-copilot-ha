# Changelog

Alle wesentlichen Änderungen am PilotSuite-Projekt werden in dieser Datei dokumentiert.

---

## [v12.0.0] - 2026-03-01

### Security Fixes (P1 - Critical)

#### WebSocket Authentication
- **websocket_handler.py**: Token-Validierung in `handle_connect()` hinzugefügt
  - Unterstützt Auth via `auth.token` Parameter, Query-Param oder Header
  - Bei fehlendem Token: Warning-Log aber erlaubt (Backward Compatibility)
  - Bei invalidem Token: Connection wird abgelehnt
  - Verhindert Unauthorized Monitoring von Neuron/Mood-Updates

#### Neuron State Override Protection
- **api/v1/neurons.py**: Admin-Token-Check für State-Overrides hinzugefügt
  - `/evaluate` mit `states` oder `context` Overrides erfordert Admin-Token
  - `/update` Endpoint erfordert immer Admin-Token
  - Neue `require_admin_token()` Funktion in `api/security.py`
  - Verhindert Manipulation der Neuron-Ergebnisse durch Clients

#### Security Module Erweiterung
- **api/security.py**: Neue `require_admin_token()` und `require_admin` Decorator
  - Immer Token-pflichtig (auch wenn globale Auth deaktiviert)
  - Für sensitive Operationen wie State-Manipulation

### Tests
- **test_auth_security.py**: 4 neue Security-Tests hinzugefügt
  - WebSocket Handler Import-Tests
  - Neuron State Override Auth-Tests
  - Alle 42 Security- und API-Tests grün ✅

### Documentation
- Review-Bericht: `groky-review-report-2026-03-01.md` erstellt
- Security-Fixes dokumentiert

---

## [Unreleased] - 2026-03-01

### Added

#### Neuron Dashboard Frontend
- **neuron_dashboard.html**: Vollständiges HTML5-Template mit dunklem PilotSuite-Theme
  - Canvas-Element für Performance-Rendering
  - Responsive Sidebar mit Legende und Statistiken
  - Tooltip-Container für Hover-Informationen
  - Steuerungs-Buttons (Demo Toggle, Reset, Random Fire)
  - CSS-Variablen für konsistentes Theming

- **neuron_dashboard.js**: D3.js Force-Directed Graph Implementierung
  - `NeuronNetwork` Klasse mit Canvas-Rendering
  - 14 Neuronen (3 Input, 8 Hidden, 3 Output)
  - 24 gewichtete Verbindungen (positiv/negativ)
  - Force-Directed Simulation mit d3-force v7
  - Zustandsbasierte Farben: inactive (#666), active (#4CAF50), firing (#FF5722)
  - Pulsierende Animation für feuernde Neuronen
  - Drag & Drop Interaktion für Nodes
  - Tooltips auf Hover mit Node-Details
  - WebSocket-Stub für spätere Live-Updates
  - Auto-Redraw bei Window-Resize
  - DPI-Support für HiDPI-Displays
  - Performance-Optimierung: alphaMin=0.01, velocityDecay=0.4
  - Kollisions-Erkennung mit forceCollide (radius=20)
  - Layer-basierte X-Positionierung für bessere Struktur

#### Tests
- **tests/test_neuron_dashboard.js**: Unit-Tests (20+ Tests)
  - Initialisierungs-Tests (Nodes, Links, Canvas)
  - Neuronen-Zustände Tests (Konstanten, Farben)
  - Verbindungen Tests (Gewichte, Connection-Count)
  - Canvas-Setup Tests (Größe, DPI)
  - Statistik-Tests (Update-Berechnung)
  - Methoden-Tests (resetLayout, setDemoMode, fireRandom, destroy)
  - Interaktions-Tests (Mouse-Events, Tooltip)
  - WebSocket-Tests (Nachrichten-Verarbeitung)
  - Resize-Handler Tests

- **tests/test_neuron_dashboard.test.js**: Integration-Tests (20+ Tests)
  - Dashboard Loading Tests (Canvas, Sidebar, Legende)
  - Statistik-Anzeige Tests (Neuronen/Verbindungs-Anzahl)
  - Neuronen-Visualisierung Tests (Typ-Verteilung)
  - Interaktions-Tests (Tooltip, Demo-Toggle, Reset, Random-Fire)
  - Canvas-Rendering Tests (Kontext, DPI, Render-Loop)
  - Zustands-Update Tests (Stats-Berechnung)
  - Responsive Design Tests (Resize, Canvas-Anpassung)
  - Performance-Tests (FPS-Stabilität, Memory-Leaks)
  - Fehlerbehandlungs-Tests (Canvas-Fehler)
  - URL-Parameter Tests (Demo-Param)

- **tests/test_neuron_dashboard_utils.js**: Utility-Tests (20+ Tests)
  - Konstanten-Tests (States, Colors, Layers)
  - Farb-Konvertierung (Hex↔RGB)
  - Distanz-Berechnung (euklidisch)
  - Collision Detection
  - State Transitions (Zyklus)
  - Weight Normalization
  - Alpha Blending
  - Pulse Animation (Radius-Berechnung)
  - Tooltip Position
  - Layer Positioning
  - Connection Counting
  - Node Filtering (Typ, State)
  - Random Selection
  - Throttling/Debouncing
  - Array Utilities (Shuffle, Chunk)
  - Object Utilities (Clone, Merge)

### Changed

### Deprecated

### Removed

### Fixed

### Security

---

## [0.2.0] - 2026-02-15

### Added
- PilotSuite Core API Endpoints
- Dashboard Template mit Jinja2
- LLM Provider Fallback Mechanism

### Changed
- Verbesserte Fehlerbehandlung in API
- Optimierte Startup-Skripte

---

## [0.1.0] - 2026-02-01

### Added
- Initiales PilotSuite Setup
- Copilot Core Add-on Struktur
- Grundlegende API-Endpunkte

---

## Format

Dieses Changelog folgt dem [Keep a Changelog](https://keepachangelog.com/de/1.0.0/) Standard.
Versionen verwenden [Semantic Versioning](https://semver.org/lang/de/).

---

## Zusammenfassung Neuron Dashboard

**Datum:** 2026-03-01  
**Implementierung:** D3.js Force-Directed Graph  
**Dateien:** 2 (HTML + JS)  
**Tests:** 60+ (Unit + Integration + Utils)  
**Features:**
- ✅ 14 Neuronen (3 Input, 8 Hidden, 3 Output)
- ✅ 24 gewichtete Verbindungen
- ✅ Canvas-Rendering für Performance
- ✅ Zustandsbasierte Visualisierung
- ✅ Pulsierende Animation
- ✅ Drag & Drop
- ✅ Tooltips
- ✅ WebSocket-Ready
- ✅ Responsive Design
- ✅ Demo-Modus

**Nächste Schritte:**
1. WebSocket-Server im Backend implementieren
2. Live-Daten aus PilotSuite Neural Engine
3. Zoom & Pan mit d3-zoom
4. Filter-Controls für Layer-Ansicht
5. Export-Funktion (PNG/SVG)
