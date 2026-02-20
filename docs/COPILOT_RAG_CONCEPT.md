# CoPilot RAG & Knowledge Graph Konzept

> **Stand: 2026-02-15** – Systematische Erfassung von Zusammenhängen als InfoBasis

---

## 1. Warum RAG? Warum Knowledge Graph?

### Das Problem
- **Habitus Miner** findet A→B Regeln (statistisch, zeitlich)
- **Event Store** speichert rohe Events (zeitlich begrenzt)
- **Candidate Store** hält Hypothesen (transient)

**Was fehlt:**
- Semantische Zusammenhänge ("Licht im Wohnzimmer" gehört zu "Wohnbereich")
- Kausale Ketten über mehrere Hops (A→B→C)
- Kontextuelle Beziehungen ("Wenn ich arbeite, ist Fokus wichtig")
- Persistente Wissensbasis für CoPilot-Entscheidungen

### Die Lösung: Zwei-Layer-System

```
┌─────────────────────────────────────────────────────────────────┐
│                    CoPilot Decision Layer                        │
│  (Neuronen, Mood, Vorschläge)                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Query
┌─────────────────────────────────────────────────────────────────┐
│                    RAG Query Interface                           │
│  "Was passiert meistens im Wohnzimmer am Abend?"                │
│  "Welche Lichter sind mit 'Entspannung' verbunden?"             │
└─────────────────────────────────────────────────────────────────┘
                    ↓                              ↓
┌──────────────────────────────┐  ┌───────────────────────────────┐
│     Knowledge Graph          │  │     Vector Store              │
│  (Strukturierte Beziehungen) │  │  (Semantische Suche)          │
│                              │  │                               │
│  • Entity → Area → Zone      │  │  • State embeddings           │
│  • Entity → Capabilities     │  │  • Pattern embeddings         │
│  • Pattern → Context         │  │  • User preference embeddings │
│  • Zone → Mood correlations  │  │  • Natural language queries   │
└──────────────────────────────┘  └───────────────────────────────┘
                    ↑                              ↑
┌─────────────────────────────────────────────────────────────────┐
│                    Data Sources                                  │
│  Event Store, Habitus Rules, HA States, User Preferences        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Knowledge Graph: Strukturierte Beziehungen

### 2.1 Knotentypen (Nodes)

```python
class NodeType(Enum):
    ENTITY = "entity"          # light.kitchen, sensor.temperature
    DOMAIN = "domain"          # light, sensor, switch
    AREA = "area"              # Wohnzimmer, Küche
    ZONE = "zone"              # habitus_zone_west, habitus_zone_night
    PATTERN = "pattern"        # A→B Regel aus Habitus
    MOOD = "mood"              # relax, focus, active
    CAPABILITY = "cap"         # dimmable, color_temp, power_metering
    TAG = "tag"                # aicp.place.kueche, aicp.role.safety
    USER = "user"              # Person (für Multi-User)
    TIME_CONTEXT = "time"      # morning, evening, weekday, weekend
```

### 2.2 Kanten (Edges) mit Gewichtungen

```python
class EdgeType(Enum):
    # Hierarchisch
    BELONGS_TO = "belongs_to"        # Entity → Area, Area → Zone
    HAS_CAPABILITY = "has_cap"       # Entity → Capability
    HAS_TAG = "has_tag"              # Entity → Tag
    
    # Kausal (aus Habitus)
    TRIGGERS = "triggers"            # Pattern A → B
    CORRELATES_WITH = "correlates"   # Statistische Korrelation
    
    # Kontextuell
    ACTIVE_DURING = "active_during"  # Pattern → TimeContext
    RELATES_TO_MOOD = "relates_mood" # Entity/Pattern → Mood
    
    # User-spezifisch
    PREFERRED_BY = "preferred_by"    # Entity/Pattern → User
    AVOIDED_BY = "avoided_by"        # Entity/Pattern → User

