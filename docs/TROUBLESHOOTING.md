# PilotSuite HA Troubleshooting

## Integration not visible after install

- Restart Home Assistant after HACS or manual install.
- Confirm files exist under `custom_components/pilotsuite/`.

## Config flow cannot complete

- Confirm the Core add-on is installed and reachable first.
- Re-check the endpoint used during setup.
- Re-open **Settings → Devices & Services** and retry.

## Legacy naming confusion

If you still see `copilot_ha` in older files or migration notes:
- current public truth is **PilotSuite** / `pilotsuite`
- canonical release path is `custom_components/pilotsuite/`
- legacy names should not be used as the main install story

## Version mismatch

Canonical version truth for this repo must stay aligned across:
- `README.md`
- `VERSION`
- `manifest.json`
- `custom_components/pilotsuite/manifest.json`
