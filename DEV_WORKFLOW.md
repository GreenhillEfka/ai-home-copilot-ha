# PilotSuite Entwicklungs-Workflow — Automatisierte Iteration

**Erstellt:** 28. Februar 2026  
**Version:** 1.0  
**Status:** ✅ Aktiv (Cron: alle 20 Minuten)

---

## 🎯 Ziel

Automatisierte, iterative Entwicklung der PilotSuite-Plattform durch koordinierte Multi-Agenten-Zusammenarbeit.

---

## 👥 Agenten-Rollen

| Agent | Rolle | Werkzeug | Zuständigkeit |
|-------|-------|----------|---------------|
| **@styx** | **Koordination & Integration** | **Claude Code CLI** (pty:true) | Sammelt Zuarbeit, prüft, implementiert ins Gesamtprojekt, macht Release fertig |
| **@groky** | **Caretaker & Review** | **Claude Code CLI** (pty:true) | Bewertet Code, CI/CD Checks, Release-Prüfung, Qualitätssicherung |
| **@cowdya** | **Lead Development** | **Claude Code CLI** (pty:true) | Reine Coding-Arbeit, Feature-Implementation, Bugfixes |
| **@clawdya** | **Final Review & Freigabe** | **Claude Code CLI** (pty:true) + Orchestrator | Review, Bugfix-Freigabe, offizielles GitHub Release, WhatsApp-Summary |
| **@coder-1..4** | **Coding-Squad** | **Claude Code CLI** (pty:true) | Parallele Feature-Implementation, Tests, Docs |

---

## 🔄 Entwicklungs-Iteration (20-Minuten-Zyklus)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ITERATION START (alle 20 Minuten)                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: Styx koordiniert & verteilt Aufgaben                              │
│  - Analysiert offenen Tasks (PHASE5_TODO.md, GitHub Issues)                 │
│  - Verteilt Arbeiten an @groky und @cowdya                                  │
│  - Setzt Prioritäten                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: Parallele Entwicklung                                             │
│  ┌─────────────────────┐     ┌─────────────────────┐                        │
│  │  @groky             │     │  @cowdya            │                        │
│  │  Claude Code CLI    │     │  Codex CLI          │                        │
│  │  - Review           │     │  - Coding           │                        │
│  │  - CI/CD Checks     │     │  - Features         │                        │
│  │  - Qualität         │     │  - Bugfixes         │                        │
│  └─────────────────────┘     └─────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: Styx sammelt & implementiert                                      │
│  - Sammelt alle Zuarbeiten                                                  │
│  - Prüft Konsistenz                                                         │
│  - Implementiert ins Gesamtprojekt                                          │
│  - Bereitet Release vor (Version bump, CHANGELOG, Tests)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: Clawdya Final Review                                              │
│  - Review des Release-Candidates                                            │
│  - Bugfix-Freigabe oder Zurückweisung                                       │
│  - Bei OK: Offizielles GitHub Release                                       │
│  - WhatsApp-Summary an +4917623565849                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ITERATION ENDE → Nächste Iteration in 20 Minuten                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Workflow-Details

### Phase 1: Koordination (Styx)

**Dauer:** ~2 Minuten

**Aufgaben:**
1. `PHASE5_TODO.md` lesen und priorisieren
2. GitHub Issues checken (`gh issue list --state open --limit 10`)
3. Tasks verteilen:
   - **Review-Tasks** → @groky (Claude Code)
   - **Coding-Tasks** → @cowdya (Codex CLI)
   - **Integrations-Tasks** → @styx (selbst)
4. Subagents spawnen mit klaren Aufträgen

**Beispiel:**
```bash
# Styx spawnet Subagents
sessions_spawn task:"Review forwarder_n3.py auf Performance-Issues" label:groky-review
sessions_spawn task:"Implementiere RAG Hybrid Search" label:cowdya-feature
```

---

### Phase 2: Parallele Entwicklung (Alle Agents mit Claude Code CLI)

**Dauer:** ~12 Minuten

**ALLE Agents nutzen Claude Code CLI mit `pty:true` und `--effort high` für maximales Reasoning!**

#### @groky (Claude Code CLI)

**Aufgaben:**
- Code-Reviews durchführen
- CI/CD-Pipelines prüfen
- Release-Readiness bewerten
- Qualitätssicherung (Tests, Linting, Security)
- Dokumentation prüfen