@dataclass
class Edge:
    source: str
    target: str
    type: EdgeType
    weight: float = 1.0
    confidence: float = 0.0
    source_type: str = "inferred"    # "explicit", "inferred", "learned"
    evidence: dict[str, Any] | None = None  # {"nAB": 42, "confidence": 0.85}
    created: str = ""
    updated: str = ""
```

### 2.3 Graph-Beispiele

```
Entity: light.kitchen
  ├── BELONGS_TO → area.kitchen (weight=1.0, source=explicit)
  ├── HAS_CAPABILITY → cap.dimmable (weight=1.0, source=explicit)
  ├── HAS_TAG → tag.aicp.place.kueche (weight=1.0, source=explicit)
  └── RELATES_TO_MOOD → mood.relax (weight=0.7, source=learned, 
                                     evidence={"n_evening_on": 89, "p": 0.78})

Pattern: light.kitchen:on → light.livingroom:on (dt=120s)
  ├── TRIGGERS → light.livingroom:on (weight=0.85, confidence=0.82)
  ├── ACTIVE_DURING → time.evening (weight=0.9)
  └── RELATES_TO_MOOD → mood.relax (weight=0.75)
```

---

## 3. Vector Store: Semantische Suche

### 3.1 Embedding-Quellen

```python
class EmbeddingType(Enum):
    STATE_SNAPSHOT = "state_snapshot"   # HA state als Text → Embedding
    PATTERN_DESCRIPTION = "pattern"      # "Licht an im Wohnzimmer am Abend"
    USER_PREFERENCE = "user_pref"        # "Ich mag es gemütlich"
    CONTEXT_BUNDLE = "context"           # Aggregierter Kontext
    NATURAL_QUERY = "query"              # User-Frage für Similarity Search
```

### 3.2 Embedding-Generierung

**Option A: Lokal (privatsphäre-freundlich)**
- `sentence-transformers/all-MiniLM-L6-v2` (384 dim, schnell)
- `BAAI/bge-m3` (1024 dim, mehrsprachig, besser)
- Läuft auf CPU, kein API-Key nötig

**Option B: Ollama (bereits vorhanden)**
- `nomic-embed-text` (768 dim)
- Integration via `http://192.168.31.84:11434/api/embeddings`

**Option C: Remote API (OpenAI, etc.)**
- Nur wenn lokale Option nicht reicht

### 3.3 State-to-Text Transformation

```python
def state_to_text(entity_id: str, state: str, attrs: dict) -> str:
    """Transformiert HA state in embedding-freundlichen Text."""
    
    # Entity-Name auflösen
    name = get_friendly_name(entity_id)
    area = get_area_name(entity_id)
    
    # State beschreiben
    if state == "on":
        state_desc = "eingeschaltet"
    elif state == "off":
        state_desc = "ausgeschaltet"
    elif state == "playing":
        state_desc = f"spielt {attrs.get('media_title', 'Medien')}"
    else:
        state_desc = f"Status: {state}"
    
    # Kontext anreichern
    parts = [f"{name} in {area} ist {state_desc}"]
    
    if attrs.get("brightness"):
        pct = int(attrs["brightness"] / 255 * 100)
        parts.append(f"Helligkeit: {pct}%")
    
    if attrs.get("temperature"):
        parts.append(f"Temperatur: {attrs['temperature']}°C")
    
    return ". ".join(parts) + "."
```

**Beispiel:**
```
Input: light.kitchen, state=on, brightness=180
Text: "Küchenlicht in Küche ist eingeschaltet. Helligkeit: 71%."
Embedding: [0.12, -0.34, 0.56, ...] (384-dim)
```

---

## 4. RAG Query Interface

### 4.1 Query-Typen

