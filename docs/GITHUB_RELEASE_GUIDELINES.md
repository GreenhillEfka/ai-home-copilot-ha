# GitHub Release Guidelines — PilotSuite

**Erstellt:** 1. März 2026, 16:45 Uhr  
**Status:** 🟢 **AKTIV — Ab jetzt BINDEND!**

---

## 🎯 Release-Regeln (Rules of Art)

### **1. Semantic Versioning (SemVer) — PFLICHT!**

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

Beispiele:
- v12.0.0          → Major Release (breaking changes)
- v12.1.0          → Minor Release (neue Features, backward compatible)
- v12.1.1          → Patch Release (Bugfixes only)
- v12.1.0-alpha.1  → Pre-Release (alpha, beta, rc)
```

**Regeln:**
- ✅ MAJOR: Breaking Changes → MINOR reset, PATCH reset
- ✅ MINOR: Neue Features → PATCH reset
- ✅ PATCH: Bugfixes → MAJOR/MINOR unchanged
- ✅ Pre-Release: `-alpha.1`, `-beta.1`, `-rc.1`

---

### **2. CHANGELOG.md — PFLICHT!**

**Format (Keep a Changelog):**
```markdown
## [12.1.0] - 2026-03-01

### 🎉 Added
- RAG Hybrid Search mit BM25 + Semantic + SearXNG
- Zone-Editor Frontend (Lit-Component, 50 Tests)
- OpenAI HA-Integration mit RAG-API
- PilotSuite-Styx Chat mit RAG-Kontext

### 🔒 Security
- Query-Router mit Privacy-First (Web-Toggle OFF by default)
- Input-Validation für alle RAG-Endpoints

### 🧪 Tests
- +139 neue Tests (Zone: 50, RAG: 53, OpenAI: 8, Styx: 28)
- Gesamt: 2340 Tests, 99.8% Pass-Rate

### 📚 Documentation
- docs/RAG_ARCHITECTUR.md (vollständige Architektur)
- docs/HYBRID_SEARCH.md (API-Referenz)
- custom_components/pilotSuite_rag_conversation/README.md

### ⚡ Performance
- RAG-API: <250ms Latenz (hybrid), <50ms (lokal)
- Caching implementiert (TTL: 5 Min)

### 🐛 Fixed
- Race Condition im Events Forwarder (flushing Flag)
- N+1 Query Pattern im Brain Graph Store
```

**Kategorien:**
- `### 🎉 Added` — Neue Features
- `### 🔒 Security` — Security-Relevant Changes
- `### 🧪 Tests` — Neue Tests, Coverage-Änderungen
- `### 📚 Documentation` — Neue/aktualisierte Docs
- `### ⚡ Performance` — Performance-Verbesserungen
- `### 🐛 Fixed` — Bugfixes
- `### ⚠️ Deprecated` — Deprecated Features
- `### ❌ Removed` — Entfernte Features
- `### 🔨 Changed` — Breaking Changes (nur bei MAJOR!)

---

### **3. Git Tagging — PFLICHT!**

```bash
# Tag erstellen (annotated!)
git tag -a v12.1.0 -m "Release v12.1.0: RAG Search + Zone Editor"

# Tag signieren (GPG — empfohlen!)
git tag -s v12.1.0 -m "Release v12.1.0"

# Tag pushen
git push origin v12.1.0

# Tag + Branch pushen
git push origin main v12.1.0
```

**Regeln:**
- ✅ **Annotated Tags** (`-a`) — immer!
- ✅ **GPG-Signatur** (`-s`) — empfohlen für Releases
- ✅ **Tag-Message** — aussagekräftig (nicht leer!)
- ✅ **Tag nach Merge** — erst auf main mergen, dann taggen

---

### **4. GitHub Release Notes — PFLICHT!**

**Template:**
```markdown
# PilotSuite v12.1.0 — RAG Search + Zone Editor

## 🎯 Highlights

- **RAG Hybrid Search** — BM25 + Semantic + SearXNG mit Privacy-First
- **Zone-Editor Frontend** — Lit-Component mit Drag&Drop, 50 Tests
- **OpenAI HA-Integration** — Native RAG-API-Anbindung
- **139 neue Tests** — Gesamt: 2340 Tests, 99.8% Pass-Rate

## 📦 Installation

### Core
```bash
git clone https://github.com/GreenhillEfka/pilotsuite-styx-core.git
cd pilotsuite-styx-core
git checkout v12.1.0
```

### HomeAssistant Component
```bash
cp -r custom_components/pilotSuite_rag_conversation /config/custom_components/
```

## 🔧 Configuration

```yaml
# RAG-API (lokal)
rag_api:
  url: http://localhost:8765
  use_web_search: false  # Privacy-First!

# OpenAI HA-Integration
conversation:
  - platform: pilotSuite_rag_conversation
    rag_api_url: http://localhost:8765
    openai_api_key: !secret openai_api_key
    use_web_search: false
