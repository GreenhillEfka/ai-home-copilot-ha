# RAG-Architektur & Integration — PilotSuite

**Erstellt:** 1. März 2026, 16:00 Uhr  
**Status:** 🟢 **IN PROGRESS — Architektur-Klärung**  
**Version:** 1.0

---

## 🎯 Problem-Stellung

**Aktuelle Komponenten:**
1. **PilotSuite-Styx Chat-Interface** → Nutzt Ollama (lokale LLMs)
2. **OpenAI Integration für HA** → Separate Integration
3. **Unser RAG-System** → BM25 + Semantic + RRF
4. **SearXNG** → Meta-Suchdienst (Web-Suche)
5. **Onyx** → Enterprise Search Platform (hat eigenes RAG)

**Frage:** Wer macht was? Wie integrieren wir das sinnvoll?

---

## 📊 Komponenten-Übersicht

### **1. RAG-System (PilotSuite)**

| Attribut | Wert |
|----------|------|
| **Zweck** | Lokales Wissen abrufen (HA-States, Dokumente, History) |
| **Technik** | BM25 (lexikalisch) + Semantic (Vektor) + RRF (Fusion) |
| **Daten-Quellen** | HomeAssistant States, Dokumente, Chat-History, Logs |
| **LLM** | Agnostisch (Ollama ODER OpenAI) |
| **API** | `/api/rag/search` (6 Endpoints) |

**Was es macht:**
- Durchsucht **lokale** Datenquellen
- Kombiniert lexikalische + semantische Suche
- Liefert kontextuelle Antworten mit HA-Bezug

**Was es NICHT macht:**
- Keine Web-Suche (dafür ist SearXNG!)
- Kein LLM-Ersatz (nutzt LLM für Antwort-Generierung)

---

### **2. SearXNG**

| Attribut | Wert |
|----------|------|
| **Zweck** | Meta-Suchmaschine für **Web-Suche** |
| **Technik** | Aggregiert Google, Bing, DuckDuckGo, etc. |
| **Daten-Quellen** | Öffentliches Web |
| **LLM** | Keines (liefert Suchergebnisse) |
| **API** | `/search?q=...` |

**Was es macht:**
- Durchsucht das **öffentliche Web**
- Aggregiert Ergebnisse von 50+ Suchmaschinen
- Privacy-fokussiert (kein Tracking)

**Was es NICHT macht:**
- Kein Zugriff auf lokale HA-Daten
- Kein RAG (keine Vektor-Suche, keine Fusion)
- Keine Antwort-Generierung (nur Suchergebnisse)

---

### **3. Onyx**

| Attribut | Wert |
|----------|------|
| **Zweck** | Enterprise Search Platform |
| **Technik** | Eigenes RAG-System (Vektor + Keyword) |
| **Daten-Quellen** | Konfigurierbar (Docs, Confluence, Slack, etc.) |
| **LLM** | Integriert (OpenAI, Anthropic, lokale) |
| **API** | GraphQL + REST |

**Was es macht:**
- Vollständiges RAG-System (ähnlich unserem)
- Enterprise-Features (User-Management, Permissions)
- Multiple Daten-Quellen

**Was es NICHT macht:**
- Keine HA-spezifische Integration (out of the box)
- Kein SearXNG-Ersatz (keine Web-Suche)

---

### **4. OpenAI Integration für HA**

| Attribut | Wert |
|----------|------|
| **Zweck** | OpenAI LLMs in HomeAssistant nutzen |
| **Technik** | HA-Integration (offiziell) |
| **Daten-Quellen** | HA-States (als Context) |
| **LLM** | OpenAI (GPT-4, GPT-3.5) |
| **API** | HA Conversation Entity |

**Was es macht:**
- OpenAI LLMs für HA-Conversation
- Zugriff auf HA-States (als Prompt-Context)
- Simple Q&A über HA-Entitäten

**Was es NICHT macht:**
- Kein RAG (keine Vektor-Suche, keine Dokumente)
- Keine History (nur aktueller State)
- Keine lokale LLM-Option (nur OpenAI)

