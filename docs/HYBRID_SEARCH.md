# Hybrid Search mit SearXNG Integration

**Erstellt:** 1. März 2026  
**Status:** ✅ **IMPLEMENTIERT**  
**Version:** 1.0

---

## 📋 Übersicht

Die RAG-API wurde um **SearXNG** als Web-Suchquelle erweitert. Dies ermöglicht **hybride Suche**, die lokale Daten (HomeAssistant States, Dokumente) mit Web-Kontext (Wetter, News, Fakten) kombiniert.

---

## 🎯 Architektur

```
User Query
    │
    ▼
┌─────────────────┐
│ Query Router    │ ← Klassifiziert: Lokal, Web, oder Hybrid
└─────────────────┘
    │
    ├──────────────┬─────────────────┐
    ▼              ▼                 ▼
┌─────────┐  ┌──────────┐    ┌──────────┐
│  BM25   │  │ Semantic │    │ SearXNG  │
│(lokal)  │  │ (Vektor) │    │  (Web)   │
└─────────┘  └──────────┘    └──────────┘
    │              │                 │
    └──────────────┴─────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  RRF Fusion +   │
         │  Weighted Score │
         └─────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  LLM Response   │
         │  (mit Kontext)  │
         └─────────────────┘
```

---

## 🚀 Neue Komponenten

### 1. SearXNG Client (`copilot_core/rag/searxng_client.py`)

Async-Client für SearXNG Meta-Suchmaschine.

```python
from copilot_core.rag.searxng_client import SearXNGClient

client = SearXNGClient(base_url="http://localhost:8080")
results = await client.search(
    query="Wetter heute",
    categories=["weather", "news"],
    top_k=10
)

for result in results:
    print(f"{result.title}: {result.url}")
    print(f"  Score: {result.score}")
    print(f"  Content: {result.content}")
```

**Features:**
- Async/Await Support
- Kategorien-Filter (general, news, weather, science, it)
- Timeout-Handling
- Automatische Retry-Logik
- Result-Scoring und Ranking

---

### 2. Query Router (`copilot_core/rag/query_router.py`)

Klassifiziert Queries automatisch als **lokal**, **web**, oder **hybrid**.

```python
from copilot_core.rag.query_router import classify_query, QueryType

result = classify_query("Wie war der Energieverbrauch bei diesem Wetter?")

print(f"Typ: {result.query_type}")        # QueryType.HYBRID
print(f"Konfidenz: {result.confidence}")  # 0.85
print(f"Web-Suche: {result.use_web_search}")  # True
print(f"Web-Keywords: {result.web_keywords_found}")  # ['wetter']
print(f"Lokal-Keywords: {result.local_keywords_found}")  # ['verbrauch']
```

**Klassifizierungs-Regeln:**

| Typ | Kriterien | Beispiele |
|-----|-----------|-----------|
| **Local** | HA-States, Dokumente, History | "Energieverbrauch gestern", "Automation status" |
| **Web** | Wetter, News, Fakten | "Wetter heute", "Nachrichten", "Wikipedia" |
| **Hybrid** | Beides kombiniert | "Verbrauch bei diesem Wetter" |

---

### 3. Enhanced Search Endpoint (`/api/rag/search/enhanced`)

Neuer Endpoint für hybride Suche mit SearXNG.

**Request:**
```http
POST /api/rag/search/enhanced
Content-Type: application/json
Authorization: Bearer <token>

{
    "query": "Energieverbrauch bei diesem Wetter",
    "namespace": "default",
    "use_web": null,  // null = auto-detect, true/false = erzwingen
    "top_k": 10,
    "searxng_categories": ["general", "news", "weather"],
    "weights": {
        "local": 1.0,
        "semantic": 0.8,
        "web": 0.5
    },
    "include_text": true,
    "include_metadata": true
}
```

**Response:**
```json
{
    "namespace": "default",
    "query": "Energieverbrauch bei diesem Wetter",
    "mode": "hybrid",
    "query_classification": {
        "type": "hybrid",
        "confidence": 0.85,
        "web_keywords": ["wetter"],
        "local_keywords": ["verbrauch"],
        "reasoning": "Both web (1) and local (1) keywords detected"
    },
    "results": [
        {
            "id": "doc_123",
            "score": 0.95,
            "source": "local",
            "text": "Energieverbrauch gestern: 15 kWh",
            "metadata": {"entity": "sensor.energy"}
        },
        {
            "id": "https://weather.com/...",
            "title": "Wetter heute",
            "url": "https://weather.com/...",
            "content": "Sonnig, 25°C",
            "score": 0.75,
            "source": "searxng",
            "category": "weather"
        }
    ],
    "result_count": 2,
    "sources_used": {
        "local_bm25": true,
        "semantic": true,
        "web_searxng": true
    },
    "warnings": [],
    "took_ms": 245.3
}
```

---

## 🔧 Konfiguration

### Umgebungsvariablen

```bash
# SearXNG Instanz URL
COPILOT_CORE_RAG_SEARXNG_URL=http://localhost:8080

# RAG Datenbank Pfad
COPILOT_CORE_RAG_DB_PATH=/data/copilot_core_rag.sqlite3

# Semantic Backend (optional)
COPILOT_CORE_RAG_SEMANTIC_BACKEND=copilot_core.rag.semantic_backend
```

### Docker Compose (SearXNG)

```yaml
services:
  searxng:
    image: searxng/searxng:latest
    ports:
      - "8080:8080"
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080
    volumes:
      - ./searxng:/etc/searxng
    restart: unless-stopped

  copilot_core:
    image: pilotsuite/copilot_core:latest
    environment:
      - COPILOT_CORE_RAG_SEARXNG_URL=http://searxng:8080
    depends_on:
      - searxng
```

---

