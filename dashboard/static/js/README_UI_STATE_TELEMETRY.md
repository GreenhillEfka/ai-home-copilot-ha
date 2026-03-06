# UI State Telemetry (PS-UX-024)

This project emits UI state telemetry events via `window.UiState`.

Source of truth:
- `dashboard/static/js/ui_state_components.js`

## Why
Consumers (cards/widgets/dashboard) MUST avoid ad-hoc `"ui_state_*"` string literals where possible.
Instead, use `UiState.emit(<key|name>, payload)` with standardized keys.

## API
- `window.UiState.apiVersion` — semantic version of the client-side telemetry API.
- `window.UiState.EventKeys` — canonical keys → event-name mapping.
- `window.UiState.emit(eventKeyOrName, payload)` — convenience wrapper:
  - accepts either a key (e.g. `"LOADING_SHOWN"`) **or** a full event name (e.g. `"ui_state_loading_shown"`).

## Canonical events
The following keys exist in `UiState.EventKeys`:
- `LOADING_SHOWN` → `ui_state_loading_shown`
- `EMPTY_SHOWN` → `ui_state_empty_shown`
- `ERROR_SHOWN` → `ui_state_error_shown`
- `GLOBAL_DEGRADED_ON` → `ui_global_degraded_on`
- `GLOBAL_DEGRADED_OFF` → `ui_global_degraded_off`
- `RETRY_CLICKED` → `ui_state_retry_clicked`
- `RETRY_SUCCEEDED` → `ui_state_retry_succeeded`
- `RETRY_FAILED` → `ui_state_retry_failed`

## Payload conventions (minimal)
All events SHOULD include:
- `scope`: which screen/widget emitted the event (e.g. `dashboard`, `suggestions`, `errors`, `suggestion_detail`)
- `source`: optional component identifier (e.g. `styx-suggestions-card`)
- `message` / `detail`: optional human-readable strings
- `degraded`: optional boolean if the UI is in read-only/stale mode

The emitter automatically appends:
- `emittedAt` (ISO timestamp)

## Consumer examples
- Suggestions Card: `custom_components/copilot_ha/www/styx-suggestions-card.js`
- Error Card: `custom_components/copilot_ha/www/styx-error-card.js`

## Do / Don't
Do:
- `UiState.emit('LOADING_SHOWN', { scope: 'suggestions', source: 'styx-suggestions-card' })`

Don't:
- `window.dispatchEvent(new CustomEvent('ui_state_loading_shown', ...))` (unless `UiState` is not available)
