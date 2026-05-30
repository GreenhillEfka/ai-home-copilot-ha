# PilotSuite HA Installation

## Canonical install order

1. Install PilotSuite Core from `https://github.com/GreenhillEfka/pilotsuite-styx-core`.
2. Install PilotSuite HA from this repository.

## Recommended path, HACS custom repository

1. Open HACS.
2. Go to Integrations.
3. Open the menu and choose **Custom repositories**.
4. Add `https://github.com/GreenhillEfka/pilotsuite-styx-ha` as category **Integration**.
5. Install **PilotSuite HA**.
6. Restart Home Assistant.
7. Open **Settings → Devices & Services**.
8. Add integration **PilotSuite**.

## Manual installation

1. Copy `custom_components/pilotsuite/` into `/config/custom_components/`.
2. Restart Home Assistant.
3. Add integration **PilotSuite** from **Devices & Services**.

## First verification path

1. Confirm PilotSuite Core is healthy first.
2. Confirm Home Assistant can see `custom_components/pilotsuite/`.
3. Complete the PilotSuite config flow.
4. Confirm the integration loads without relying on legacy `copilot_ha` paths.
