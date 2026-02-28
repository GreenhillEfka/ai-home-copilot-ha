# 🤖 openai-codex-operator Skill — Agenten-Guide

> **Verfügbar für:** Alle Agenten (Clawdya, Styx, Cowdya, Groky, Perplexya, Viewona)

---

## 📋 Was ist der Skill?

Der `openai-codex-operator` Skill ermöglicht es allen Agenten, **OpenAI Codex CLI** direkt aus OpenClaw zu nutzen — für Coding-Tasks, Code-Reviews, Debugging und Refactoring.

**Vorteile:**
- ✅ Nutzt ChatGPT Plus Auth (kein API-Guthaben nötig)
- ✅ Läuft lokal im Terminal
- ✅ Kann Code lesen, schreiben, testen
- ✅ Unterstützt Background-Tasks mit Monitoring

---

## 🎯 Wann soll ich Codex nutzen?

### ✅ **Nutze Codex bei:**

| Aufgabe | Beispiel-Prompt |
|---------|-----------------|
| **Neue Features implementieren** | "Implement a REST API endpoint for user login" |
| **Code Reviews** | "Review this PR and list critical issues" |
| **Bugs finden & fixen** | "Find the root cause of this failing test" |
| **Refactoring** | "Refactor this module to use async/await" |
| **Tests schreiben** | "Write unit tests for this function" |
| **Dokumentation generieren** | "Generate docstrings for all public methods" |
| **Code erklären** | "Explain what this regex does" |
| **Boilerplate erstellen** | "Create a Python FastAPI project structure" |

### ❌ **Nutze Codex NICHT bei:**

- Einfachen One-Liner Fixes (selber machen)
- Code nur lesen (nutze `read` Tool)
- Aufgaben im `~/clawd` Workspace (niemals Agents dort spawnen!)
- Wenn keine Codex CLI verfügbar ist (vorher `codex --version` prüfen)

---

## 🛠️ Wie rufe ich Codex auf?

### 1️⃣ **Einfache One-Shot Tasks** (foreground)

```bash
codex exec "<Aufgabe>" --sandbox workspace-write
```

**Beispiel:**
```bash
codex exec "Write a Python function that calculates fibonacci(n)" --sandbox workspace-write
```

**OpenClaw Tool-Call:**
```json
{
  "tool": "exec",
  "command": "codex exec \"Write a Python function...\" --sandbox workspace-write",
  "pty": true,
  "workdir": "/path/to/repo"
}
```

---

### 2️⃣ **Lange Tasks** (background mit Monitoring)

**Schritt 1: Starten**
```bash
codex exec "Refactor the entire auth module" --sandbox danger-full-access
```
→ Mit `background:true` und `pty:true`

**Schritt 2: Pollen**
```bash
process action=poll, sessionId=<returned_id>
```

**Schritt 3: Logs lesen**
```bash
process action=log, sessionId=<returned_id>
```

**Schritt 4: Bei Input antworten**
```bash
process action=submit, sessionId=<returned_id>, text="yes"
```

---

### 3️⃣ **Interaktive Session** (für komplexe Workflows)

```bash
codex  # Interactive mode
```

Dann mit `process action=send-keys` oder `process action=paste` interagieren.

---

## 🔒 Sandbox-Modi

| Modus | Beschreibung | Wann nutzen |
|-------|--------------|-------------|
| `workspace-write` | Schreiben nur im Workspace | ✅ Standard für die meisten Tasks |
| `danger-full-access` | Vollzugriff auf System | Nur wenn nötig (z.B. externe APIs, DB) |
| `read-only` | Nur lesen (kein Schreiben) | Für Reviews, Analysen |

**Empfehlung:** Immer mit dem **restriktivsten Modus** starten, der funktioniert.

---

## ⚠️ Häufige Fehler & Lösungen

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| `codex: command not found` | CLI nicht installiert | `npm i -g @openai/codex` |
| `OAuth token has been revoked` | Login abgelaufen | `codex logout` + `codex login --device-auth` |
| `sandbox limits` | Zu restriktiv | `--sandbox danger-full-access` versuchen |
| `wrong repo modified` | Falsches workdir | Immer `workdir` explizit setzen |

---

## 📝 Best Practices

1. **Vor dem ersten Call:** `codex --version` prüfen
2. **Immer `pty:true`** setzen (Codex braucht TTY)
3. **Immer `workdir`** aufs Ziel-Repo setzen
4. **Bei langen Tasks:** Background + Monitoring nutzen
5. **Ergebnisse verifizieren:** Nicht blind vertrauen, Logs prüfen!
6. **Keine halben Antworten:** Erst melden, wenn Task wirklich fertig

---

## 🧪 Test-Command

Um zu prüfen, ob Codex funktioniert:

```bash
codex exec "What is 2+2? Answer in one word." --sandbox workspace-write
```

**Erwartete Antwort:** `Four`

---

## 🔗 Referenzen

- [Codex CLI Docs](https://developers.openai.com/codex)
- [Skill: openai-codex-operator](/config/.openclaw/workspace/skills/openai-codex-operator/SKILL.md)
- [Usage Recipes](/config/.openclaw/workspace/skills/openai-codex-operator/references/codex-usage-recipes.md)

---

**Letztes Update:** 2026-02-28  
**Getestet mit:** Codex v0.106.0, ChatGPT Plus OAuth
