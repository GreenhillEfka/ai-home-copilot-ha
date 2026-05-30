# Contributing

## Scope

Keep contributions aligned to the canonical integration tree:
- `custom_components/pilotsuite/`
- `docs/`

## Before opening a PR

1. Keep public install truth simple: Core first, HA second.
2. Keep version truth aligned across `README.md`, `VERSION`, `manifest.json`, and `custom_components/pilotsuite/manifest.json`.
3. Run the smoke path from `docs/TESTING.md`.
4. Do not reintroduce `copilot_ha` as the primary public install story.

## Pull request expectations

- describe the user-visible effect
- list touched files
- include proof run
- call out any workflow or release metadata changes
