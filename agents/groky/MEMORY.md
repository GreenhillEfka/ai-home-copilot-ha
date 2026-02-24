# MEMORY.md - Groky's Long-Term Memory

This file contains distilled learnings, decisions, and important context about the PilotSuite project from Groky's perspective.

## Project Overview

**PilotSuite** - AI-powered Home Assistant integration with local-first architecture.

### Hauptkomponenten (PilotSuite Styx)
- **pilotsuite-styx-ha** (`https://github.com/GreenhillEfka/pilotsuite-styx-ha`): Home Assistant custom component (frontend/UI, HACS installierbar)
- **pilotsuite-styx-core** (`https://github.com/GreenhillEfka/pilotsuite-styx-core`): Backend API und Processing Engine (Python/Ollama, integriert mit HA via custom component)

### Entwicklungszweig-Struktur
- `ai_home_copilot_hacs_repo` → vorgeschichtliche Version / Entwicklungszweig von `pilotsuite-styx-ha`
- `ha-copilot-repo` → vorgeschichtliche Version / Entwicklungszweig von `pilotsuite-styx-core`

**Zusammengehörigkeit**: Beide Projekte (`pilotsuite-styx-ha` + `pilotsuite-styx-core`) bilden **gemeinsam PilotSuite** — sie kommunizieren über REST API und müssen **immer zusammen** betrachtet werden.

## Groky's Core Responsibilities

### Daily/Weekly
- Git-Status prüfen → backup branch bei Änderungen
- `dev` branches von beiden Repos pullen
- Disk cleanup (pip cache, tmp files)
- Log rotation (30 days)

### Development Cycle
1. **Plan & Sketch** (Grok-Orchestration) → Architektur entscheiden, Feature branch erstellen
2. **Build & Test** (Codex/Claude Code) → API endpoints, knowledge graph, scene extraction
3. **Refine & Review** → GitHub PR, testen auf echter HA Instanz
4. **Release** → Tagging, GitHub Releases, HACS metadata update

### Ollama Setup
- Remote Ollama auf `192.168.31.84:11434`
- Zugriff via `OLLAMA_HOST=http://192.168.31.84:11434`
- Verfügbare Modelle: `qwen3-coder-next:cloud`, `kimi-k2.5:cloud`, `glm-4.7-flash:latest`, `deepseek-r1:latest`

## Key Decisions

### Architecture
- Local-first AI with Ollama support
- Modular design for extensibility
- Knowledge graph for home context
- Multi-user preference learning (MUPL)

### Development Workflow
- GitHub backup branches: `backup/YYYY-MM-DD`
- Dev branches: `dev/feature-YYYY-MM-DD`
- Release tags following semantic versioning

## Learnings

### Model Performance
- `qwen3-coder-next:cloud` works well for coding tasks via remote Ollama
- `kimi-k2.5:cloud` good for general orchestration tasks

### Common Issues
- SSH key location: `/config/.ssh/` vs `/root/.ssh/`
- GitHub push conflicts: Use force-with-lease carefully
- Session cleanup: Run daily to manage disk space
- Projektzusammengehörigkeit: `ai_home_copilot_hacs_repo` und `ha-copilot-repo` **müssen gemeinsam** betrachtet werden — sie bilden ein System.
- Ollama Fallback: Bei 500 Error auf `kimi-k2.5:cloud` oder `glm-4.7-flash:latest` ausweichen
- Status Reporting: Jeder Dev-Run muss Status per Telegram senden (nicht vergessen!)

## Active TODOs

### P0 (Critical)
- Error isolation improvements
- Connection pooling

### P1 (Important)
- Scene/Routine pattern extraction
- Push notifications

### P2 (Nice to have)
- MCP Phase 2
- Test suite expansion

## Notes

*Last updated: 2026-02-23 by Groky*