```python
class QueryType(Enum):
    SEMANTIC = "semantic"      # "Was passiert abends im Wohnzimmer?"
    STRUCTURAL = "structural"  # "Zeige alle Entities in Zone X"
    CAUSAL = "causal"          # "Was löst normalerweise Licht Y aus?"
    TEMPORAL = "temporal"      # "Was ist typisch um 22 Uhr?"
    CONTEXTUAL = "contextual"  # "Was passt zu Stimmung 'Entspannung'?"
```

### 4.2 Unified Query API

```python
class RAGQuery:
    query_type: QueryType
    text: str | None                    # Für semantic search
    entity_id: str | None               # Für entity-bezogene Queries
    zone_id: str | None                 # Für zone-bezogene Queries
    mood: str | None                    # Für mood-bezogene Queries
    time_context: str | None            # morning, evening, etc.
    max_results: int = 10
    min_confidence: float = 0.5
    include_evidence: bool = False      # Zeige Begründungen

class RAGResult:
    results: list[dict[str, Any]]
    sources: list[str]                  # Woher stammt die Info?
    confidence: float
    evidence: dict[str, Any] | None     # Beweise/Statistiken
```

### 4.3 Query-Beispiele

```python
# Beispiel 1: Semantische Suche
query = RAGQuery(
    query_type=QueryType.SEMANTIC,
    text="Ich möchte mich entspannen",
    max_results=5
)
# → Returns: Entities/Patterns mit hoher mood.relax-Korrelation

# Beispiel 2: Kausale Analyse
query = RAGQuery(
    query_type=QueryType.CAUSAL,
    entity_id="light.livingroom",
    max_results=10
)
# → Returns: Pattern-Graph aller A→B Regeln mit light.livingroom

# Beispiel 3: Kontextuelle Empfehlung
query = RAGQuery(
    query_type=QueryType.CONTEXTUAL,
    mood="focus",
    time_context="morning",
    max_results=3
)
# → Returns: Entities/Patterns die zu "Fokus am Morgen" passen
```

---

## 5. Implementierung: Phasen

### Phase 1: Knowledge Graph Foundation (v0.5.0)

**Ziel:** Strukturierte Beziehungen erfassbar machen

**Komponenten:**
1. **Graph Store** – SQLite-basiert oder Neo4j (embedded)
2. **Entity Graph Builder** – Liest HA States, baut Hierarchie
3. **Pattern Inserter** – Importiert Habitus-Regeln in Graph
4. **Graph Query API** – Einfache Traversierungen

**Scope:**
- Nodes: ENTITY, AREA, ZONE, PATTERN, MOOD, CAPABILITY
- Edges: BELONGS_TO, HAS_CAPABILITY, TRIGGERS, RELATES_TO_MOOD
- Keine Embeddings in Phase 1

**Files:**
```
copilot_core/
├── knowledge_graph/
│   ├── __init__.py
│   ├── graph_store.py      # SQLite/Neo4j backend
│   ├── models.py           # NodeType, EdgeType, Edge
│   ├── builder.py          # Graph aus HA states aufbauen
│   ├── pattern_importer.py # Habitus-Regeln importieren
│   └── api.py              # Query endpoints
```

### Phase 2: Vector Store Integration (v0.6.0)

**Ziel:** Semantische Suche ermöglichen

**Komponenten:**
1. **Embedding Service** – Lokales Modell oder Ollama
2. **State Embedder** – Transformiert HA states → Text → Embedding
3. **Vector Store** – FAISS oder Chroma (embedded)
4. **Semantic Search API** – Similarity queries

**Scope:**
- Embeddings für State Snapshots
- Similarity Search
- Kombinierte Graph + Vector Queries

**Files:**
```
copilot_core/
├── embeddings/
│   ├── __init__.py
│   ├── embedder.py         # Text → Embedding
│   ├── state_text.py       # State → Text Transformation
│   └── vector_store.py     # FAISS/Chroma wrapper
```

### Phase 3: RAG Integration (v0.7.0)

**Ziel:** Unified Query Interface für CoPilot