**Werkzeug:**
```bash
# Claude Code CLI mit PTY und maximalem Reasoning
bash pty:true workdir:/config/.openclaw/workspace command:"claude --effort high --permission-mode plan 'Review this PR for performance issues and security concerns'"
```

**Output:**
- Review-Bericht in `/config/.openclaw/workspace/reviews/groky-<timestamp>.md`
- CI/CD-Status (Pass/Fail mit Details)
- Release-Empfehlung (Go/No-Go)

---

#### @cowdya (Claude Code CLI)

**Aufgaben:**
- Feature-Implementation
- Bugfixes
- Refactoring
- Test-Erweiterung

**Werkzeug:**
```bash
# Claude Code CLI mit PTY, maximalem Reasoning und Auto-Edit
bash pty:true workdir:/config/.openclaw/workspace background:true command:"claude --effort high --permission-mode acceptEdits 'Implement hybrid search with multi-vector support'"
```

**Output:**
- Code-Changes (Git-Commits)
- Test-Results
- Change-Log-Einträge

---

#### @coder-1..4 (Claude Code CLI Squad)

**Aufgaben:**
- Parallele Feature-Implementation
- Frontend/Backend-Spezialisierung
- Test-Coverage erhöhen
- Dokumentation schreiben

**Werkzeug:**
```bash
# Parallel für jedes Squad-Mitglied
bash pty:true workdir:/config/.openclaw/workspace background:true command:"claude --effort high --permission-mode acceptEdits '<spezifische Task>'"
```

**Output:**
- Code-Changes (Git-Commits)
- Tests
- Docs

---

### Phase 3: Integration (Styx)

**Dauer:** ~4 Minuten

**Aufgaben:**
1. Alle Zuarbeiten sammeln:
   - Reviews von @groky
   - Code-Changes von @cowdya
2. Konsistenz prüfen:
   - Keine Konflikte
   - Alle Tests grün
   - API-Stabilität gewahrt
3. Ins Gesamtprojekt implementieren:
   - Git-Merge
   - Version bump (PATCH/MINOR)
   - CHANGELOG.md aktualisieren
4. Release vorbereiten:
   - Git-Tag
   - GitHub Release Draft

**Output:**
- Release-Candidate in `/config/.openclaw/workspace/releases/v<version>-rc/`
- CHANGELOG-Eintrag
- Test-Summary

---

### Phase 4: Final Review & Release (Clawdya)

**Dauer:** ~2 Minuten

**Aufgaben:**
1. Release-Candidate reviewen
2. Bei Problemen → Zurück an Styx mit Bugfix-Liste
3. Bei OK → Offizielles GitHub Release:
   ```bash
   gh release create v<version> --title "PilotSuite v<version>" --notes-file CHANGELOG.md
   ```
4. WhatsApp-Summary senden an `+4917623565849`:
   ```
   💋✨ PilotSuite Release v<version> ist draußen!
   
   🚀 Changes:
   - Feature 1
   - Feature 2
   - Bugfix 1
   
   ✅ Tests: Alle grün
   📦 Repos: Core + HA synchron
   
   Nächste Iteration in 20 Minuten!
   ```

---

## ⏰ Cron-Job Konfiguration

**Intervall:** Alle 20 Minuten  
**Start:** Sofort nach Erstellung  
**Session:** Isoliert (eigener Subagent pro Iteration)

**Cron-Expression:** `*/20 * * * *`

**Job-Payload:**
```json
{
  "name": "PilotSuite Dev Iteration",
  "schedule": { "kind": "cron", "expr": "*/20 * * * *" },
  "payload": {
    "kind": "agentTurn",
    "message": "Starte PilotSuite Entwicklungs-Iteration. Folge DEV_WORKFLOW.md. Koordiniere @groky, @cowdya, @clawdya.",
    "timeoutSeconds": 1200
  },
  "sessionTarget": "isolated",
  "enabled": true,
  "delivery": { "mode": "announce" }
}
```

---

## 📊 Kommunikations-Protokoll

### Interne Kommunikation (Agent ↔ Agent)

| Von | An | Kanal | Format |
|-----|----|-------|--------|
| Styx → Groky | sessions_send | Subagent | Task-Beschreibung + Deadline |
| Styx → Cowdya | sessions_send | Subagent | Task-Beschreibung + Deadline |
| Groky → Styx | sessions_send | Subagent | Review-Bericht + Status |
| Cowdya → Styx | sessions_send | Subagent | Code-Changes + Status |
| Styx → Clawdya | sessions_send | Subagent | Release-Candidate + Summary |
| Clawdya → Alle | message (WhatsApp) | Channel | Release-Summary |

