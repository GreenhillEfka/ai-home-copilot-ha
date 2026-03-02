# Changelog

Alle wesentlichen Änderungen am PilotSuite Styx Core Backend.

## [12.0.8] - 2026-03-02

### Added
- **Hybrid Cache Optimization** (`copilot_core/cache/hybrid_cache.py`)
  - **Redis + Local LRU Hybrid Architecture** - Zwei-Ebenen-Caching für maximale Performance
    - **Local LRU Cache**: Ultra-schneller In-Memory-Cache für heiße Daten (500-1000 Einträge)
    - **Redis Cache**: Geteilter, persistenter Cache für verteilte Systeme
    - **Write-Through Policy**: Schreibt in beide Ebenen gleichzeitig
    - **Read-Through Policy**: Prüft lokal zuerst, dann Redis (Fast Path)
  
  - **Optimiert für häufige Anfragen**:
    - **Sensor-Daten**: Hohe Lesefrequenz, moderate Schreibfrequenz (TTL: 5 Min)
    - **RAG-Ergebnisse**: Teuer zu berechnen, häufig abgerufen (TTL: 10 Min)
    - **Habitus-Zonen**: Mittlere Zugriffshäufigkeit (TTL: 15 Min)
  
  - **Cache-Hit-Rate Optimierung**:
    - **Target: >80% Hit-Rate** durch intelligentes Prefetching
    - LRU-Eviction verhindert Memory-Bloat
    - Automatische Metriken-Erfassung (Hits, Misses, Evictions, Expirations)
    - Graceful Degradation bei Redis-Ausfall (Local Cache als Fallback)
  
  - **Cache Warming**:
    - `warm_cache()` Methode zum Vorab-Füllen des Caches
    - Unterstützt asynchrone Loader-Funktionen
    - Fehler-tolerant (einzelne Fehler brechen nicht ab)
  
  - **Comprehensive Metrics**:
    - Getrennte Metriken für Local, Redis und Hybrid-Layer
    - Hit-Rate-Berechnung in Echtzeit
    - Verfügbar via `get_metrics()` / `get_stats()`

- **Global Cache Instances** (Singleton-Pattern):
  - `get_sensor_cache()` - 500 Einträge, 5 Min TTL, Target: >85% Hit-Rate
  - `get_habitus_cache()` - 200 Einträge, 15 Min TTL, Target: >80% Hit-Rate
  - `get_rag_cache()` - 1000 Einträge, 10 Min TTL, Target: >90% Hit-Rate
  - `init_all_caches()` / `shutdown_all_caches()` - Lifecycle-Management

- **Test Coverage** (`tests/test_hybrid_cache.py`):
  - **23 umfassende Tests** für HybridCacheManager:
    - Basic Operations (set, get, delete, clear, exists)
    - TTL-Expiration
    - LRU-Eviction
    - Get-or-Set Pattern (sync + async)
    - Metrics Tracking
    - **Hit-Rate Simulation** (>80% Target verifiziert)
    - Sensor Cache Hit-Rate Test
    - RAG Cache Hit-Rate Test
    - Global Instances (Singleton)
    - Cache Warming
    - Concurrency Tests (Read, Write, Mixed)

### Changed
- **Cache Architecture**:
  - Von einfachem In-Memory-Cache zu Hybrid-Architektur erweitert
  - Redis-Integration mit `redis.asyncio` (automatische Fallback-Logik)
  - Namespace-Prefix für Redis-Keys: `pilotsuite:hybrid:`

### Technical Details
- **HybridCacheManager Features**:
  - Async-safe mit `asyncio.Lock`
  - Hintergrund-Tasks für Cleanup und Redis-Sync
  - Konfigurierbare Parameter (TTL, Size, Redis-Settings)
  - Vollständige Typ-Hints (Python 3.11+)

- **Performance-Optimierungen**:
  - Local Cache: O(1) Lookup via OrderedDict
  - LRU-Eviction: Automatisch bei Size-Überschreitung
  - Redis: Connection-Pooling durch `redis.asyncio`
  - Minimaler Overhead bei Local-Cache-Hits

### Test Results
- **Hybrid Cache Tests**: 23/23 Tests ✅
  - Hit-Rate Simulation: **>80% achieved** ✅
  - Sensor Cache: **>85% hit rate** ✅
  - RAG Cache: **>90% hit rate** ✅
  - Concurrency: Alle Tests bestanden ✅

