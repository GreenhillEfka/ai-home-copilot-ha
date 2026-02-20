# Model-Routing-Strategie (Token-Effizienz + Robustheit)

## Aktueller Fallback-Stack (bereits sehr gut!)

```
1. anthropic/claude-sonnet-4-0 (primary) 
2. openrouter/auto
3. anthropic/claude-opus-4-6  
4. anthropic/claude-haiku-4-5 ← GÜNSTIG
5. anthropic/claude-sonnet-4-5
6. openai-codex/gpt-5.3-codex
7. openai/gpt-5.1-codex 
8. openai/o3-mini
9. openai/gpt-4o-mini ← SEHR GÜNSTIG
10. ollama/deepseek-r1 ← KOSTENLOS + LOKAL
11. openrouter/free
12. ollama/qwen3-4b ← KOSTENLOS + LOKAL
13. ollama/codellama ← KOSTENLOS + LOKAL
```

## Task-Based Model-Assignment (Vorschlag)

### Heartbeats/Routine (→ günstig/kostenlos)
- **Primary:** `anthropic/claude-haiku-4-5` (sehr günstig, intelligent)
- **Fallback:** `ollama/deepseek-r1` (kostenlos, lokal)
- **Context:** minimal (nur HEARTBEAT.md + heute)

### Simple Q&A/Info (→ mid-tier)  
- **Primary:** `openai/gpt-4o-mini` (sehr günstig, solid)
- **Fallback:** `anthropic/claude-haiku-4-5`

### Complex/Creative (→ premium)
- **Primary:** `anthropic/claude-sonnet-4-0` (aktuell)
- **Fallback:** `openai/gpt-5.1-codex` für Code
- **Fallback:** `anthropic/claude-opus-4-6` für Creative

### Specialist Tasks
- **Code:** `openai-codex/gpt-5.3-codex` → `ollama/codellama`
- **Reasoning:** `openai/o3-mini` → `openai/o1` 
- **Emergency:** `ollama/deepseek-r1` (immer verfügbar)

## Implementierung (Safe Rollout)

### Phase 1: Heartbeat-Optimierung (sofort testbar)
```bash
# Test Haiku für Heartbeats
/model haiku
? (test heartbeat)
```
→ Wenn OK, dann HEARTBEAT.md erweitern mit `# Model: haiku`

### Phase 2: Task-Detection (experimentell)
- Keywords für Model-Routing erkennen
- Bei Unsicherheit: Standard-Modell verwenden
- Log/Monitor für Optimierung

### Phase 3: Auto-Routing (nach Tests)
- Config-Patch für task-based primaries
- Fallback-Chain bleibt unverändert (Robustheit)

## Kontingent-Schutz

### Provider-Monitoring
- **Anthropic**: 2h cooldown bei billing issues
- **OpenAI**: 2h cooldown bei billing issues  
- **OpenRouter**: 0.5h cooldown (günstig/backup)
- **Ollama**: unlimited (lokal)

### Emergency-Modus (bei Rate-Limits)
1. Switch zu Ollama-only
2. Reduzierte Funktionalität, aber funktionsfähig
3. Auto-retry nach cooldown

### Budget-Alerts (Idee)
- Daily/Weekly token tracking
- Warning bei 80% Budget
- Auto-downgrade bei 90%

## Ollama Service-Check

Ist bereits aktiv: `http://76e18fb5-ollama:11434`
- deepseek-r1: 8B params, 16k context ← **Starker Allrounder**
- qwen3-4b: 4B params, 8k context ← **Ultra-effizient**  
- codellama: 7B params, 16k context ← **Code-Spezialist**

## Risiko-Mitigation

### No-Single-Point-of-Failure
- ✅ Multiple Provider (Anthropic, OpenAI, OpenRouter)
- ✅ Local Ollama (funktioniert ohne Internet/API)
- ✅ Diverse Model-Sizes (von 4B bis 405B)

### Graceful Degradation
- Premium → Mid-tier → Budget → Local
- Funktionalität bleibt erhalten, nur Quality/Speed variiert
- Transparente Fallback-Meldungen

---
*Ready to test: Heartbeat mit Haiku*