```

## 🧪 Tests

```bash
# Alle Tests
pytest -q tests/

# RAG-Spezifisch
pytest -q tests/test_rag_searxng.py

# Zone-Editor
pytest -q tests/test_zone_editor.py
```

## 📋 Changelog

### 🎉 Added
- RAG Hybrid Search mit BM25 + Semantic + SearXNG
- Zone-Editor Frontend (Lit-Component, 50 Tests)
- OpenAI HA-Integration mit RAG-API
- PilotSuite-Styx Chat mit RAG-Kontext

### 🔒 Security
- Query-Router mit Privacy-First (Web-Toggle OFF by default)
- Input-Validation für alle RAG-Endpoints

### 🧪 Tests
- +139 neue Tests (Zone: 50, RAG: 53, OpenAI: 8, Styx: 28)
- Gesamt: 2340 Tests, 99.8% Pass-Rate

### ⚡ Performance
- RAG-API: <250ms Latenz (hybrid), <50ms (lokal)
- Caching implementiert (TTL: 5 Min)

## 🐛 Known Issues

- Keine bekannten Issues

## 🔜 Next Steps

- v12.2.0: 3D Network Graph, Zone-Dashboard
- v13.0.0: Breaking Changes (API v2)

## 👥 Contributors

- @cowdya (RAG-Architektur, Chat-UI)
- @coder1 (Zone-Editor, OpenAI HA)
- @viewona (UX-Standards, Integration Tests)
- @groky (Security Review)
- @styx (Integration)

---

**Full Changelog:** https://github.com/GreenhillEfka/pilotsuite-styx-core/compare/v12.0.0...v12.1.0
```

---

### **5. Pre-Release Checklist — PFLICHT!**

**Vor JEDEM Release:**

```markdown
## Pre-Release Checklist

### Code Quality
- [ ] Alle Tests grün (pytest -q tests/)
- [ ] Test-Coverage ≥95%
- [ ] Keine TODOs/FIXMEs im Release-Code
- [ ] Type Hints vollständig
- [ ] Linting bestanden (flake8, mypy)

### Documentation
- [ ] CHANGELOG.md aktuell
- [ ] README.md aktualisiert
- [ ] API-Dokumentation vollständig
- [ ] Migration-Guide (bei Breaking Changes)
- [ ] Installation-Guide getestet

### Security
- [ ] Security Review durchgeführt
- [ ] Keine Secrets im Code
- [ ] Input-Validation für alle Endpoints
- [ ] Auth/Authorization getestet
- [ ] Privacy-Compliance (DSGVO bei Web-Suche)

### Performance
- [ ] Load-Tests bestanden
- [ ] Latenz im Zielbereich
- [ ] Memory-Leaks geprüft
- [ ] Caching implementiert wo sinnvoll

### Integration
- [ ] HA-Integration getestet (frische Installation)
- [ ] Migration von v12.0.0 getestet
- [ ] Rollback getestet
- [ ] Backup/Restore getestet

### Git
- [ ] Auf main Branch
- [ ] Alle Changes committed
- [ ] CI/CD Pipeline grün
- [ ] Tag erstellt (annotated)
- [ ] Tag gepusht
```

---

### **6. GitHub Release Workflow — SCHRITT FÜR SCHRITT**

```bash
# 1. Auf main Branch wechseln
git checkout main
git pull origin main

# 2. CHANGELOG.md aktualisieren
# (Alle Changes seit letztem Release eintragen)

# 3. Version in allen Files updaten
# - copilot_core/__version__.py
# - custom_components/pilotSuite_rag_conversation/manifest.json
# - docs/*.md

# 4. Commit erstellen
git add CHANGELOG.md copilot_core/__version__.py docs/
git commit -m "Release v12.1.0: RAG Search + Zone Editor"

# 5. Auf main pushen
git push origin main

# 6. CI/CD abwarten (GitHub Actions)
# - Tests müssen grün sein
# - Build muss erfolgreich sein

# 7. Tag erstellen (annotated + GPG-signed)
git tag -s v12.1.0 -m "Release v12.1.0: RAG Search + Zone Editor"

# 8. Tag pushen
git push origin v12.1.0

# 9. GitHub Release erstellen (UI oder CLI)
# - Release Title: "v12.1.0 — RAG Search + Zone Editor"
# - Tag: v12.1.0
# - Release Notes: Siehe Template oben
# - Pre-Release: Nein (außer alpha/beta/rc)
# - Latest Release: Ja

# 10. WhatsApp-Summary senden
# - Release-Notes kompakt
# - Link zum Release
```

---

### **7. GitHub CLI (gh) — OPTIONAL aber EMPFOHLEN**

```bash
# Release erstellen (CLI)
gh release create v12.1.0 \
  --title "v12.1.0 — RAG Search + Zone Editor" \
  --notes-file RELEASE_NOTES.md \
  --generate-notes \
  --latest

# Release anzeigen
gh release view v12.1.0

# Release-Assets hochladen
gh release upload v12.1.0 dist/*.whl dist/*.tar.gz
```