### Files Changed
- `copilot_core/cache/hybrid_cache.py` (NEW) - 650+ Zeilen
- `tests/test_hybrid_cache.py` (NEW) - 23 Tests
- `copilot_core/cache.py` (UPDATED) - Legacy-Code beibehalten

### Migration Guide
```python
# Alt (einfacher Cache)
from copilot_core.cache import CacheManager
cache = CacheManager(default_ttl=300)

# Neu (Hybrid Cache mit Redis)
from copilot_core.cache.hybrid_cache import HybridCacheManager
cache = HybridCacheManager(
    redis_host="localhost",
    redis_port=6379,
    local_cache_size=500,
    default_ttl=300,
)
await cache.start()

# Nutzung (API identisch)
await cache.set("key", value, ttl=300)
value = await cache.get("key")
metrics = await cache.get_metrics()
```

### Usage Examples
```python
# Sensor-Daten cachen (hohe Frequenz)
from copilot_core.cache.hybrid_cache import get_sensor_cache

sensor_cache = get_sensor_cache()
await sensor_cache.start()

# Sensor-Wert cachen
await sensor_cache.set("sensor:temp:1", {"value": 23.5, "unit": "°C"})

# Sensor-Wert lesen (Local Cache First)
data = await sensor_cache.get("sensor:temp:1")

# Metriken prüfen
metrics = await sensor_cache.get_metrics()
print(f"Hit-Rate: {metrics['hybrid']['metrics']['hit_rate']:.2%}")

# RAG-Ergebnisse cachen (teure Berechnung)
from copilot_core.cache.hybrid_cache import get_rag_cache

rag_cache = get_rag_cache()
await rag_cache.start()

# Teure Berechnung cachen
async def expensive_search(query):
    # ... RAG-Suche ...
    return results

results = await rag_cache.get_or_set(
    f"rag:{query}",
    expensive_search,
    ttl=600  # 10 Minuten
)
```

## [12.0.7] - 2026-03-02

### Added
- **API Performance Optimization**
  - `CacheManager` (`copilot_core/api/cache_manager.py`) - Redis-basiertes Caching mit lokalem Fallback
  - `QueryOptimizer` (`copilot_core/api/query_optimizer.py`) - Query-Timing, Index-Suggestions, langsame Query-Erkennung
  - `lazy_load()` Helper für paginierte Responses
  - `@cached` Decorator für API-Endpoints mit automatischem Caching

- **Predictive Automation** (`copilot_core/predictive_automation.py`)
  - ML-basierte Vorhersage von Nutzeraktionen (RandomForest)
  - Automatische Automation-Vorschläge basierend auf Verhalten
  - Verhaltensmuster-Analyse und -Speicherung
  - Integration mit BrainGraphService für kontextuelle Vorhersagen

- **Test Coverage**
  - `test_phase5_integration.py` - 22 Integration Tests für:
    - Notifications API (5 Tests)
    - Sharing API / Cross-Home-Sharing (4 Tests)
    - Collective Intelligence API (5 Tests)
    - Federated Learning Edge Cases (8 Tests)
  - `test_cache.py` - 10 Tests für CacheManager (LRU, TTL, Patterns)
  - `test_cache_manager.py` - 13 Tests für Cache & QueryOptimizer
  - `test_predictive_automation.py` - 15 Tests für Predictive Automation

### Changed
- **Test Improvements**
  - Fixed test_cache.py to match actual CacheManager API
  - Removed tests for non-existent functions
  - Added tests for invalidate_pattern() and stats()

### Technical Details
- CacheManager unterstützt Redis + lokalen In-Memory Cache
- Automatische Fallback-Logik bei Redis-Ausfall
- LRU-Eviction bei vollem Cache
- QueryOptimizer trackt langsame Queries und schlägt Indexes vor
- Predictive Automation lernt aus Nutzerverhalten (Zeit, Zone, Entity, Action)

### Test Results
- **Phase 5 Integration**: 22/22 Tests ✅
- **Cache Manager**: 23/23 Tests ✅ (test_cache.py + test_cache_manager.py)
- **Predictive Automation**: 15/15 Tests ✅
- **Total New Tests**: 60 Tests added, all passing

### Files Changed
- `copilot_core/api/cache_manager.py` (NEW)
- `copilot_core/api/query_optimizer.py` (NEW)
- `copilot_core/predictive_automation.py` (NEW)
- `tests/test_phase5_integration.py` (NEW)
- `tests/test_cache.py` (UPDATED)
- `tests/test_cache_manager.py` (NEW)
- `tests/test_predictive_automation.py` (NEW)

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
