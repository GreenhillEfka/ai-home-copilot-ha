# PilotSuite HA API / Integration Reference

## Canonical source path

- `custom_components/pilotsuite/`

## What this repository owns

- Home Assistant config flow
- integration wiring
- entities and sensors
- dashboard-facing resources
- metadata for HACS and GitHub releases

## Core relationship

PilotSuite HA pairs with the PilotSuite Core add-on:
- `https://github.com/GreenhillEfka/pilotsuite-styx-core`
- expected default endpoint: `http://<home-assistant-host>:8909`

## Current metadata truth

- domain: `pilotsuite`
- integration name: `PilotSuite HA`
- config flow: enabled
- integration type: `hub`

Older `copilot_ha` references should be treated as legacy migration surfaces, not current release truth.
