# Token-Optimierungsstrategie ("Sparpläne")

## Zielsetzung
Reduzierung der API-Costs bei gleichbleibender oder besserer Funktionalität.

## Aktuelle Kostentreiber

### 1. Heartbeat-Pattern
**Problem:** 
- Alle ~30 Minuten Full-Context Load (AGENTS.md, SOUL.md, USER.md, memory files)
- Großes Modell (Sonnet) auch für triviale "nichts zu tun" Checks
- HEARTBEAT.md meist leer → verschwendete Token

**Lösungsansätze:**
- **Adaptive Frequenz:** Bei Inaktivität seltener checken (1h, 2h, 4h Stufen)
- **Minimal Context:** Heartbeats mit reduziertem Kontext (nur HEARTBEAT.md + letzte 2 memory-Einträge)
- **Model-Downgrade:** Heartbeats mit günstigerem Modell (Haiku statt Sonnet)

### 2. Memory-Loading
**Problem:**
- `memory_search` + `memory_get` bei jeder Frage, auch bei trivialen
- Große Memory-Dateien werden komplett geladen

**Lösungsansätze:**
- **Lazy Loading:** Memory nur bei expliziten Erinnerungs-Keywords laden
- **Smart Chunking:** Nur relevante Abschnitte laden, nicht ganze Dateien
- **Cache-Strategie:** Häufig genutzte Memory-Snippets session-intern cachen

### 3. Model-Routing
**Problem:**
- Sonnet für alles, auch für einfache Ja/Nein-Entscheidungen oder Routine-Checks

**Lösungsansätze:**
- **Task-Classification:** Anfrage-Typ erkennen → passendes Modell wählen
  - **Routine/Status:** Haiku oder GPT-4o-mini
  - **Komplex/Kreativ:** Sonnet oder GPT-4o
  - **Code/Analyse:** GPT-4o oder O1-mini
- **Escalation-Pattern:** Start mit kleinem Modell, upgrade bei Bedarf

## Implementierungsplan

### Phase 1: Heartbeat-Optimierung (sofort)
```markdown
# HEARTBEAT.md Erweiterung
# Adaptive Heartbeat - Context: minimal | Frequency: adaptive | Model: haiku

## Quick Checks (every 30-60min)
- [ ] Critical notifications (errors, alerts)
- [ ] Immediate todos from memory/today

## Deep Checks (every 2-4h)  
- [ ] Email/Calendar scan
- [ ] Project status updates
- [ ] Memory consolidation

## Night Mode (23:00-08:00)
- [ ] Emergency only
```

### Phase 2: Model-Routing (1-2 Wochen)
- OpenClaw Gateway Config erweitern: Model-Aliases mit Cost-Tags
- Anfrage-Klassifikation implementieren
- Session-Parameter für dynamisches Model-Switching

### Phase 3: Memory-Optimierung (2-3 Wochen)
- Memory-Search mit Relevanz-Threshold
- Chunk-basierte Memory-Loading
- Session-lokaler Memory-Cache

## Messbare Ziele
- **50% Reduktion** der Heartbeat-Costs durch Model-Downgrade + adaptive Frequenz
- **30% Reduktion** der Memory-Loading-Costs durch Smart-Chunking
- **Keine Funktionalitätsverluste** bei komplexen Aufgaben

## Monitoring
- Token-Usage pro Tag tracken (vor/nach Optimierung)
- Response-Quality bei verschiedenen Model-Routing-Strategien testen
- User-Zufriedenheit bei reduzierter Heartbeat-Frequenz messen

---
*Stand: 2026-02-10 - erste Strategie-Version*