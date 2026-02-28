# Claude Code CLI vs Codex CLI vs OpenClaw coding-agent

**Erstellt:** 28. Februar 2026  
**Recherche-Tiefe:** Feature-Vergleich, Reasoning-Level, Integration

---

## Executive Summary

| Tool | Typ | Zielgruppe | Reasoning-Level |
|------|-----|------------|-----------------|
| **Claude Code** | Agentic CLI von Anthropic | Entwickler, die tief im Codebase arbeiten | Claude 3.7/3.5 Sonnet (starkes Reasoning) |
| **Codex CLI** | Coding Agent von OpenAI | ChatGPT-Abonnenten, OpenAI-Ökosystem | GPT-5.3-Codex / GPT-5.2-Codex (höchstes Coding-Reasoning) |
| **OpenClaw coding-agent** | Orchestrator-Skill | OpenClaw-Nutzer mit Multi-Agent-Setup | Variabel (abhängig von gewähltem Backend) |

---

## 1. Claude Code CLI

### Features
- **Terminal-native:** Läuft direkt im Terminal, IDE, Desktop-App oder Browser
- **Codebase-Understanding:** Versteht gesamte Codebases, arbeitet über mehrere Dateien hinweg
- **Git-Integration:** Erstellt Commits, Branches, Pull Requests automatisch
- **MCP-Support:** Model Context Protocol für externe Tools (Google Drive, Jira, Slack, etc.)
- **Sandboxing:** Standardmäßig read-only, explizite Genehmigung für Schreibzugriff
- **CLAUDE.md:** Projekt-spezifische Konfigurationsdatei für Custom Instructions
- **Plugins:** Erweiterbar mit Custom Commands und Agents

### Reasoning-Level
- **Modell:** Claude 3.7 Sonnet / Claude 3.5 Sonnet
- **Stärken:** 
  - Exzellentes Code-Understanding und Erklärung
  - Starke Refactoring-Fähigkeiten
  - Gute Balance zwischen Geschwindigkeit und Tiefe
- **Schwächen:**
  - Weniger spezialisiert auf reine Coding-Tasks als Codex

### Sicherheit
- **Sandbox:** Filesystem- und Network-Isolation für bash-Kommandos
- **Permissions:** Explizite Genehmigung für sensible Operationen
- **Prompt-Injection-Schutz:** Command-Blocklist, Input-Sanitization, isolierte Context-Windows

### Integration
- **Installation:** `curl -fsSL https://claude.ai/install.sh | bash` (macOS/Linux)
- **IDE-Support:** VS Code, JetBrains (IntelliJ, PyCharm, WebStorm)
- **Desktop-App:** Standalone für macOS, Windows
- **Web:** Browser-basiert ohne lokale Installation
- **Auth:** Claude Subscription oder Anthropic Console Account

---

## 2. OpenAI Codex CLI

### Features
- **Lokaler Agent:** Läuft auf dem eigenen Rechner, keine Cloud-Pflicht
- **Model-Auswahl:** Konfigurierbar über `~/.codex/config.toml`
- **Sandbox-Modi:** 
  - `read-only` – Nur Lesen
  - `workspace-write` – Schreiben im Workspace (Default)
  - `danger-full-access` – Vollzugriff (nicht empfohlen)
- **Approval-Policies:** `on-request`, `untrusted`, `never`
- **Web-Search:** Cached (Default) oder Live-Suche
- **Undo-Funktion:** Per-Turn Git-Ghost-Snapshots
- **Multi-Agent:** Experimenteller Multi-Agent-Support

### Reasoning-Level
- **Modelle:**
  - `gpt-5.3-codex` – Aktuellstes, stärkstes Coding-Modell
  - `gpt-5.3-codex-spark` – Research Preview, extrem schnell (ChatGPT Pro)
  - `gpt-5.2-codex` – Vorgänger, immer noch stark
  - `gpt-5.1-codex-max` – Für lange Horizon-Agentic-Tasks
- **Stärken:**
  - **Höchstes Coding-Reasoning** der Branche (Stand 2026)
  - Spezialisiert auf lange, agentic Coding-Sessions
  - Exzellente Debugging- und Fix-Fähigkeiten
- **Schwächen:**
  - Benötigt Git-Repo zum Starten
  - Komplexere Konfiguration

### Sicherheit
- **OS-Sandbox:** Seatbelt (macOS), Landlock+seccomp (Linux), Windows Sandbox
- **Protected Paths:** `/.git`, `/.codex`, `/.agents` read-only geschützt
- **Network:** Standardmäßig deaktiviert, explizit aktivierbar
- **Managed Configuration:** Organizations können Policies erzwingen (`requirements.toml`)

### Integration
- **Installation:** 
  - `npm install -g @openai/codex`
  - `brew install --cask codex` (macOS)
- **IDE-Support:** VS Code, Cursor, Windsurf
- **Desktop-App:** `codex app` oder chatgpt.com/codex
- **Auth:** ChatGPT-Login (Plus, Pro, Team, Edu, Enterprise) oder API-Key
- **Konfiguration:** `~/.codex/config.toml` + projekt-spezifisch `.codex/config.toml`

---

## 3. OpenClaw coding-agent Skill

### Features
- **Multi-Backend:** Unterstützt Codex, Claude Code, Pi, OpenCode
- **Bash-First:** Alle Agents laufen via `exec` mit `pty:true`
- **Background-Mode:** Lange Tasks im Hintergrund mit Session-Tracking
- **Process-Management:** `process`-Tool für Log, Poll, Write, Kill
- **Parallelisierung:** Mehrere Agents gleichzeitig (z.B. für Batch-PR-Reviews)
- **Git-Worktrees:** Parallele Issue-Fixes in isolierten Worktrees
- **Auto-Notify:** Wake-Trigger bei Completion via `openclaw system event`

