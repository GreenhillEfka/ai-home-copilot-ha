# Safe Model-Optimization Rollout

## ✅ Pre-Flight Checks (DONE)
- [x] Ollama service läuft: `http://76e18fb5-ollama:11434`
- [x] 3 Modelle verfügbar: deepseek-r1 (8B), qwen3-4b, codellama 
- [x] Model-Override funktioniert: `ollama/deepseek-r1` getestet
- [x] Fallback-Chain ist robust (12 Modelle tief)

## 🧪 Phase 1: Controlled Testing (NEXT)

### 1A: Haiku Heartbeat Test (5 min)
```bash
# Switch zu Haiku für 1-2 Heartbeat-Cycles
/model haiku
# Test heartbeat response time + quality
# Measure: response latency, functionality, cost

# Wenn OK → zurück zu Sonnet
/model default
```

### 1B: Deepseek Fallback Test (5 min)  
```bash
# Temporärer Switch zu lokalem Modell
/model ollama-deepseek  
# Test: simple Q&A, basic reasoning
# Measure: response quality vs. Sonnet

# Zurück zu Sonnet
/model default
```

### 1C: Task-Specific Tests (10 min)
- **Code Task** → `/model ollama-codellama`
- **Simple Info** → `/model gpt4o-mini`
- **Complex Reasoning** → `/model opus` (wenn nötig)

## 🎯 Phase 2: Heartbeat Optimization (wenn Tests OK)

### Safe HEARTBEAT.md Update
```markdown
# HEARTBEAT.md v2 (Token-Optimized)

# Model: haiku (cost-optimized for routine checks)
# Context: minimal (only today + critical alerts)

## Quick Checks (every 45-60min, not 30min)
- [ ] Critical alerts from memory/today
- [ ] HA errors/warnings (if configured)

## Deep Checks (every 3-4h)  
- [ ] Email scan (unread count only)
- [ ] Calendar (next 24h events)
- [ ] Project status (if working day)

## Night Mode (23:00-07:00)
- [ ] Emergency/critical only
```

### Backup Plan
- Keep `HEARTBEAT.md.backup` with current version
- Monitor for 24h
- Rollback if issues: `mv HEARTBEAT.md.backup HEARTBEAT.md`

## 🚀 Phase 3: Smart Routing (later, optional)

### Context-Based Model Selection
- **Routine/Status** → Haiku/GPT-4o-mini/Deepseek
- **Complex/Creative** → Sonnet/Opus 
- **Code** → GPT-5/Codellama
- **Emergency** → Ollama (always works)

## 📊 Success Metrics

### Must-Maintain
- ✅ **100% uptime** (fallbacks working)
- ✅ **Response quality** für complex tasks
- ✅ **All current functionality** 

### Optimize
- 📉 **50% token reduction** auf Heartbeats
- 📉 **30% overall cost reduction**
- ⚡ **Faster routine responses** (local models)

## 🛡️ Risk Mitigation

### Immediate Rollback Triggers
- **Functionality loss** → back to Sonnet immediately
- **Poor response quality** → escalate model
- **API errors** → fallback chain activated
- **User dissatisfaction** → manual override

### Monitoring Dashboard (Idea)
```bash
# Daily cost tracking
echo "$(date): Sonnet: $X, Haiku: $Y, Ollama: $0" >> logs/daily_costs.txt
```

---
**🟢 Ready for Phase 1 Testing** 
*Estimated time: 20 minutes total*
*Risk: LOW (easy rollback)*