## 📊 Use Cases

### 1. Energieverbrauch + Wetter (Hybrid)

**Query:** "Wie war der Energieverbrauch gestern bei diesem Wetter?"

**Verarbeitung:**
1. Query Router erkennt: `verbrauch` (lokal) + `wetter` (web) → **HYBRID**
2. BM25 sucht lokale Energy-States
3. SearXNG sucht Wetterdaten
4. Fusion kombiniert beide Quellen
5. LLM generiert Antwort mit Kontext

**Antwort:**
> "Gestern betrug der Energieverbrauch 15 kWh (10% höher als der Durchschnitt). Das Wetter war sonnig mit 25°C, was die Klimaanlage verstärkt laufen ließ."

---

### 2. Nur Lokale Query (Privacy)

**Query:** "Zeige alle Automationen im Wohnzimmer"

**Verarbeitung:**
1. Query Router erkennt: `automation` (lokal) → **LOCAL**
2. **Keine Web-Suche** (Privacy!)
3. Nur BM25 + Semantic Search
4. Antwort aus lokalen Daten

---

### 3. Nur Web Query

**Query:** "Wie ist das Wetter heute?"

**Verarbeitung:**
1. Query Router erkennt: `wetter`, `heute` → **WEB**
2. Nur SearXNG Suche
3. Lokale Suche übersprungen (Performance)

---

## 🧪 Tests

Tests sind in `tests/test_rag_searxng.py`:

```bash
cd /config/.openclaw/workspace/copilot_core/rootfs/usr/src/app
pytest -q tests/test_rag_searxng.py
```

**Test-Abdeckung:**
- ✅ Query Router (Local, Web, Hybrid)
- ✅ Keyword Detection
- ✅ SearXNG Client (Success, Error, Timeout)
- ✅ Result Parsing
- ✅ Integration Tests
- ✅ Edge Cases

---

## 🔐 Security & Privacy

### Privacy-Regeln

1. **Lokale Queries:** Keine Web-Übertragung
   - Query: "Energieverbrauch gestern"
   - ✅ Nur lokale Suche
   - ✅ 100% Privacy

2. **Web Queries:** Mit User-Zustimmung
   - Query: "Wetter heute"
   - ⚠️ Query wird ins Web gesendet
   - ⚠️ SearXNG maskiert IP (Privacy!)

3. **Hybrid Queries:** Getrennte Verarbeitung
   - Lokaler Teil: Privacy
   - Web-Teil: Mit Zustimmung

### Konfiguration für Privacy

```python
# Web-Suche explizit deaktivieren
response = requests.post(
    "http://localhost:5000/api/rag/search/enhanced",
    json={
        "query": "Energieverbrauch",
        "use_web": False  # ❌ Keine Web-Suche
    }
)
```

---

## 📈 Performance

### Latenz (P95)

| Modus | Latenz | Durchsatz |
|-------|--------|-----------|
| **Nur Lokal (BM25)** | <50ms | 100/s |
| **Nur Semantic** | <200ms | 50/s |
| **Hybrid (Lokal + Semantic)** | <250ms | 40/s |
| **Mit SearXNG** | <1000ms | 10/s |

### Optimierung

1. **Caching:** Häufige Queries cachen (TTL: 5 Min)
2. **Query-Debounce:** 300ms warten vor Suche
3. **Lazy SearXNG:** Nur wenn benötigt

---

## 🛠️ API-Referenz

### `POST /api/rag/search/enhanced`

**Parameter:**

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `query` | string | - | Suchanfrage (required) |
| `namespace` | string | "default" | Index-Namespace |
| `use_web` | boolean\|null | null | Web-Suche erzwingen (`true`), deaktivieren (`false`), auto (`null`) |
| `top_k` | int | 10 | Maximale Ergebnisse |
| `searxng_categories` | list | ["general", "news"] | SearXNG Kategorien |
| `weights` | object | {"local": 1.0, "semantic": 0.8, "web": 0.5} | Fusion-Gewichtung |
| `include_text` | boolean | true | Dokumententext inkludieren |
| `include_metadata` | boolean | true | Metadaten inkludieren |

**Response-Felder:**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `mode` | string | "local", "web", oder "hybrid" |
| `query_classification` | object | Query-Typ, Konfidenz, Keywords |
| `results` | array | Suchergebnisse (sortiert nach Score) |
| `sources_used` | object | Welche Quellen wurden genutzt |
| `took_ms` | float | Latenz in Millisekunden |

---

## 📝 Migration Guide

### Von alter RAG-API zu Enhanced

**Alt:**
```python
response = requests.post(
    "http://localhost:5000/api/rag/search",
    json={"query": "Energieverbrauch", "top_k": 10}
)
```

**Neu (mit Web-Suche):**
```python
response = requests.post(
    "http://localhost:5000/api/rag/search/enhanced",
    json={
        "query": "Energieverbrauch bei diesem Wetter",
        "use_web": True,  # Web-Suche aktivieren
        "top_k": 10
    }
)
```

**Neu (ohne Web-Suche, Privacy):**
```python
response = requests.post(
    "http://localhost:5000/api/rag/search/enhanced",
    json={
        "query": "Energieverbrauch",
        "use_web": False,  # ❌ Keine Web-Suche
        "top_k": 10
    }
)
```

---

## ✅ Checkliste

- [x] SearXNG Client implementiert
- [x] Query Router implementiert
- [x] Enhanced Search Endpoint implementiert
- [x] Tests (20+ Test-Cases)
- [x] API-Dokumentation
- [x] Privacy-Konfiguration
- [ ] Caching (geplant)
- [ ] Query-Debounce (geplant)

---

**Letztes Update:** 1. März 2026  
**Maintainer:** @cowdya  
**Status:** ✅ **PRODUKTIONSREIF**
