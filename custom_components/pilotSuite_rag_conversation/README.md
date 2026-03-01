# PilotSuite RAG Conversation für HomeAssistant

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/pilotsuite/pilotsuite-styx-core)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![HomeAssistant](https://img.shields.io/badge/HomeAssistant-custom-blue.svg)](https://www.home-assistant.io/)

## 🎯 Übersicht

Die **PilotSuite RAG Conversation** Integration erweitert HomeAssistant um kontextuelle Antworten mittels RAG-API (Retrieval-Augmented Generation).

### Features

- ✅ **RAG-API Integration** - Nutzt lokale Wissensdatenbank (HA-States, Dokumente, History)
- ✅ **OpenAI LLM** - Hochwertige Antwortgenerierung mit GPT-4/GPT-3.5
- ✅ **Web-Suche optional** - SearXNG-Integration für Web-Kontext (privacy-fokussiert)
- ✅ **Conversation History** - Session-basiertes Gedächtnis für kontextuelle Gespräche
- ✅ **Einfache Konfiguration** - YAML oder UI-ConfigFlow

## 📋 Voraussetzungen

- **HomeAssistant** 2023.10 oder höher
- **Python** 3.10 oder höher
- **RAG-API** (PilotSuite RAG-System) muss laufen
- **OpenAI API Key** (für LLM-Inferenz)

## 🚀 Installation

### Option A: Manuelles Copy

1. **Component kopieren:**
   ```bash
   cp -r custom_components/pilotSuite_rag_conversation /config/custom_components/
   ```

2. **HomeAssistant neustarten:**
   ```bash
   # Über HomeAssistant UI: Einstellungen → System → Neustart
   # ODER per SSH:
   ha core restart
   ```

3. **Integration konfigurieren** (siehe unten)

### Option B: HACS (Custom Repository)

```bash
# HACS Repository hinzufügen
ha addons install hacs
# Dann über HACS UI: Custom Repositories → pilotSuite/pilotsuite-styx-core
```

## ⚙️ Konfiguration

### YAML-Konfiguration (configuration.yaml)

```yaml
conversation:
  - platform: pilotSuite_rag_conversation
    rag_api_url: http://localhost:8765
    openai_api_key: !secret openai_api_key
    model: gpt-4
    use_web_search: false  # Standard: keine Web-Suche
```

**Parameter:**

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|----------|--------------|
| `rag_api_url` | string | `http://localhost:8765` | URL der RAG-API |
| `openai_api_key` | string | **erforderlich** | OpenAI API Key |
| `model` | string | `gpt-4` | OpenAI Model (gpt-4, gpt-4-turbo, gpt-4o, gpt-3.5-turbo) |
| `use_web_search` | boolean | `false` | Web-Suche (SearXNG) aktivieren |

### UI-Konfiguration (ConfigFlow)

1. **HomeAssistant UI:** Einstellungen → Geräte & Dienste
2. **Integration hinzufügen:** `+` unten rechts
3. **Suchen:** "PilotSuite RAG Conversation"
4. **Konfigurieren:**
   - RAG-API URL (Standard: `http://localhost:8765`)
   - OpenAI API Key
5. **Optionen** (nach Einrichtung):
   - Model auswählen
   - Web-Suche aktivieren/deaktivieren

### Secrets (empfohlen)

```yaml
# /config/secrets.yaml
openai_api_key: sk-your-openai-api-key-here
```

```yaml
# configuration.yaml
conversation:
  - platform: pilotSuite_rag_conversation
    rag_api_url: http://localhost:8765
    openai_api_key: !secret openai_api_key
```

## 🧪 Nutzung

### Conversation Entities

Nach der Installation steht eine **Conversation Entity** zur Verfügung:

```yaml
# Beispiel: Sprachsteuerung über Piper + conversation
intent_script:
  ask_energy:
    speech: "Wie war der Energieverbrauch?"
    action:
      service: conversation.process
      data:
        agent_id: conversation.pilotSuite_rag_conversation
        text: "Wie war der Energieverbrauch gestern?"
```

### Direkt über Service

```yaml
service: conversation.process
data:
  agent_id: conversation.pilotSuite_rag_conversation
  text: "Welche Geräte sind im Wohnzimmer?"
```

### Sprachassistenten

Die Integration funktioniert mit allen HomeAssistant Sprachassistenten:

- **Assist** (offizieller HA Voice Assistant)
- **Rhasspy**
- **Piper**
- **Alexa/Google** (über HA-Integrationen)

## 🔧 Services

### `pilotSuite_rag_conversation.search_rag`

Manuelle RAG-Suche (für Testing/Debugging):

```yaml
service: pilotSuite_rag_conversation.search_rag
data:
  query: "Energieverbrauch letzte Woche"
  use_web: false
```

### `pilotSuite_rag_conversation.get_conversation_history`

History einer Konversation abrufen:

```yaml
service: pilotSuite_rag_conversation.get_conversation_history
data:
  conversation_id: "default-conversation"
```

### `pilotSuite_rag_conversation.clear_conversation_history`

History löschen:

```yaml
service: pilotSuite_rag_conversation.clear_conversation_history
data:
  conversation_id: "default-conversation"
```

## 🧠 Architektur

```
┌─────────────────────────────────────────────────────────┐
│              User Query (HomeAssistant)                 │
│        "Wie war der Energieverbrauch gestern?"          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│         PilotSuite RAG Conversation Component           │
│                                                         │
│  1. RAG-Suche (lokaler Kontext)                         │
│     → /api/rag/search (BM25 + Semantic + RRF)           │
│                                                         │
│  2. Prompt-Building mit RAG-Kontext                     │
│     → "Basierend auf: {rag_results}\nFrage: {query}"    │
│                                                         │
│  3. OpenAI-Inferenz                                     │
│     → GPT-4/GPT-3.5 für Antwort-Generierung             │
│                                                         │
│  4. History-Update                                      │
│     → Session-basiertes Gedächtnis                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              HomeAssistant Response                     │
│  "Der Energieverbrauch gestern betrug 15.3 kWh."        │
└─────────────────────────────────────────────────────────┘
```

### Daten-Quellen (RAG-API)

Die RAG-API durchsucht:

- **HA-States** (Gerätezustände, Sensoren, Automationen)
- **Dokumente** (PDFs, Markdown, Notizen)
- **History** (Chat-Verlauf, Logs)
- **Optional: Web** (SearXNG für öffentliche Informationen)

## 🧪 Tests

### Unit Tests ausführen

```bash
cd /config/custom_components/pilotSuite_rag_conversation
pytest test_init.py -v
```

### Test-Coverage

```bash
pytest test_init.py --cov=pilotSuite_rag_conversation --cov-report=html
```

### Manuelle Tests

1. **RAG-Suche testen:**
   ```yaml
   service: pilotSuite_rag_conversation.search_rag
   data:
     query: "Test query"
   ```

2. **Conversation testen:**
   ```yaml
   service: conversation.process
   data:
     agent_id: conversation.pilotSuite_rag_conversation
     text: "Wie ist das Wetter?"
   ```

## 🔐 Security & Privacy

### Privacy-Modi

| Modus | Beschreibung | Privacy |
|-------|--------------|---------|
| **Nur Lokal** | RAG-API durchsucht nur HA-Daten | ✅ 100% lokal |
| **Hybrid** | RAG-API + SearXNG (Web) | ⚠️ Web-Query erforderlich |
| **Nur Web** | Nur SearXNG (nicht empfohlen) | ⚠️ Web-Query erforderlich |

### Empfehlungen

1. **API Keys in secrets.yaml** speichern (nicht im Git!)
2. **Web-Suche nur bei Bedarf** aktivieren (`use_web_search: false`)
3. **RAG-API lokal betreiben** (localhost oder internes Netzwerk)
4. **HTTPS für RAG-API** bei externem Zugriff

## 🐛 Troubleshooting

### "RAG-API unreachable"

- **Prüfen:** Läuft die RAG-API?
  ```bash
  curl http://localhost:8765/health
  ```
- **Lösung:** RAG-API starten oder URL korrigieren

### "OpenAI API error"

- **Prüfen:** Ist der API Key korrekt?
  ```bash
  curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"
  ```
- **Lösung:** API Key in secrets.yaml aktualisieren

### "Timeout during RAG search"

- **Ursache:** RAG-API zu langsam oder überlastet
- **Lösung:**
  - RAG-API Performance optimieren
  - Timeout erhöhen (in `__init__.py` anpassen)
  - Caching aktivieren

### "Keine kontextuellen Informationen gefunden"

- **Ursache:** RAG-API hat keine passenden Ergebnisse
- **Lösung:**
  - Query umformulieren
  - RAG-API Datenquellen prüfen (Indizierung?)
  - Web-Suche aktivieren (`use_web_search: true`)

## 📚 Weiterführende Links

- [RAG-Architektur-Dokumentation](docs/RAG_ARCHITECTUR.md)
- [HomeAssistant Conversation API](https://developers.home-assistant.io/docs/voice/intent-recognition/conversation/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [SearXNG Documentation](https://docs.searxng.org/)

## 🤝 Support

- **Issues:** [GitHub Issues](https://github.com/pilotsuite/pilotsuite-styx-core/issues)
- **Discussions:** [GitHub Discussions](https://github.com/pilotsuite/pilotsuite-styx-core/discussions)
- **Dokumentation:** [PilotSuite Docs](https://pilotsuite.com/docs)

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE)

---

**Version:** 1.0.0  
**Erstellt:** 1. März 2026  
**Autor:** PilotSuite Team
