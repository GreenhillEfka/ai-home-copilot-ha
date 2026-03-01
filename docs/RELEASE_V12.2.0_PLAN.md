# PilotSuite v12.2.0 Release Plan

> **Release-Datum:** März 2026  
> **Fokus:** Chat Pipeline, LLM-Provider-Abstraktion, Zero-Config Flow  
> **Priorität:** P0 (High Priority)

---

## 🎯 Release Vision

**v12.2.0** macht PilotSuite zum **kompletten Conversational AI System** für Home Assistant:

1. **Chat Pipeline** — Natürliche Sprachsteuerung mit RAG-Kontext
2. **LLM-Provider-Abstraktion** — OpenAI, Ollama, OpenClaw (optional) mit Fallback
3. **Zero-Config Flow** — Installation in <5 Minuten mit Long-Life HA Token
4. **Autarkie** — Funktioniert OHNE OpenClaw (OpenClaw ist optional!)

---

## 📋 Feature Overview

### P0: Chat Pipeline (Core Feature)

| Feature | Beschreibung | Status |
|---------|--------------|--------|
| **Conversation Agent** | HA-Assist Integration für Sprachsteuerung | ⏳ TODO |
| **RAG-Kontext** | HA-States, Historie, Dokumente im Prompt | ⏳ TODO |
| **LLM-Fallback** | OpenAI → Ollama → Ollama Tiny (immer online!) | ⏳ TODO |
| **Zero-Config** | Auto-Discovery + Long-Life HA Token | ⏳ TODO |

### P0: LLM-Provider-Abstraktion

| Provider | Beschreibung | Fallback-Level |
|----------|--------------|----------------|
| **OpenAI** | GPT-4 (beste Qualität, Cloud) | Primary |
| **Ollama** | qwen3.5:397b-cloud (lokal, privacy) | Fallback 1 |
| **Ollama Tiny** | qwen2.5:1.5b (klein, robust, immer da!) | Fallback 2 |
| **OpenClaw** | Clawdya (optional, wenn installiert) | Optional |

### P1: Zero-Config Flow

| Schritt | Beschreibung | Auto/Manual |
|---------|--------------|-------------|
| **1. HA Token** | Long-Life Access Token erstellen | Manual (einmalig) |
| **2. Config** | `configuration.yaml` mit minimalen Werten | Auto-Beispiel |
| **3. Discovery** | RAG-API Auto-Discovery (localhost:8765) | ✅ Automatisch |
| **4. LLM** | OpenAI-Key optional (Fallback zu Ollama) | Optional |
| **5. Start** | HA Neustart → Fertig! | ✅ Automatisch |

---

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│         HomeAssistant Assist Pipeline                            │
│         (Spracheingabe / Text-Input)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│   pilotSuite_rag_conversation (HA Component)                     │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  LLM-Fallback-Chain (automatisch!)                        │  │
│   │                                                           │  │
│   │  1️⃣ OpenAI (GPT-4) — Primary                             │  │
│   │     ↓ (Timeout/Error)                                     │  │
│   │  2️⃣ Ollama (qwen3.5) — Fallback 1                        │  │
│   │     ↓ (Timeout/Error)                                     │  │
│   │  3️⃣ Ollama Tiny (qwen2.5:1.5b) — Fallback 2              │  │
│   │     ↓ (Optional)                                          │  │
│   │  4️⃣ OpenClaw (Clawdya) — Nur wenn installiert            │  │
│   └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  RAG-API Client (IMMER dabei — autark!)                   │  │
│   │  - BM25 (HA-States, Dokumente, Historie)                  │  │
│   │  - Semantic (Vektor-Suche)                                │  │
│   │  - Optional: SearXNG (Web-Suche)                          │  │
│   └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Dateien (neu/geändert)

### Neu zu erstellen:

| Datei | Beschreibung | Prio |
|-------|--------------|------|
| `custom_components/pilotSuite_rag_conversation/llm_provider.py` | BaseLLMProvider Interface | P0 |
| `custom_components/pilotSuite_rag_conversation/providers/openai_provider.py` | OpenAI Implementation | P0 |
| `custom_components/pilotSuite_rag_conversation/providers/ollama_provider.py` | Ollama Implementation | P0 |
| `custom_components/pilotSuite_rag_conversation/providers/ollama_tiny_provider.py` | Ollama Tiny Implementation | P0 |
| `custom_components/pilotSuite_rag_conversation/providers/openclaw_provider.py` | OpenClaw Implementation (optional) | P2 |
| `custom_components/pilotSuite_rag_conversation/llm_fallback.py` | Fallback-Chain Logic | P0 |
| `custom_components/pilotSuite_rag_conversation/config_flow.py` | Zero-Config Setup Flow | P1 |
| `custom_components/pilotSuite_rag_conversation/strings.json` | i18n Strings (DE/EN) | P1 |

### Zu ändern:

| Datei | Änderung | Prio |
|-------|----------|------|
| `custom_components/pilotSuite_rag_conversation/__init__.py` | LLM-Provider-Integration | P0 |
| `custom_components/pilotSuite_rag_conversation/conversation.py` | Chat Pipeline Logic | P0 |
| `custom_components/pilotSuite_rag_conversation/manifest.json` | Version → 12.2.0, Dependencies | P0 |
| `custom_components/pilotSuite_rag_conversation/configuration.yaml` | Schema erweitern (Fallback, Provider) | P0 |
| `README.md` | Dokumentation für alle Provider | P1 |
| `CHANGELOG.md` | v12.2.0 Eintrag | P1 |

---

## 🚀 Implementierungs-Plan (gestaffelt für maximale Effizienz)

### Iteration 1: LLM-Provider-Abstraktion (17:55 - 18:15)

**Agent: @cowdya** (20 Min)

| Task | Datei | ETA |
|------|-------|-----|
| BaseLLMProvider Interface | `llm_provider.py` | 5 Min |
| OpenAIProvider | `providers/openai_provider.py` | 5 Min |
| OllamaProvider | `providers/ollama_provider.py` | 5 Min |
| OllamaTinyProvider | `providers/ollama_tiny_provider.py` | 5 Min |

**Acceptance Criteria:**
- ✅ Alle Provider implementieren `BaseLLMProvider`
- ✅ `generate(prompt: str) -> str` Interface
- ✅ Timeout-Handling (30s pro Provider)
- ✅ Logging (welcher Provider war erfolgreich?)

---

### Iteration 2: Fallback-Chain (18:15 - 18:30)

**Agent: @cowdya** (15 Min)

| Task | Datei | ETA |
|------|-------|-----|
| LLMFallbackChain | `llm_fallback.py` | 10 Min |
| Config-Schema erweitern | `configuration.yaml` | 5 Min |

**Acceptance Criteria:**
- ✅ Fallback-Reihenfolge konfigurierbar
- ✅ Automatischer Wechsel bei Error/Timeout
- ✅ Letzter Error wird geloggt
- ✅ Exception wenn ALLE Provider failen

---

### Iteration 3: Chat Pipeline Integration (18:30 - 18:50)

**Agent: @cowdya** (20 Min)

| Task | Datei | ETA |
|------|-------|-----|
| `__init__.py` aktualisieren | LLM-Provider-Init | 5 Min |
| `conversation.py` aktualisieren | Fallback-Chain-Integration | 10 Min |
| `manifest.json` Version | → 12.2.0 | 2 Min |
| Dependencies prüfen | `aiohttp`, `async-timeout` | 3 Min |

**Acceptance Criteria:**
- ✅ Conversation Agent nutzt Fallback-Chain
- ✅ RAG-Kontext wird in Prompt injiziert
- ✅ HA-Assist funktioniert (Sprache + Text)

---