**Komponenten:**
1. **RAG Query Engine** – Kombiniert Graph + Vector
2. **Context Aggregator** – Fasst Query-Ergebnisse zusammen
3. **CoPilot Integration** – Neuronen nutzen RAG
4. **Explainability** – Zeigt Beweise für Ergebnisse

**Scope:**
- Alle Query-Typen
- Integration in Mood-Context
- Integration in Vorschlags-Engine

**Files:**
```
copilot_core/
├── rag/
│   ├── __init__.py
│   ├── query_engine.py     # Unified RAG queries
│   ├── context_aggregator.py
│   └── copilot_bridge.py   # Integration in Neuronen
```

---

## 6. Knowledge Graph vs. Vector Store: Wann was?

| Anwendungsfall | Knowledge Graph | Vector Store |
|---------------|-----------------|--------------|
| "Welche Entities sind in Zone X?" | ✅ Exakt | ❌ Unpräzise |
| "Was löst normalerweise Y aus?" | ✅ Kausale Kette | ⚠️ Ähnliche Patterns |
| "Ich möchte entspannen" | ❌ Kein Mapping | ✅ Semantic Search |
| "Zeige alle Lichter" | ✅ Filter nach Domain | ❌ Overkill |
| "Was ist typisch für Abend?" | ✅ Zeit-Kontext | ✅ Ähnliche States |
| Multi-Hop Reasoning | ✅ Traversierung | ❌ Nicht möglich |

**Empfehlung:** Beide Systeme parallel, kombinierte Queries.

---

## 7. Datenfluss: Von Events zu Knowledge

```
HA State Change
      ↓
Event Store (JSONL)
      ↓
Habitus Miner → A→B Rules (Pattern)
      ↓
Pattern Importer → Knowledge Graph
      ↓
State Embedder → Vector Store
      ↓
RAG Query Engine
      ↓
CoPilot Neuronen → Mood Context → Vorschläge
```

**Beispiel-Datenfluss:**

```
1. Event: light.kitchen:on @ 20:15
2. Event Store: persistiert mit Zone, Context
3. Habitus Miner: findet Pattern "light.kitchen:on → light.livingroom:on" (85% conf)
4. Graph: 
   - Pattern Node: p_001
   - Edge: p_001 TRIGGERS light.livingroom:on (0.85)
   - Edge: p_001 ACTIVE_DURING evening (0.9)
   - Edge: p_001 RELATES_TO_MOOD relax (0.75)
5. Embedding:
   - Text: "Küchenlicht geht an, meistens gefolgt von Wohnzimmerlicht am Abend"
   - Vector: [0.23, -0.45, ...]
6. RAG Query: "Was passiert wenn ich die Küche betrete?"
   → Graph: light.kitchen → Patterns → light.livingroom
   → Vector: Ähnliche States/Patterns
   → Result: "Meistens geht auch das Wohnzimmerlicht an"
```

---

## 8. CoPilot Integration

### 8.1 Neuron-Zugang zum RAG

```python
class NeuronContext:
    """Neuron fragt RAG für Kontext."""
    
    def get_related_patterns(self, entity_id: str) -> list[Pattern]:
        query = RAGQuery(
            query_type=QueryType.CAUSAL,
            entity_id=entity_id,
            max_results=5,
            min_confidence=0.7
        )
        result = rag_engine.query(query)
        return self._to_patterns(result)
    
    def get_mood_entities(self, mood: str) -> list[str]:
        query = RAGQuery(
            query_type=QueryType.CONTEXTUAL,
            mood=mood,
            max_results=10
        )
        result = rag_engine.query(query)
        return [r["entity_id"] for r in result.results]
```

### 8.2 Mood-Context Enhancement

