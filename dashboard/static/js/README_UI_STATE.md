# UiState shared components (Dashboard / Lovelace)

This folder contains a small, **stable** UI-state + telemetry helper used across PilotSuite frontend surfaces.

## Public API (window.UiState)

Exposed by: `ui_state_components.js`

- `window.UiState.apiVersion` – semantic-ish marker for breaking changes.
- `window.UiState.EventKeys` / `window.UiState.Events`
  - Canonical telemetry event names (avoid ad-hoc strings):
    - `LOADING_SHOWN` → `ui_state_loading_shown`
    - `EMPTY_SHOWN` → `ui_state_empty_shown`
    - `ERROR_SHOWN` → `ui_state_error_shown`
    - `RETRY_CLICKED` → `ui_state_retry_clicked`
    - `RETRY_SUCCEEDED` → `ui_state_retry_succeeded`
    - `RETRY_FAILED` → `ui_state_retry_failed`
    - `GLOBAL_DEGRADED_ON` → `ui_global_degraded_on`
    - `GLOBAL_DEGRADED_OFF` → `ui_global_degraded_off`
- `window.UiState.emit(eventNameOrKey, payload)`
  - Convenience helper to emit telemetry.
  - Accepts either the full event name (`"ui_state_*"`) **or** the enum key (`"LOADING_SHOWN"`).

## Components

- `StateSkeleton`, `StateEmpty`, `StateError`
  - Render consistent UI shells for loading/empty/error.
  - Auto-emit telemetry with the canonical event names.

- `GlobalDegradedBanner`
  - Optional banner for degraded connectivity.
  - Can auto-wire itself to `ERROR_SHOWN` with `{ degraded: true }`.

- `UiStateToolkit`
  - Convenience wrapper for `loading()` / `empty()` / `error()` + banner control.

## Recommended usage (consumer)

```js
// Prefer UiStateToolkit when available.
const ui = window.UiState?.UiStateToolkit
  ? new window.UiState.UiStateToolkit({ scope: 'dashboard/home' })
  : null;

ui?.loading(container, { source: 'zone:wohn', message: 'Daten werden geladen…' });

// For custom cards/widgets: prefer UiState.emit + enum keys
window.UiState?.emit('RETRY_CLICKED', { scope: 'suggestions', source: 'styx-suggestions-card' });
```

## Notes

- Keeping event names centralized ensures consistent analytics and easier QA assertions.
- Consumers should not hardcode `ui_state_*` strings unless `UiState` is not present.