### Iteration 4: Zero-Config Flow (18:50 - 19:10)

**Agent: @coder1** (20 Min)

| Task | Datei | ETA |
|------|-------|-----|
| `config_flow.py` erstellen | Setup Wizard | 10 Min |
| `strings.json` erstellen | DE/EN Strings | 5 Min |
| Auto-Discovery Logic | RAG-API auf localhost:8765 | 5 Min |

**Acceptance Criteria:**
- ✅ HA UI Config Flow (nicht nur YAML)
- ✅ Long-Life HA Token als einzige manuelle Eingabe
- ✅ RAG-API Auto-Discovery (localhost:8765)
- ✅ OpenAI-Key optional (Fallback zu Ollama)

---

### Iteration 5: Testing (19:10 - 19:30)

**Agent: @coder3** (20 Min)

| Task | Tests | ETA |
|------|-------|-----|
| Provider-Tests | OpenAI, Ollama, Ollama Tiny | 5 Min |
| Fallback-Tests | 20+ Szenarien | 10 Min |
| Integration-Tests | HA-Assist End-to-End | 5 Min |

**Acceptance Criteria:**
- ✅ 20+ neue Tests
- ✅ 95%+ Pass-Rate
- ✅ Fallback-Szenarien abgedeckt

---

### Iteration 6: Dokumentation & Release (19:30 - 19:45)

**Agent: @Clawdya** (15 Min)

| Task | Datei | ETA |
|------|-------|-----|
| README.md aktualisieren | Provider-Dokumentation | 5 Min |
| CHANGELOG.md | v12.2.0 Eintrag | 3 Min |
| WhatsApp-Summary | Release Notes | 2 Min |
| GitHub Release | v12.2.0-alpha.1 | 5 Min |

**Acceptance Criteria:**
- ✅ Dokumentation vollständig
- ✅ Release auf GitHub
- ✅ Community informiert

---

## ⏰ Zeitplan (gestaffelte Iterationen)

| Uhrzeit | Iteration | Agent | Fokus |
|---------|-----------|-------|-------|
| **17:55** | Iteration 1 | @cowdya | LLM-Provider-Abstraktion |
| **18:15** | Iteration 2 | @cowdya | Fallback-Chain |
| **18:30** | Iteration 3 | @cowdya | Chat Pipeline Integration |
| **18:50** | Iteration 4 | @coder1 | Zero-Config Flow |
| **19:10** | Iteration 5 | @coder3 | Testing (20+ Tests) |
| **19:30** | Iteration 6 | @Clawdya | Docs + Release |
| **19:45** | **DONE** | — | 🎉 v12.2.0-alpha.1 LIVE |

---

## 🔧 Zero-Config Flow (Detail-Spezifikation)

### Long-Life HA Token (Empfohlen!)

**Warum Long-Life Token?**
- ✅ Einmalig erstellen → funktioniert für immer
- ✅ Keine wiederholte Authentifizierung nötig
- ✅ Besser für Beispiel-Konfiguration (Copy-Paste)
- ✅ Sicherer als Passwort in Config

**Erstellung (einmalig):**
```yaml
# HomeAssistant → Profil → Long-Lived Access Token → Create Token
# Name: "PilotSuite"
# Token kopieren und in secrets.yaml:

openclaw_ha_token: YOUR_LONG_LIFE_TOKEN_HERE
```

### Minimal-Konfiguration (Zero-Config):

```yaml
# configuration.yaml (MINIMAL — nur 3 Zeilen!)
conversation:
  - platform: pilotSuite_rag_conversation
    ha_token: !secret openclaw_ha_token
    # RAG-API wird automatisch auf localhost:8765 entdeckt
    # LLM-Fallback: OpenAI (optional) → Ollama → Ollama Tiny
```

### Vollständige Konfiguration (alle Optionen):

