# Iteration Manager Worker

## Name
`iteration-manager`

## Zweck
Alle 5 Minuten die nächste sinnvolle Entwicklungsiteration starten und maximal 2 Taskworker parallel halten.

## Arbeitsweise

### 1. Status prüfen
```bash
# Aktive Worker zählen
sessions_list kinds=["subagent"] | jq '.[] | select(.label | startswith("task-")) | .id' | wc -l
```

### 2. Nächste Iteration bestimmen
```bash
# Priorisierte Liste lesen
cat /config/.openclaw/workspace/projects/ai_home_copilot/INDEX.md
```

### 3. Worker  starten wenn< 2
```bash
# Nächsten offenen Task wählen
# → Branch checkout
# → Tests ausführen
# → Report schreiben
# → Status in INDEX.md aktualisieren
```

### 4. Modell-Auswahl (Ollama Cloud)

| Task-Typ | Modell | Reasoning |
|----------|--------|-----------|
| Python/HA Tests | `glm-5:cloud` | Ja |
| Code Review | `deepseek-r1:latest` | Ja |
| Doc Updates | `glm-5:cloud` | Nein |
| Merge Prep | `glm-5:cloud` | Nein |

## Model Context Switching

Bei Modellwechsel:
1. Vorher: "Wechsle zu [Modell] für [Aufgabe]"
2. Nachher: "Ergebnis mit [Modell]: [Kurzfassung]"
3. Keine Wiederholung - klarer Übergabepunkt

## Output
- Nur bei signifikanter Änderung (Worker gestartet/fertig)
- `NO_REPLY` wenn alles stabil

## Config
```json
{
  "maxConcurrentWorkers": 2,
  "intervalMinutes": 5,
  "modelSelection": {
    "code_review": "ollama/glm-5:cloud",
    "testing": "ollama/deepseek-r1:latest",
    "documentation": "ollama/glm-5:cloud"
  }
}
```

## Integration mit React Board
- INDEX.md dient als Single Source of Truth
- Tasks werden nicht automatisch aktualisiert (manuell im Board)
- Worker liest INDEX.md, nicht die API
