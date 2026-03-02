# 🚀 Claude Code CLI Integration — PilotSuite Dev Loop

**Erstellt:** 2026-03-02 04:30 CET  
**Status:** 🟢 Aktiv (3 Sessions pro Iteration)

---

## 🎯 Ziel

Jede 20-Minuten-Iteration umfasst **3 parallele Claude Code CLI Sessions** für maximale Code-Implementation.

---

## 📋 Standard-Tasks pro Iteration

| Session | Priorität | Typ | Beispiel-Task | Modell |
|---------|-----------|-----|---------------|--------|
| **Session 1** | P0 | Cache/Performance | CacheManager, Query-Optimization | `ollama/qwen3-coder-next` |
| **Session 2** | P1 | API/Features | Batch-Operations, New Endpoints | `ollama/qwen3-coder-next` |
| **Session 3** | P2 | Infrastruktur | WebSocket, Reconnect, Monitoring | `ollama/qwen3.5` |

---

## 🛠️ Command-Vorlage (Lokal mit Ollama)

```bash
# Session 1: P0 Cache/Performance
cd /config/.openclaw/workspace/pilotsuite-styx-core && \
claude --effort high --permission-mode acceptEdits \
  --model ollama/qwen3-coder-next \
  'P0: <Task-Beschreibung>'

# Session 2: P1 API/Features
cd /config/.openclaw/workspace/pilotsuite-styx-core && \
claude --effort high --permission-mode acceptEdits \
  --model ollama/qwen3-coder-next \
  'P1: <Task-Beschreibung>'

# Session 3: P2 Infrastruktur
cd /config/.openclaw/workspace/pilotsuite-styx-core && \
claude --effort high --permission-mode acceptEdits \
  --model ollama/qwen3.5 \
  'P2: <Task-Beschreibung>'
```

---

## 🔄 Workflow pro Iteration

### **Phase 1: Task-Auswahl (2 Min)**
1. PHASE5_TODO.md lesen
2. Top-3-Prioritäten identifizieren (P0, P1, P2)
3. Tasks in AGENTEN_INTEGRATIONSPLAN.md eintragen

### **Phase 2: Sessions Starten (1 Min)**
```bash
# Alle 3 Sessions parallel starten
claude --effort high --permission-mode acceptEdits --model ollama/qwen3-coder-next 'P0: ...' &
claude --effort high --permission-mode acceptEdits --model ollama/qwen3-coder-next 'P1: ...' &
claude --effort high --permission-mode acceptEdits --model ollama/qwen3.5 'P2: ...' &
wait
```

### **Phase 3: Coding (12 Min)**
- Alle 3 Sessions arbeiten parallel
- Auto-Edit Mode für direkte Code-Änderungen
- Tests werden parallel geschrieben

### **Phase 4: Integration (5 Min)**
- Commits prüfen
- Tests laufen lassen
- Merge ins Hauptprojekt
- Release taggen

---

## 📊 Metriken pro Iteration

| Metrik | Ziel | Messung |
|--------|------|---------|
| **Sessions gestartet** | 3 | ✅ Zählung |
| **Commits erstellt** | ≥3 | ✅ Git log |
| **Tests geschrieben** | ≥20 | ✅ pytest --co |
| **Code-Qualität** | ≥90% Coverage | ✅ coverage report |
| **Features abgeschlossen** | ≥3 | ✅ CHANGELOG |

---

## 🚨 Fallback bei Problemen

| Problem | Lösung |
|---------|--------|
| Claude API Credits zu niedrig | ✅ **Lokale Ollama-Modelle** (qwen3-coder-next, qwen3.5) |
| Session timeout | Retry mit `--effort medium` |
| Code-Konflikte | Manuelles Merge durch @styx |
| Tests rot | Bugfix-Session priorisieren |

---

## ✅ Checkliste pro Iteration

- [ ] 3 Tasks identifiziert (P0, P1, P2)
- [ ] 3 Claude Code CLI Sessions gestartet
- [ ] Sessions nutzen lokale Ollama-Modelle
- [ ] Code wurde committet
- [ ] Tests sind grün
- [ ] Release wurde getaggt
- [ ] CHANGELOG aktualisiert

---

**Erste Iteration:** 2026-03-02 04:30 CET  
**Nächste Iteration:** Automatisch in 20 Minuten via Cron

---

💋✨ **AB JETZT STANDARD — 3 CLAUDE CODE CLI SESSIONS PRO LOOP!** 🚀