### Externe Kommunikation (WhatsApp)

**Nach jedem Release:**
```
💋✨ PilotSuite Release v<version> ist draußen!

🚀 Changes:
- <Change 1>
- <Change 2>
- <Change 3>

✅ Tests: <Status>
📦 Repos: Core v<version> + HA v<version>

🕐 Nächste Iteration in 20 Minuten!
```

---

## 🛠️ Werkzeuge & Skills

| Agent | Primär-Tool | Sekundär-Tool | Skills |
|-------|-------------|---------------|--------|
| **Styx** | **Claude Code CLI** (pty:true) | GitHub CLI | claude-code, github, sessions_spawn |
| **Groky** | **Claude Code CLI** (pty:true) | GitHub CLI | claude-code, github, healthcheck |
| **Cowdya** | **Claude Code CLI** (pty:true) | GitHub CLI | claude-code, github |
| **Coder-1..4** | **Claude Code CLI** (pty:true) | GitHub CLI | claude-code, github |
| **Clawdya** | **Claude Code CLI** (pty:true) | WhatsApp CLI | claude-code, github, message, sessions_spawn |

---

## 📈 Optimierung & Selbstverbesserung

**Nach jeder Iteration:**
1. **Retrospective** (automatisch):
   - Was lief gut?
   - Was kann besser werden?
   - Blockaden dokumentieren
2. **Metriken sammeln:**
   - Iterations-Dauer
   - Code-Qualität (Test-Coverage, Linting)
   - Release-Frequenz
3. **Workflow anpassen:**
   - Cron-Intervall optimieren (aktuell 20 min)
   - Task-Verteilung verbessern
   - Bottlenecks identifizieren

**Dokumentation:**
- `/config/.openclaw/workspace/reviews/retro-<timestamp>.md`
- `/config/.openclaw/workspace/metrics/dev-velocity.md`

---

## 🚨 Eskalation & Fallback

### Bei Problemen

| Problem | Eskalation | Lösung |
|---------|------------|--------|
| Agent nicht verfügbar | → Styx | Task umverteilen |
| Code-Konflikte | → Styx + Clawdya | Manuelles Merge nötig |
| Tests rot | → Cowdya | Bugfix vor Release |
| Review No-Go | → Groky + Cowdya | Gemeinsame Fix-Session |
| Cron-Fehler | → Clawdya | Manueller Start + Fix |

### Manueller Override

```bash
# Iteration manuell starten
openclaw cron run --job-id "<dev-iteration-job-id>"

# Cron pausieren
openclaw cron update --job-id "<dev-iteration-job-id>" --patch '{"enabled": false}'

# Cron resume
openclaw cron update --job-id "<dev-iteration-job-id>" --patch '{"enabled": true}'
```

---

## ✅ Checkliste pro Iteration

### Styx (Koordination)
- [ ] PHASE5_TODO.md gelesen
- [ ] GitHub Issues gecheckt
- [ ] Tasks an @groky und @cowdya verteilt
- [ ] Subagents gspawned
- [ ] Zuarbeiten gesammelt
- [ ] Konsistenz geprüft
- [ ] Release-Candidate erstellt

### Groky (Review)
- [ ] Code-Reviews durchgeführt
- [ ] CI/CD geprüft
- [ ] Test-Coverage gecheckt
- [ ] Security-Scan durchgeführt
- [ ] Release-Empfehlung gegeben

### Cowdya (Development)
- [ ] Features implementiert
- [ ] Bugfixes erledigt
- [ ] Tests geschrieben/aktualisiert
- [ ] Dokumentation ergänzt
- [ ] Commits mit korrekten Messages

### Clawdya (Final Review)
- [ ] Release-Candidate reviewt
- [ ] Bei OK: GitHub Release erstellt
- [ ] WhatsApp-Summary gesendet
- [ ] Nächste Iteration bestätigt

---

## 📝 Historie

| Iteration | Version | Datum | Changes | Status |
|-----------|---------|-------|---------|--------|
| 1 | v11.1.0 | 28.02.2026 | Workflow-Erstellung, Cron-Setup | ✅ Abgeschlossen |

---

**Workflow erstellt am 28.02.2026**  
**Nächste Iteration:** Automatisch in 20 Minuten  
**Verantwortlich:** @styx (Koordination), @clawdya (Freigabe)