```python
class MoodContext:
    """Mood wird durch RAG-Infos angereichert."""
    
    def enhance_mood(self, base_mood: str, current_state: dict) -> EnhancedMood:
        # 1. Ähnliche historische States finden
        similar = rag_engine.semantic_search(
            text=self._state_to_text(current_state),
            max_results=5
        )
        
        # 2. Typische Patterns für diese States
        patterns = []
        for state in similar:
            p = rag_engine.get_patterns(entity_id=state["entity_id"])
            patterns.extend(p)
        
        # 3. Mood-Korrelationen
        mood_scores = defaultdict(float)
        for p in patterns:
            if p.mood_correlation:
                mood_scores[p.mood_correlation.mood] += p.mood_correlation.score
        
        # 4. Enhanced Mood
        return EnhancedMood(
            base=base_mood,
            correlations=dict(mood_scores),
            evidence=[p.to_dict() for p in patterns[:3]],
            confidence=self._calculate_confidence(similar, patterns)
        )
```

---

## 9. Privacy & Performance

### 9.1 Privacy

- **Embeddings lokal** – Keine externen APIs nötig
- **Keine PII in Embeddings** – Entity-IDs, keine Namen/Adressen
- **Opt-out pro Entity** – Tag `aicp.rag.excluded`
- **Datenminimierung** – Nur relevante States embedden

### 9.2 Performance

| Komponente | Größe | Latenz |
|-----------|-------|--------|
| Knowledge Graph | ~1-5MB (1k entities) | <10ms |
| Vector Store | ~50-200MB (10k embeddings) | <50ms |
| Combined Query | – | <100ms |

**Optimierungen:**
- Graph: In-Memory Cache für häufige Queries
- Vector: IVF Index für schnelle Ähnlichkeitssuche
- Batch Embedding für neue States

---

## 10. Fragen & Entscheidungen

### Offen:
1. **Graph Backend:** SQLite (einfach) vs. Neo4j (mächtig) vs. NetworkX (Python-only)?
2. **Vector Store:** FAISS (Meta) vs. Chroma (einfacher) vs. Qdrant (produktiv)?
3. **Embedding-Modell:** Lokal (MiniLM/BGE) vs. Ollama (nomic-embed-text)?
4. **Sync-Strategie:** Real-time vs. Batch-Update?
5. **Multi-User:** User-spezifische Graphs oder gemeinsamer mit User-Edges?

### Empfehlung (v0.5-0.7):
- **Graph:** SQLite mit Adjazenzliste (einfach, eingebaut)
- **Vector:** Chroma (Python-native, persistent, einfach)
- **Embedding:** Ollama `nomic-embed-text` (bereits vorhanden, 768-dim)
- **Sync:** Batch alle 5 Minuten + Event-basiert bei wichtigen Änderungen
- **Multi-User:** Gemeinsamer Graph mit User-spezifischen Edges

---

## 11. Nächste Schritte

1. **v0.5.0 – Knowledge Graph Foundation**
   - Graph Store implementieren
   - Entity Graph Builder
   - Pattern Importer
   - Basis Query API

2. **v0.6.0 – Vector Store**
   - Ollama Embedding Integration
   - State-to-Text Pipeline
   - Chroma Vector Store
   - Semantic Search API

3. **v0.7.0 – RAG Integration**
   - Unified Query Engine
   - CoPilot Bridge
   - Mood Enhancement
   - Dashboard-Integration

---

## 12. Relation zu bestehendem System

| Bestehend | RAG-Erweiterung |
|-----------|-----------------|
| Event Store | → Embedding Store (zusätzlich) |
| Habitus Miner | → Pattern Import in Graph |
| Candidate Store | → Kann Graph befragen |
| Mood Context | → Wird durch RAG angereichert |
| Brain Graph (UI) | → Zeigt Graph-Struktur |
| Tag System | → Tags als Graph-Knoten |

**Synergien:**
- Brain Graph zeigt Knowledge Graph visuell
- Tags werden zu Graph-Knoten (automatisch)
- Habitus-Regeln werden zu Pattern-Knoten
- Mood-Context wird durch RAG informiert

---

*Dieses Konzept ist die Basis für die nächsten Entwicklungsphasen. Feedback erwünscht!*