---

### **5. Ollama (PilotSuite-Styx)**

| Attribut | Wert |
|----------|------|
| **Zweck** | Lokale LLMs betreiben |
| **Technik** | LLM-Inferenz (Qwen3.5, Llama3, etc.) |
| **Daten-Quellen** | Prompt-Context (manuell) |
| **LLM** | Lokal (Ollama-Models) |
| **API** | `/api/generate`, `/api/chat` |

**Was es macht:**
- Lokale LLM-Inferenz (privacy, offline)
- Multiple Models parallel
- Günstig im Betrieb (keine API-Kosten)

**Was es NICHT macht:**
- Kein RAG (keine Vektor-Suche)
- Keine persistente Wissensdatenbank
- Keine Web-Suche

---

## 🔄 Idealer Workflow (Architektur v2.0)

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Query (HomeAssistant)                    │
│              "Wie war der Energieverbrauch gestern?"            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Query Router (PilotSuite)                     │
│  Klassifiziert Query-Typ:                                        │
│  - Lokal (HA-States, Dokumente) → RAG                           │
│  - Web (News, Wetter, Fakten) → SearXNG                         │
│  - Hybrid (Lokal + Web) → Beide + Fusion                        │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌─────────────────┐ ┌──────────┐ ┌─────────────────┐
    │   RAG-API       │ │ SearXNG  │ │ Onyx (optional) │
    │   (lokal)       │ │ (Web)    │ │ (Enterprise)    │
    │                 │ │          │ │                 │
    │ - BM25          │ │ - Google │ │ - Vektor        │
    │ - Semantic      │ │ - Bing   │ │ - Keyword       │
    │ - RRF Fusion    │ │ - DDG    │ │ - Fusion        │
    └─────────────────┘ └──────────┘ └─────────────────┘
              │               │               │
              └───────────────┴───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Result Fusion & Ranking                          │
│  - RRF (Reciprocal Rank Fusion)                                 │
│  - Weighted Scoring (Lokal > Web für HA-Queries)                │
│  - Deduplication                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              LLM (Antwort-Generierung)                           │
│  WAHLWEISE:                                                     │
│  - Ollama (lokal, privacy, günstig)                             │
│  - OpenAI (bessere Qualität, API-Kosten)                        │
│  - Anthropic (Claude, hohe Qualität)                            │
│                                                                 │
│  Prompt: "Basierend auf diesen Kontext: {RAG_Results}..."       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              HomeAssistant Response                              │
│  - Chat-Interface (PilotSuite-Styx)                             │
│  - Notify-Service (Push an User)                                │
│  - Log (für History & Training)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Architektur-Entscheidungen

### **1. RAG-API ist die ZENTRALE Schnittstelle**

✅ **ALLE LLMs (Ollama, OpenAI, Claude) nutzen RAG-API!**

```python
# ❌ Falsch: LLM fragt direkt HA-States ab
response = ollama.generate(prompt="Wie war der Energieverbrauch?")

# ✅ Richtig: RAG-API liefert kontextuelle Daten
rag_results = rag_api.search(query="Energieverbrauch gestern")
response = ollama.generate(
    prompt=f"Basierend auf: {rag_results}\nFrage: Energieverbrauch gestern?"
)
```

**Vorteile:**
- Einheitliche Datenquelle für ALLE LLMs
- RAG-Logik (BM25 + Semantic + RRF) zentral
- LLM ist austauschbar (Ollama ↔ OpenAI ↔ Claude)

---

### **2. SearXNG ist DATA-SOURCE für RAG**

✅ **SearXNG wird in RAG integriert (nicht separat!)**

```python
# RAG-API nutzt SearXNG für Web-Recherche
def hybrid_search(query: str):
    # 1. Lokale Suche (BM25 + Semantic)
    local_results = bm25_search(query)
    semantic_results = semantic_search(query)
    
    # 2. Web-Suche (SearXNG)
    if needs_web_context(query):
        web_results = searxng_search(query)
    else:
        web_results = []
    
    # 3. Fusion (RRF)
    return rrf_fusion(local_results, semantic_results, web_results)
```

