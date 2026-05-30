# PilotSuite HA User Guide

## What this integration does

PilotSuite HA connects Home Assistant to the PilotSuite Core add-on and provides the Home Assistant-native side of the product:
- config flow
- entity and sensor surfaces
- dashboard resources
- integration lifecycle wiring

## Basic setup flow

1. Install PilotSuite Core first.
2. Install PilotSuite HA.
3. Restart Home Assistant.
4. Add **PilotSuite** in **Devices & Services**.
5. Complete the config flow.
6. Verify the integration stays on the `pilotsuite` domain.

## Canonical maintainer paths

- integration code: `custom_components/pilotsuite/`
- public docs: `README.md`, `docs/`
- canonical metadata: `VERSION`, `manifest.json`, `custom_components/pilotsuite/manifest.json`

## Release guidance

Public install truth for testers should stay simple:
- Core first
- HA second
- HACS custom repository first
- manual copy path second
