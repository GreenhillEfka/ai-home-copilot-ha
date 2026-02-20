# PilotSuite - Entwicklungs-Setup

## Überblick

Dieses Setup kombiniert:
- **React Board** für visuelles Projektmanagement
- **Ollama Cloud Modelle** für optimierte Taskbearbeitung
- **Iteration Manager Worker** für kontinuierliche Entwicklung

## React Board

**URL:** http://192.168.30.18:48099/__openclaw__/ReactBoard/

**Features:**
- Kanban Board (Offen → In Arbeit → Review → Erledigt)
- Multi-Projekt Support
- File Browser
- Activity Log

## Modell-Auswahl

| Task-Typ | Modell | Kontext | Reasoning |
|----------|--------|---------|-----------|
| Python/HA Tests | `glm-5:cloud` | 128K | ✅ |
| Code Review | `deepseek-r1:latest` | 131K | ✅ |
| Documentation | `glm-5:cloud` | 128K | ❌ |
| Merge Prep | `glm-5:cloud` | 128K | ❌ |

## Iteration Manager Worker

**Konfiguration:**
- Intervall: 5 Minuten
- Max. parallele Worker: 2
- Single Source: `projects/ai_home_copilot/INDEX.md`

## Workflow

```
React Board (visuell)
        ↓
INDEX.md (Single Source of Truth)
        ↓
Iteration Manager Worker (5min Tick)
        ↓
Task Worker (sessions_spawn)
        ↓
Report → INDEX.md Update
```

## Nächste Schritte

1. **brain_graph_v2** → Tests starten
2. **UniFi Module** → Ergebnis abwarten (16:15)
3. **Habitus Zones v2** → Auf Brain Graph aufbauen

## Model Context Switching

Bei Übergabe zwischen Modellen:
1. "Wechsle zu [Modell] für [Aufgabe]"
2. Ergebnis: "[Kurzfassung]"
3. Klarer Übergabepunkt - keine Wiederholung
