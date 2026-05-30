# PilotSuite HA Testing

## Fresh-operator smoke path

1. Install PilotSuite Core first.
2. Install PilotSuite HA.
3. Restart Home Assistant.
4. Complete the PilotSuite config flow.
5. Confirm Home Assistant is loading files from `custom_components/pilotsuite/`.

## Maintainer smoke path

Run from the repository root:

```bash
python -m pytest tests/test_agent_status_sensor_projection.py tests/test_brain_activity_sensor_projection.py tests/test_neuron_dashboard_sensors_projection.py tests/test_notification_sensor_projection.py -q
```

## Canonical test paths

- integration code: `custom_components/pilotsuite/`
- workflow checks: `.github/workflows/ci.yml`
- metadata checks: `VERSION`, `manifest.json`, `custom_components/pilotsuite/manifest.json`