**Vorteile:**
- RAG kann Web-Kontext hinzufügen (z.B. "Wie ist das Wetter heute?")
- Einheitliche API für Client (egal ob lokal oder Web)
- SearXNG ist eine von mehreren Daten-Quellen

---

### **3. Onyx ist ALTERNATIVE oder ERGÄNZUNG**

**Option A: Onyx ersetzt unser RAG**
- ✅ Vorteil: Enterprise-Features out of the box
- ❌ Nachteil: Weniger HA-spezifisch, mehr Overhead

**Option B: Onyx ergänzt unser RAG**
- ✅ Unser RAG für HA-spezifische Queries
- ✅ Onyx für Enterprise-Docs (Confluence, Slack, etc.)
- ✅ Fusion beider Ergebnisse

**Empfehlung: Option B** (hybrid)

```python
# RAG-API nutzt Onyx als zusätzliche Quelle
def enterprise_search(query: str):
    # 1. PilotSuite RAG (HA-Fokus)
    ha_results = pilotSuite_rag.search(query)
    
    # 2. Onyx RAG (Enterprise-Fokus)
    onyx_results = onyx_api.search(query)
    
    # 3. Fusion (HA > Enterprise für HA-Queries)
    return weighted_fusion(ha_results, onyx_results, weights=[0.7, 0.3])
```

---

### **4. OpenAI Integration für HA nutzt RAG-API**

✅ **OpenAI HA-Integration wird um RAG-API erweitert!**

**Aktuell (limitiert):**
```python
# OpenAI HA Integration (ohne RAG)
prompt = f"Current states: {hass.states.all()}\nUser: {query}"
response = openai.generate(prompt)
```

**Neu (mit RAG):**
```python
# OpenAI HA Integration (MIT RAG)
rag_results = rag_api.search(query)
prompt = f"Context from RAG: {rag_results}\nUser: {query}"
response = openai.generate(prompt)
```

**Implementierung:**
- Custom HA-Component (`pilotSuite_rag_conversation`)
- Ersetzt/augmentiert offizielle OpenAI-Integration
- Nutzt RAG-API für kontextuelle Antworten

---

### **5. Ollama (PilotSuite-Styx) nutzt RAG-API**

✅ **PilotSuite-Styx Chat-Interface nutzt RAG-API!**

```python
# PilotSuite-Styx Chat (MIT RAG)
async def handle_user_query(query: str):
    # 1. RAG-Suche (lokal + Web)
    rag_results = await rag_api.search(query)
    
    # 2. LLM-Prompt mit Kontext
    prompt = f"""
    Basierend auf diesem Kontext:
    {rag_results}
    
    Beantworte die Frage: {query}
    """
    
    # 3. Ollama-Inferenz
    response = await ollama.generate(
        model="qwen3.5:397b-cloud",
        prompt=prompt
    )
    
    return response
```

---

## 📋 Implementierungs-Plan

### **Phase 1: RAG-API erweitern (P0)**

| Task | Agent | Aufwand |
|------|-------|---------|
| SearXNG-Integration (als Data-Source) | @cowdya | 15 Min |
| Onyx-Integration (optional, als Data-Source) | @cowdya | 15 Min |
| Query-Router (Lokal vs. Web vs. Hybrid) | @cowdya | 10 Min |
| Result-Fusion (RRF + Weighted) | @cowdya | 10 Min |

### **Phase 2: OpenAI HA-Integration (P0)**

| Task | Agent | Aufwand |
|------|-------|---------|
| Custom HA-Component (`pilotSuite_rag_conversation`) | @coder-1 | 20 Min |
| RAG-API-Integration | @coder-1 | 10 Min |
| Tests (HA-Integration) | @coder-3 | 15 Min |

### **Phase 3: PilotSuite-Styx Update (P0)**

