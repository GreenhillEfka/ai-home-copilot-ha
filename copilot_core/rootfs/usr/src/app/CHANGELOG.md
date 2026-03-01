# Changelog

Alle wesentlichen Änderungen am PilotSuite Styx Core Backend.

## [Unreleased]

## [12.0.2] - 2026-03-01

### Fixed
- **RAG Blueprint Registration** - RAG Hybrid Search API jetzt korrekt in `core_setup.py` registriert
  - Blueprint-Pfad von `/api/rag` auf `/api/v1/rag` aktualisiert für Konsistenz
  - `init_rag_api()` Funktion hinzugefügt für Test-Isolation
  - Behebt 404-Fehler bei RAG-Endpoints in Test-Suite
  
- **Test Isolation** - Verbesserte Test-Isolation für Flask Blueprints
  - `tests/test_rag_hybrid_search.py` - Korrekte API-Pfade (`/api/v1/rag/*`)
  - `tests/test_rag_hybrid_api.py` - Korrekte API-Pfade (`/api/v1/rag/*`)
  - Fixture-Updates für saubere State-Resets zwischen Tests
  - Behebt Test-Pollution bei Suite-Durchläufen

### Changed
- **RAG Blueprint** (`copilot_core/api/v1/rag.py`):
  - URL-Prefix von `/api/rag` auf `/api/v1/rag` für API-Konsistenz
  - `init_rag_api()` Helper-Funktion für Test-Reset
  
- **Core Setup** (`copilot_core/core_setup.py`):
  - RAG Blueprint-Registrierung hinzugefügt
  - Import für `rag_bp` ergänzt

### Test Results
- **Core API Tests**: 209 passed, 1 skipped (RAG, Zone Editor, Notifications, Sharing)
- **RAG Hybrid Search**: 36/36 Tests passing
- **RAG Hybrid API**: 40/40 Tests passing  
- **Zone Editor**: 59/59 Tests passing
- **Notifications API**: 23/23 Tests passing
- **Sharing API**: 28/28 Tests passing

### Files Changed
- `copilot_core/api/v1/rag.py` - Blueprint-Prefix + init_rag_api()
- `copilot_core/core_setup.py` - RAG Blueprint-Registrierung
- `tests/test_rag_hybrid_search.py` - API-Pfad-Korrekturen
- `tests/test_rag_hybrid_api.py` - API-Pfad-Korrekturen

---

## [Zone Dashboard] - 2026-03-01

### Added
- **Zone Dashboard API** (`/api/v1/zone/dashboard`) - Neue API für Zone-Übersicht mit Status, Mood und Quick-Actions
  - `GET /api/v1/zone/dashboard` - Komplette Dashboard-Daten aller Zonen
  - `GET /api/v1/zone/dashboard/summary` - Zusammenfassung (Counts, aktive Zonen)
  - `GET /api/v1/zone/dashboard/mood` - Mood-Daten aller Zonen (comfort, joy, frugality)
  - `PUT /api/v1/zone/dashboard/mood/<zone_id>` - Mood für Zone setzen
  - `POST /api/v1/zone/dashboard/quick-action` - Quick-Action ausführen
  - `GET /api/v1/zone/dashboard/<zone_id>` - Detail-Daten einer Zone
- **Zone Dashboard Frontend Component** (`static/zone_dashboard.js`)
  - Lit-basiertes Web Component für Grid-Dashboard
  - Echtzeit-Status (aktiv, idle, Personen)
  - Mood-Visualisierung (Balken für Komfort, Freude, Sparsamkeit)
  - Entity-Count pro Zone nach Domain
  - Quick-Actions (Licht an/aus, Komfort-Modus, Zone toggle)
  - Auto-Refresh alle 30 Sekunden
  - Integration mit Zone Editor (Navigation zur Vollbearbeitung)
- **Tests** (`tests/test_zone_dashboard.py`)
  - 25+ Tests für API-Endpunkte
  - Testabdeckung: Dashboard, Summary, Mood, Quick-Actions, Entity-Counts
  - Edge Cases: leere Zonen, fehlende Metadata, Default-Werte

### Integration
- Verwendet `habitus_zones.py` als Datenquelle
- Wiederverwendet Styles und Patterns aus `zone_editor.js`
- Kompatibel mit bestehender Zone-Editor-API
-准备 für HomeAssistant Entity-State-Integration

### Changed
- Zone Dashboard ist read-only (schnelle Übersicht)
- Zone Editor bleibt für vollständige Bearbeitung (CRUD)

---

## [11.9.0] - 2026-03-01

### Phase 6: Code Quality & Production Readiness

#### Added
- **Type Hints** für alle Phase 5 APIs:
  - `copilot_core/notifications/api.py` - Vollständige Type Hints für alle 5 Endpoints
  - `copilot_core/collective_intelligence/api.py` - Vollständige Type Hints für alle 15 Endpoints
  - `copilot_core/sharing/api.py` - Type Hints bereits vorhanden (v11.8.0)
  - Alle Endpoint-Funktionen verwenden `-> Tuple[Dict[str, Any], int]` Return-Typen
  - Alle Helper-Funktionen haben korrekte Type Annotations (`Optional[Any]`, `Dict[str, Any]`)

- **Dokumentation** erweitert:
  - Module Docstrings mit Endpoint-Übersicht
  - Request/Response Format-Dokumentation in allen Docstrings
  - Args/Returns Sections für alle Funktionen
  - `__all__` Export-Listen für öffentliche APIs

- **Tests** (`tests/test_phase6_type_hints.py`):
  - 8 neue Tests für Type Hint Validierung
  - Automatische Prüfung aller Return Annotations
  - Dokumentationstests für Module Docstrings
  - Alle Tests passing (100%)

#### Changed
- **Notifications API** (`copilot_core/notifications/api.py`):
  - Von `NotificationEngine | None` zu `Optional[NotificationEngine]`
  - Von `tuple` zu `Tuple[Dict[str, Any], int]` für alle Endpoints
  - Erweiterte Docstrings mit Request-Body-Beispielen

- **Collective Intelligence API** (`copilot_core/collective_intelligence/api.py`):
  - Von `CollectiveIntelligenceService | None` zu `Optional[CollectiveIntelligenceService]`
  - Von `tuple[dict[str, Any], int]` zu `Tuple[Dict[str, Any], int]`
  - Konsistente Type Hints für alle 15 Endpoints
  - `__all__` Liste für klare Export-Definition

#### Test Results
- **Gesamte Test-Suite**: 2201 passed, 4 skipped (99.8% Pass-Rate)
- **Phase 5 APIs**: 76/76 Tests passing (Notifications, Sharing, Collective Intelligence)
- **Phase 6 Type Hints**: 8/8 Tests passing
- **Alle Flask Integration Tests**: Enabled und laufend
- **Alle NumPy-abhängigen Tests**: Enabled und laufend

#### Files Changed
- `copilot_core/notifications/api.py` - Type hints und Dokumentation
- `copilot_core/collective_intelligence/api.py` - Type hints und Dokumentation
- `tests/test_phase6_type_hints.py` - Neue Type Hint Validierungstests
- `CHANGELOG.md` - Dieses Changelog

---

## [2026.03.01]

### Added
- Initiale Version Zone Dashboard