### Reasoning-Level
- **Variabel:** Hängt vom gewählten Backend ab
  - **Codex:** GPT-5.2-Codex (Default in OpenClaw)
  - **Claude Code:** Claude 3.7/3.5 Sonnet
  - **Pi:** Konfigurierbar (OpenAI, Anthropic, etc.)
- **Stärken:**
  - **Flexibilität:** Wechsel zwischen Agents je nach Task
  - **Orchestrierung:** Koordination mehrerer Agents
  - **OpenClaw-Integration:** Nahtlose Einbindung in Messaging, Notifications, Skills
- **Schwächen:**
  - Kein eigenes Reasoning-Modell (nur Wrapper)
  - Komplexität durch Multi-Agent-Setup

### Sicherheit
- **PTY-Erforderlich:** Alle Agents brauchen `pty:true` für korrekte Ausgabe
- **Workspace-Beschränkung:** 
  - **NIEMALS** in `~/.openclaw/` starten (liest Soul-Docs!)
  - **NIEMALS** in `~/Projects/openclaw/` Branches checken (Live-Instanz!)
- **Temp-Repos:** Für PR-Reviews in Temp-Dir oder Git-Worktree klonen
- **Sandbox:** Abhängig vom Backend (Codex/Claude eigene Sandboxes)

### Integration
- **Voraussetzungen:** 
  - `claude`, `codex`, `opencode`, oder `pi` CLI installiert
  - Bash-Tool mit `pty:true` Support
- **Skill-Pfad:** `~/.openclaw/skills/coding-agent/SKILL.md`
- **Auth:** Abhängig vom Backend (siehe oben)
- **OpenClaw-Features:**
  - WhatsApp/Telegram-Benachrichtigungen
  - Subagent-Spawning für komplexe Tasks
  - Session-Logs für Analyse

---

## Direkter Vergleich

| Kriterium | Claude Code | Codex CLI | OpenClaw coding-agent |
|-----------|-------------|-----------|----------------------|
| **Reasoning (Coding)** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ (Backend-abhängig) |
| **Reasoning (Allgemein)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ (Backend-abhängig) |
| **Geschwindigkeit** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (spark) | ⭐⭐⭐ (Overhead) |
| **Sicherheit** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ (Backend-abhängig) |
| **Flexibilität** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **IDE-Integration** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ (Terminal-only) |
| **Multi-Agent** | ❌ | ⚠️ (experimentell) | ✅ (nativ) |
| **OpenClaw-Integration** | ❌ | ❌ | ✅ (nativ) |
| **Kosten** | Claude Subscription | ChatGPT Subscription | Backend-abhängig |

---

## Empfehlungen

### Für einzelne Coding-Tasks
**→ Codex CLI** mit `gpt-5.3-codex`
- Höchstes Coding-Reasoning
- Schnellste Ausführung
- Beste Security-Sandbox

### Für Codebase-Exploration & Refactoring
**→ Claude Code**
- Besseres allgemeines Understanding
- Stärker bei Erklärungen
- Bessere IDE-Integration

### Für OpenClaw-Nutzer
**→ OpenClaw coding-agent**
- **Vorteile:**
  - Nahtlose Integration in OpenClaw-Ökosystem
  - Multi-Agent-Orchestrierung (parallele PR-Reviews, Batch-Issue-Fixes)
  - Auto-Notify bei Completion
  - Einheitliches Interface für alle Agents
- **Empfohlenes Backend:** Codex CLI (`gpt-5.2-codex` oder `gpt-5.3-codex` wenn verfügbar)
- **Use-Cases:**
  - Batch-PR-Reviews mit parallelen Agents
  - Multi-Issue-Fixing mit Git-Worktrees
  - Lange Background-Tasks mit WhatsApp-Notification

### Für Enterprise/Teams
**→ Codex CLI mit Managed Configuration**
- Admin-enforced Requirements (`requirements.toml`)
- Zentrale Policy-Steuerung
- Audit-Logging

---

## Setup-Empfehlung für OpenClaw

```bash
# 1. Codex CLI installieren
npm install -g @openai/codex

# 2. Config anpassen (~/.codex/config.toml)
model = "gpt-5.3-codex"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
web_search = "cached"

# 3. coding-agent Skill nutzen
bash pty:true workdir:~/project command:"codex exec --full-auto 'Feature implementieren'"

# 4. Für lange Tasks im Background
bash pty:true workdir:~/project background:true command:"codex exec 'Großes Refactoring'"
# → sessionId tracken mit process-Tool
# → Auto-Notify am Ende: openclaw system event --text "Done: ..." --mode now
```

---

## Fazit

**Codex CLI** ist der aktuelle König für reines Coding-Reasoning (GPT-5.3-Codex).  
**Claude Code** glänzt bei allgemeinem Codebase-Understanding und IDE-Integration.  
**OpenClaw coding-agent** ist die beste Wahl für OpenClaw-Nutzer, die Multi-Agent-Orchestrierung und nahtlose Integration brauchen.

**Hybrid-Ansatz empfohlen:** OpenClaw coding-agent als Orchestrator, mit Codex CLI als primärem Backend für Coding-Tasks und Claude Code für komplexe Codebase-Analysen.

---

*Bericht erstellt von Subagent (Label: claude-code-research)*  
*Quellen: GitHub Repos, offizielle Dokumentation (code.claude.com, developers.openai.com/codex), OpenClaw Skills*