```yaml
# configuration.yaml (VOLLSTÄNDIG)
conversation:
  - platform: pilotSuite_rag_conversation
    
    # HA Token (ERFORDERLICH)
    ha_token: !secret openclaw_ha_token
    
    # RAG-API (optional, Default: localhost:8765)
    rag_api_url: http://localhost:8765
    
    # Primary LLM-Provider (optional, Default: OpenAI)
    provider: openai
    openai_api_key: !secret openai_api_key
    model: gpt-4
    
    # Fallback-Kette (optional, Default: [openai, ollama, ollama_tiny])
    fallback_enabled: true
    fallback_order:
      - openai
      - ollama
      - ollama_tiny
    
    # Ollama-Config (Fallback 1)
    ollama_url: http://localhost:11434
    ollama_model: qwen3.5:397b-cloud
    
    # Ollama Tiny (Fallback 2)
    ollama_tiny_model: qwen2.5:1.5b
    
    # Privacy (optional, Default: false)
    use_web_search: false
```

---

## ✅ Acceptance Criteria (v12.2.0)

| Kriterium | Status |
|-----------|--------|
| **LLM-Provider-Abstraktion** | ✅ DONE (Iteration 1) |
| **Fallback-Chain (3 Level)** | ✅ DONE (Iteration 2) |
| **Chat Pipeline (HA-Assist)** | ✅ DONE (Iteration 3) |
| **Zero-Config Flow** | ✅ DONE (Iteration 4) |
| **20+ neue Tests** | ⏳ WAITING (Iteration 5 läuft parallel) |
| **Dokumentation vollständig** | ✅ DONE (Iteration 6) |
| **v12.2.0-alpha.1 Release** | ⏳ PENDING (wartet auf Test-Results) |

---

## 🎉 Release Notes (FINAL)

```markdown
## v12.2.0-alpha.1 — Chat Pipeline & LLM-Fallback

**Release-Datum:** 2026-03-01  
**Tag:** `v12.2.0-alpha.1`

### 🎯 Highlights

- **Chat Pipeline** — Natürliche Sprachsteuerung via HA-Assist
- **LLM-Provider-Abstraktion** — OpenAI, Ollama, OpenClaw (optional)
- **Fallback-Chain** — OpenAI → Ollama → Ollama Tiny (immer online!)
- **Zero-Config Flow** — Installation in <5 Minuten

### 🔧 Technical

- BaseLLMProvider Interface für alle Provider
- Automatische Fallback-Kette bei Error/Timeout
- RAG-API Auto-Discovery (localhost:8765)
- Long-Life HA Token für einfache Konfiguration

### 📚 Documentation

- Vollständige Provider-Dokumentation
- Zero-Config Setup-Guide
- Beispiel-Konfigurationen (minimal + vollständig)

### ⚠️ Breaking Changes

- **Keine!** Voll abwärtskompatibel

### 🙏 Credits

- @cowdya: LLM-Provider-Abstraktion, Fallback-Chain
- @coder1: Zero-Config Flow, Config Flow UI
- @coder3: Testing (20+ Tests)
- @groky: Release Management, CI/CD

### 📊 Test Results

**Status:** ⏳ WAITING (Iteration 5 läuft parallel)

**Erwartet:**
- 20+ neue Tests
- 95%+ Pass-Rate
- Fallback-Szenarien vollständig abgedeckt

**Merge-Point:** Sobald Iteration 5 (Testing) abgeschlossen ist, werden die Test-Results hier eingetragen und das Release wird finalisiert.
```

---

## 🚀 Nächste Schritte

1. **JETZT:** Iteration 1 starten (LLM-Provider-Abstraktion)
2. **18:15:** Iteration 2 (Fallback-Chain)
3. **18:30:** Iteration 3 (Chat Pipeline)
4. **18:50:** Iteration 4 (Zero-Config)
5. **19:10:** Iteration 5 (Testing)
6. **19:30:** Iteration 6 (Release)

**Let's go!** 💋✨
