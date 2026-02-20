# Zusätzliche Profi Worker

## Übersicht

| Worker | Status | Modul | Template |
|--------|--------|-------|----------|
| mood_module_test | 📝 Config fertig | mood_module | MODULE_TEST_WORKER |
| media_context_v2_test | 📝 Config fertig | media_context_v2 | MODULE_TEST_WORKER |
| forwarder_quality_test | 📝 Config fertig | forwarder_quality | MODULE_TEST_WORKER |
| unifi_module_test | 📝 Config fertig | unifi_module | MODULE_TEST_WORKER |

## Templates

### MODULE_TEST_WORKER
**Pfad:** `docs/worker_templates/MODULE_TEST_WORKER.md`

**Funktion:**
- py_compile Check
- Import-Check
- Tests ausführen (falls vorhanden)
- Review-Checkliste
- Merge-Vorbereitung

## Worker Configs

### Ort
`notes/workers/{module}_test_worker.json`

### Struktur
```json
{
  "name": "AI Home CoPilot: {Module Name} Test",
  "interval": null,  // einmalig
  "timeoutSeconds": 600,
  "model": "ollama/glm-5:cloud",
  "enabled": true,
  "targets": {
    "module": "{module_name}",
    "branch": "{git_branch}",
    "spec": "docs/module_specs/{module}_v0.1.md"
  }
}
```

## Cron-Job erstellen

```bash
# Beispiel: mood_module Test Worker starten
openclaw cron add --config notes/workers/mood_module_test_worker.json
```

## Nächste Schritte

1. Worker als Cron-Jobs registrieren
2. Module testen
3. Ergebnisse reporten
4. Bei Bedarf fixes einbauen
5. Release vorbereiten

## Noch offen

| Modul | Status | Worker |
|-------|--------|--------|
| brain_graph | merged_to_wip_branch | ❌ |
| dev_surface | merged_to_wip_branch | ❌ |
| diagnostics_contract | merged_to_wip_branch | ❌ |
