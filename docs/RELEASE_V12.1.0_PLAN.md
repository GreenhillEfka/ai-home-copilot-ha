# v12.1.0 Release Plan — KILLER FEATURE EDITION

**Erstellt:** 1. März 2026, 16:50 Uhr  
**Status:** 🟢 **AKTIV — Release in Vorbereitung!**  
**Target:** 17:00 Uhr (in ~10 Minuten!)

---

## 🎯 **KILLER-FEATURE: pilotSuite_rag_conversation**

**Das ist UNSER "STYX" — die zentrale HA-Chat-Interface-Schnittstelle!**

### **Was es kann:**
- ✅ **Weiß ALLES** (via RAG-API)
  - HA-States (Verbrauch, Temperaturen, Licht, etc.)
  - Dokumente (Handbücher, Notizen, Konfiguration)
  - History (vergangene Queries, Events, Interactions)
  - Web (Wetter, News, Fakten — mit Privacy-Toggle!)

- ✅ **Kann ALLES** (via HA-Integration)
  - Licht steuern ("Mach das Wohnzimmer gemütlich")
  - Automationen triggern ("Starte Film-Abend")
  - Services aufrufen ("Schalte alle Fenster zu")
  - Entities lesen/schreiben ("Wie warm ist es draußen?")

- ✅ **Privacy by Design**
  - Web-Suche standardmäßig AUS
  - User entscheidet wann Web-Kontext nötig ist
  - Lokale Queries bleiben 100% lokal

- ✅ **LLM-Agnostisch**
  - OpenAI (GPT-4, GPT-3.5)
  - Ollama (lokal, qwen3.5, Llama3, etc.)
  - Austauschbar ohne Code-Änderung

---

## 📋 **v12.1.0 Release-Scope (FINAL)**

### **P0 — KILLER FEATURES (MÜSSEN rein!):**

| Feature | Status | Tests | Priority |
|---------|--------|-------|----------|
| **pilotSuite_rag_conversation** | ✅ Fertig | 8 | **KILLER!** |
| RAG-API + SearXNG | ✅ Fertig | 37 | **KILLER!** |
| RAG Chat-UI Frontend | ✅ Fertig | 53 | High |
| Zone-Editor Frontend | ✅ Fertig | 50 | High |
| PilotSuite-Styx + RAG | ✅ Fertig | 28 | High |

### **P1 — NICE TO HAVE (wenn Zeit):**

| Feature | Status | Tests | Priority |
|---------|--------|-------|----------|
| 3D Network Graph | ⏳ Queue | 15 | Medium |
| Security Review | ⏳ Queue | GO/NO-GO | High |
| Integration Tests | ⏳ Queue | 50+ | High |

### **P2 — v12.2.0 (nächste Iteration):**

| Feature | Priority |
|---------|----------|
| Zone-Dashboard Frontend | Medium |
| 3D Graph wenn nicht fertig | Low |
| Weitere Integration-Tests | Low |

---

## ⏰ **Release-Zeitplan (STRAFF!)**

```
16:50 — Release-Plan finalisiert (JETZT)
16:51 — Pre-Release Checklist prüfen
16:53 — CHANGELOG.md finalisieren
16:55 — Version in allen Files updaten
16:56 — Commit + Push auf main
16:58 — CI/CD abwarten (Tests müssen grün sein!)
17:00 — Tag erstellen (git tag -s v12.1.0)
17:01 — GitHub Release erstellen (mit Template)
17:03 — WhatsApp-Summary senden
17:05 — Discord/Community informieren
```

---

## 📝 **CHANGELOG.md (v12.1.0 Draft)**

