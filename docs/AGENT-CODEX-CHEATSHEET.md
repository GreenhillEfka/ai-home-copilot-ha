# 🤖 Codex Quick-Reference für Agenten

> **Skill:** `openai-codex-operator` (aktiviert ✅)  
> **Verfügbar für:** Clawdya, Styx, Cowdya, Groky, Perplexya, Viewona

---

## ⚡ Quick Commands

```bash
# Test (immer zuerst probieren)
codex exec "What is 2+2? Answer in one word." --sandbox workspace-write

# Feature implementieren
codex exec "Implement <feature> with tests" --sandbox workspace-write

# Code reviewen
codex exec "Review this PR and list critical issues" --sandbox workspace-write

# Bug fixen
codex exec "Find root cause of <error> and propose fix" --sandbox danger-full-access

# Refactoring
codex exec "Refactor <module> to use <pattern>" --sandbox workspace-write
```

---

## 🎯 Wann nutzen?

| Agent | Typische Use-Cases |
|-------|-------------------|
| **Clawdya** 💋✨ | Koordiniert, ruft Codex bei Coding-Tasks |
| **Styx** 🌙🪷🔥 | PilotSuite-Code, HA-Integrationen, Automation |
| **Cowdya** 🧑‍💻 | Development, Code Reviews, neue Features |
| **Groky** 🦝🔧 | CI/CD, Releases, Automation Checks |
| **Perplexya** 🔮 | Code erklären, Dokumentation |
| **Viewona** 🎨 | UI-Code, 3D-Vision Skripte |

---

## ⚠️ Wichtig

1. **Immer `pty:true`** bei OpenClaw exec
2. **Immer `workdir`** setzen aufs Ziel-Repo
3. **Sandbox:** `workspace-write` zuerst, `danger-full-access` nur wenn nötig
4. **Login prüfen:** `codex login status` vor ersten Call
5. **Bei Fehlern:** Guide lesen → `/config/.openclaw/workspace/docs/CODEX-SKILL-GUIDE.md`

---

## 🔧 Troubleshooting

| Fehler | Fix |
|--------|-----|
| OAuth abgelaufen | `codex logout` + `codex login --device-auth` |
| Sandbox blockiert | `--sandbox danger-full-access` |
| Codex nicht gefunden | `npm i -g @openai/codex` |

---

**Test-Status:** ✅ Funktioniert (2026-02-28)  
**Letzter Test:** `codex exec "What is 2+2?"` → Antwort: "Four"