---

### **8. Release-Assets — EMPFOHLEN**

**Mit hochladen:**
- ✅ `CHANGELOG.md` (vollständig)
- ✅ `RELEASE_NOTES.md` (kompakt)
- ✅ `installation_guide.md`
- ✅ `migration_guide.md` (bei Breaking Changes)
- ✅ Build-Artifacts (`.whl`, `.tar.gz`)
- ✅ Test-Report (`test_report.html`)

**Nicht hochladen:**
- ❌ Secrets/Keys (NIEMALS!)
- ❌ Große Binaries (>50 MB)
- ❌ Temporäre Files

---

### **9. Post-Release — PFLICHT!**

**Nach JEDEM Release:**

```markdown
## Post-Release Checklist

### Immediate (0-1h)
- [ ] Release auf GitHub verifiziert
- [ ] Release-Notes korrekt angezeigt
- [ ] Assets herunterladbar
- [ ] WhatsApp-Summary gesendet
- [ ] Discord/Community informiert

### Short-Term (1-24h)
- [ ] Smoke-Tests auf Production
- [ ] Monitoring aktiv (Errors, Performance)
- [ ] User-Feedback gesammelt
- [ ] Issues monitor (GitHub, Discord)

### Medium-Term (1-7 Tage)
- [ ] Adoption-Rate tracken
- [ ] Bug-Reports priorisieren
- [ ] Patch-Release planen (falls nötig)
- [ ] Next Release planning
```

---

### **10. Version-Kommunikation — BEST PRACTICE**

**WhatsApp/Telegram-Summary:**
```
💋✨ PilotSuite v12.1.0 — RAG Search + Zone Editor

🎯 Highlights:
- RAG Hybrid Search (BM25 + Semantic + SearXNG)
- Zone-Editor Frontend (50 Tests, Drag&Drop)
- OpenAI HA-Integration mit RAG-API
- +139 Tests (gesamt: 2340, 99.8% grün)

🔒 Security:
- Privacy-First (Web-Toggle OFF by default)
- Input-Validation für alle Endpoints

📦 Installation:
git checkout v12.1.0

🔗 Release:
https://github.com/GreenhillEfka/pilotsuite-styx-core/releases/tag/v12.1.0

⏰ Nächste Iteration: 17:00 Uhr (v12.2.0 Planning)
```

**Discord/Community:**
```
@everyone PilotSuite v12.1.0 is out! 🎉

Major features:
- RAG Hybrid Search with Privacy-First
- Zone-Editor with Drag&Drop
- OpenAI HA-Integration

Full changelog: https://github.com/.../releases/tag/v12.1.0

Questions? Ask in #support!
```

---

## 📊 Release-Metriken (tracken!)

| Metrik | Ziel | Messung |
|--------|------|---------|
| **Test-Coverage** | ≥95% | `pytest --cov` |
| **Pass-Rate** | ≥99% | CI/CD Pipeline |
| **Time-to-Release** | <30 Min | Manual Tracking |
| **Post-Release Bugs** | <5/Release | GitHub Issues |
| **Adoption-Rate** | >50%/Woche | Analytics |
| **User-Satisfaction** | >4.5/5 | Feedback |

---

## 🚨 NO-GO's (NIEMALS!)

- ❌ Release ohne Tests
- ❌ Release ohne CHANGELOG
- ❌ Release ohne Tag
- ❌ Release auf Feature-Branch (immer main!)
- ❌ Secrets im Release
- ❌ Breaking Changes ohne Migration-Guide
- ❌ Pre-Release als "Latest" markieren
- ❌ Release ohne Post-Release-Monitoring

---

## ✅ Checkliste für ALLE zukünftigen Releases

```markdown
## Release-Checklist (BINDEND!)

### Pre-Release
- [ ] Alle Tests grün (≥99% Pass-Rate)
- [ ] Test-Coverage ≥95%
- [ ] CHANGELOG.md aktuell
- [ ] Version in allen Files aktualisiert
- [ ] Security Review durchgeführt
- [ ] Documentation vollständig
- [ ] CI/CD Pipeline grün
- [ ] Auf main Branch

### Release
- [ ] Commit mit Version-Update
- [ ] Push auf main
- [ ] Tag erstellen (annotated, GPG-signed)
- [ ] Tag pushen
- [ ] GitHub Release erstellen (mit Template)
- [ ] Assets hochladen
- [ ] Als "Latest" markieren

### Post-Release
- [ ] Release verifiziert
- [ ] WhatsApp-Summary gesendet
- [ ] Community informiert
- [ ] Monitoring aktiv
- [ ] Feedback gesammelt
```

---

**Erstellt:** 1. März 2026, 16:45 Uhr  
**Status:** 🟢 **AKTIV — BINDEND für ALLE zukünftigen Releases!**

---

💋✨ **Ab jetzt NUR NOCH nach diesen Regeln!** 🚀