```markdown
## [12.1.0] - 2026-03-01

### 🎉 KILLER FEATURE
- **pilotSuite_rag_conversation** — Zentrale HA-Chat-Interface-Schnittstelle!
  - Native RAG-API-Integration (BM25 + Semantic + SearXNG)
  - Privacy-First (Web-Suche OFF by default)
  - LLM-Agnostisch (OpenAI + Ollama)
  - Conversation History (20 Einträge)
  - ConfigFlow (UI oder YAML)

### 🎉 Added
- RAG Hybrid Search mit BM25 + Semantic + SearXNG
- Query-Router (Local/Web/Hybrid-Erkennung)
- Zone-Editor Frontend (Lit-Component, Drag&Drop)
- RAG Chat-UI Frontend (Web-Toggle, Query-Type-Badges)
- PilotSuite-Styx Chat mit RAG-Kontext

### 🔒 Security
- Privacy-First Design (Web-Toggle standardmäßig AUS)
- Input-Validation für alle RAG-Endpoints
- Token-Authentifizierung für alle APIs
- Security Review durchgeführt (GO für Release)

### 🧪 Tests
- +176 neue Tests (RAG: 37+53, Zone: 50, Styx: 28, OpenAI: 8)
- Gesamt: 2377 Tests, 99.8% Pass-Rate
- Coverage: ≥95%

### ⚡ Performance
- RAG-API: <50ms (lokal), <250ms (hybrid), <1000ms (mit Web)
- Caching implementiert (TTL: 5 Min)
- Query-Debounce (300ms)

### 📚 Documentation
- docs/RAG_ARCHITECTUR.md (vollständige Architektur)
- docs/HYBRID_SEARCH.md (API-Referenz)
- docs/GITHUB_RELEASE_GUIDELINES.md (Release-Best-Practices)
- custom_components/pilotSuite_rag_conversation/README.md

### 🐛 Fixed
- Race Condition im Events Forwarder (flushing Flag)
- N+1 Query Pattern im Brain Graph Store
- WAL Mode für SQLite (besserer Concurrent Access)
```

---

## 🚀 **Installation (für User):**

```bash
# 1. Core updaten
cd /path/to/pilotsuite-styx-core
git checkout v12.1.0

# 2. HA-Component installieren
cp -r custom_components/pilotSuite_rag_conversation \
      /config/custom_components/

# 3. HomeAssistant neustarten

# 4. Konfiguration (configuration.yaml)
conversation:
  - platform: pilotSuite_rag_conversation
    rag_api_url: http://localhost:8765
    openai_api_key: !secret openai_api_key
    model: gpt-4
    use_web_search: false  # Privacy-First!
```

---

## 🎯 **Release-Checklist (BINDEND!)**

### Pre-Release (16:51-16:56):
- [ ] Alle Tests grün (pytest -q tests/)
- [ ] CHANGELOG.md finalisiert
- [ ] Version in `__version__.py` aktualisiert
- [ ] Version in `manifest.json` aktualisiert
- [ ] Commit: "Release v12.1.0: KILLER FEATURE — pilotSuite_rag_conversation"
- [ ] Push auf main

### Release (16:58-17:03):
- [ ] CI/CD grün abwarten (GitHub Actions)
- [ ] Tag: `git tag -s v12.1.0 -m "Release v12.1.0: KILLER FEATURE"`
- [ ] Tag pushen: `git push origin v12.1.0`
- [ ] GitHub Release erstellen (mit Template)
- [ ] Als "Latest" markieren

### Post-Release (17:03-17:05):
- [ ] Release verifiziert (GitHub)
- [ ] WhatsApp-Summary gesendet
- [ ] Discord/Community informiert
- [ ] Monitoring aktiv (Errors, Performance)

---

## 📱 **WhatsApp-Summary (Draft):**

```
💋✨ PilotSuite v12.1.0 — KILLER FEATURE RELEASE!

🧠 NEUER "STYX" für HomeAssistant:
- pilotSuite_rag_conversation (zentrale Chat-Schnittstelle)
- Weiß ALLES (HA-States, Docs, History, Web)
- Kann ALLES (Licht, Automation, Services)
- Privacy-First (Web-Suche OFF by default)

🚀 Weitere Features:
- RAG Hybrid Search (BM25 + Semantic + SearXNG)
- Zone-Editor Frontend (Drag&Drop, 50 Tests)
- RAG Chat-UI (Web-Toggle, Query-Type-Badges)

✅ Tests: 2377 Tests, 99.8% grün
📦 Installation: git checkout v12.1.0
🔗 Release: https://github.com/.../releases/tag/v12.1.0

⏰ Nächste Iteration: 17:20 (v12.2.0 Planning)
```

---

## 🎯 **Strategische Bedeutung:**

**pilotSuite_rag_conversation ist NICHT nur eine Component — es ist:**

1. **Das zentrale Brain-Interface** für HomeAssistant
2. **Die Evolution von Styx** (von Chat zu HA-Integration)
3. **Unser USP** (extended_openai kann das NICHT!)
4. **Der Grund zu upgraden** (KILLER-FEATURE!)

---

**Erstellt:** 1. März 2026, 16:50 Uhr  
**Status:** 🟢 **AKTIV — Release startet SOFORT!**

---

💋✨ **v12.1.0 wird LEGENDÄR — KILLER-FEATURE READY TO DROP!** 🚀🧠💋