| Task | Agent | Aufwand |
|------|-------|---------|
| Chat-Interface auf RAG-API umstellen | @cowdya | 10 Min |
| Query-Router integrieren | @cowdya | 10 Min |
| Tests (Chat mit RAG) | @coder-3 | 10 Min |

### **Phase 4: Visual UX (P1)**

| Task | Agent | Aufwand |
|------|-------|---------|
| RAG Chat-UI (mit SearXNG-Toggle) | @viewona | 15 Min |
| Query-Typ-Indikator (Lokal/Web/Hybrid) | @viewona | 10 Min |

---

## 🔐 Security & Privacy

### **Daten-Fluss:**

```
User Query
    │
    ▼
┌─────────────────┐
│ Query Router    │ ← Prüft: Lokal oder Web?
└─────────────────┘
    │
    ├──────────────┬─────────────────┐
    ▼              ▼                 ▼
┌─────────┐  ┌──────────┐    ┌──────────┐
│   RAG   │  │ SearXNG  │    │  Onyx    │
│(lokal)  │  │  (Web)   │    │(optional)│
│✅ Privacy│  │⚠️ Public │    │⚠️ Config │
└─────────┘  └──────────┘    └──────────┘
```

### **Privacy-Regeln:**

1. **Lokale Queries (HA-States) → NUR lokales RAG**
   - Keine Web-Übertragung
   - SearXNG wird NICHT genutzt
   - 100% privacy

2. **Web-Queries (Wetter, News) → SearXNG**
   - Query wird ins Web gesendet
   - SearXNG maskiert IP (Privacy!)
   - User muss zustimmen (Toggle in UI)

3. **Hybrid-Queries → Beide**
   - Lokaler Teil: privacy
   - Web-Teil: mit User-Zustimmung

---

## 📊 Performance & Belastung

### **RAG-API Belastung:**

| Query-Typ | Latenz | Durchsatz | Belastung |
|-----------|--------|-----------|-----------|
| **Nur Lokal (BM25)** | <50ms | 100/s | Niedrig |
| **Nur Semantic** | <200ms | 50/s | Mittel |
| **Hybrid (BM25 + Semantic)** | <250ms | 40/s | Mittel |
| **Mit SearXNG** | <1000ms | 10/s | Hoch |
| **Mit Onyx** | <500ms | 20/s | Mittel |

### **Optimierung:**

1. **Caching:**
   - Häufige Queries cachen (TTL: 5 Min)
   - Reduziert Belastung um ~60%

2. **Query-Debounce:**
   - User tippt → 300ms warten → erst dann suchen
   - Reduziert Queries um ~80%

3. **Lazy SearXNG:**
   - SearXNG nur wenn explizit benötigt
   - Toggle in UI ("Web-Suche aktivieren")

---

## ✅ Empfehlung

### **Architektur:**

```
┌─────────────────────────────────────────────────────────┐
│              PilotSuite RAG-API (zentral)               │
│                                                         │
│  Data-Sources:                                          │
│  - Lokale DB (HA-States, Dokumente, History) ✅         │
│  - SearXNG (Web-Suche, optional) ✅                     │
│  - Onyx (Enterprise, optional) ⏳                       │
│                                                         │
│  LLM-Backends:                                          │
│  - Ollama (lokal, default) ✅                           │
│  - OpenAI (HA-Integration) ✅                           │
│  - Claude (optional) ⏳                                 │
└─────────────────────────────────────────────────────────┘
```

### **Nächste Schritte:**

1. **RAG-API erweitern** (SearXNG-Integration) — @cowdya
2. **OpenAI HA-Integration updaten** (RAG-API nutzen) — @coder-1
3. **PilotSuite-Styx updaten** (RAG-API nutzen) — @cowdya
4. **RAG Chat-UI** (mit SearXNG-Toggle) — @viewona

---

**Erstellt:** 1. März 2026, 16:00 Uhr  
**Status:** 🟢 **IN PROGRESS**  
**Nächste Iteration:** Implementierung startet SOFORT!
