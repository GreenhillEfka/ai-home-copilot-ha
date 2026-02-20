# Worker-Konfiguration

## Übersicht

| Worker | Intervall | Model | Status |
|--------|-----------|-------|--------|
| Autopilot | 10min | glm-5:cloud | ✅ |
| Dashboard UX | 30min | glm-5:cloud | ✅ gefixt |
| Module Kernel | 5min | default | ✅ |
| Decision Matrix | 10min | default | ✅ |
| Task Scout | 15min | glm-5:cloud | ✅ gefixt |
| Debug Level | 30min | default | ✅ |
| PilotSuite Checkpoints | 30min | default | ✅ |
| Telegram Progress | 10min | glm-5:cloud | ✅ gefixt |

## Fixtures

Alle Worker nutzen `ollama/glm-5:cloud` als Model (außer Autopilot/Module Kernel/Decision Matrix/Debug Level/PilotSuite - die haben kein explizites Model).

## Templates

- `AGENTS.md` liegt unter `/usr/lib/node_modules/openclaw/docs/reference/templates/`
- Wird von Task Scout benötigt

## Updates

- 2026-02-14: Dashboard UX, Task Scout, Telegram auf glm5 umgestellt
- AGENTS.md Template an richtige Stelle kopiert
