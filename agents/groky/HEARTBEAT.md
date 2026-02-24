# HEARTBEAT.md — Groky's Autonomic Checks

# Groky führt alle 10 Minuten autonome Dev-Checks durch.
# Fallback-Modelle garantieren Ausfallsicherheit.
# Workspace-Struktur: pilotsuite-dev/, pilotsuite-main/

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BEACHTE: LESE ZUERST PILOTSUITE_DEVELOPMENT.md
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Die Workspace-Struktur ist zentral für deine Checks.
# lies `/config/.openclaw/workspace/PILOTSUITE_DEVELOPMENT.md`

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTONOME DEV-RUN (alle 10 min)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## PHASE 1: REPO STATUS
- git fetch origin (pilotsuite-styx-core, pilotsuite-styx-ha)
- git log HEAD..origin/main --oneline
- git status --porcelain
- Branch-Sync prüfen

## PHASE 2: BUGFIX ROUND (P0)
- Error Isolation & Connection Pooling prüfen
- Wenn P0-Fixes in dev → lokal testen (in pilotsuite-dev/)
- Test-Tag erstellen (test-p0-YYYYMMDDHHMMSS)

## PHASE 3: FEATURE EXTENSION (P1/P2)
- Vision.md prüfen (roadmap items)
- PHASE5_TODO.md review (missing APIs)
- Scene/Routine, Push Notifications

## PHASE 4: HA CONFORMANCE
- manifest.json validieren
- HACS component structure prüfen
- dashboard panels existence check

## PHASE 5: RELEASE + NOTES
- CHANGELOG.md update
- RELEASE_NOTES.md erstellen/aktualisieren
- Test-Tag pushen

## PHASE 6: STATUS REPORT
- Telegram Report: Repo Status, Bugfix, Features, HA Conformance
- **BEACHTE:** Nach jedem Run Status per Telegram senden!

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WORKSPACE STRUKTUR (FÜR GROKY)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Groky arbeitet in dieser Struktur:
#
# /config/.openclaw/workspace/
# ├── pilotsuite-styx-core/       # Backend (Flask, Port 8909)
# ├── pilotsuite-styx-ha/         # HA Integration (HACS)
# ├── pilotsuite-dev/             # gemeinsame Tools (dev)
# │   ├── pilotsuite-styx-core/   # → symlink
# │   ├── pilotsuite-styx-ha/     # → symlink
# │   ├── github-action-shared.yml
# │   ├── DEVELOPMENT.md
# │   └── PHILOSOPHY.md
# ├── pilotsuite-main/            # gemeinsame Tools (main)
# │   ├── pilotsuite-styx-core/   # → symlink (vorgesehen)
# │   └── pilotsuite-styx-ha/     # → symlink (vorgesehen)
# └── logs/
#     └── pilotsuite-build-cron/

# WICHTIG: Groky nutzt pilotsuite-dev/ für Tests, CI und Build-Checks.
# Die Struktur ist zentral für die Entwicklung — siehe PILOTSUITE_DEVELOPMENT.md

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OLLAMA FALLBACK STRATEGY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Primary Model
- ollama/qwen3-coder-next:cloud (remote: 192.168.31.84:11434)

## Fallback Chain (wenn primary fehlschlägt)
1. ollama/kimi-k2.5:cloud
2. ollama/glm-4.7-flash:latest
3. ollama/deepseek-r1:latest
4. local ollama fallback (falls möglich)

## Max Retries: 3
## Retry Delay: 5000ms

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STATUS QUO (Stand: 2026-02-23)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Branches
- pilotsuite-styx-core: fix/error-isolation-connection-pooling
- pilotsuite-styx-ha: fix/error-isolation-connection-pooling

## P0 Tasks (Error Isolation)
- ✅ Error Boundary implementiert (styx-fork-core)
- ✅ Error Status API implementiert
- ⏳ In main integrieren
- ⏳ HA Integration (Dashboard Widget)

## P1 Tasks (Feature Extension)
- Scene/Routine Pattern Extraction
- Push Notifications

## P2 Tasks (Nice to have)
- MCP Phase 2
- Test Suite Expansion
