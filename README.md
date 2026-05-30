# PilotSuite — Home Assistant Integration

**Version:** 20.0.10  
**License:** MIT  
**Author:** GreenhillEfka

PilotSuite HA is the canonical Home Assistant integration for the PilotSuite product.

## Install order

1. Install **PilotSuite Core** from `https://github.com/GreenhillEfka/pilotsuite-styx-core`.
2. Install **PilotSuite HA** from this repository.

## Canonical repo layout

- `README.md` , public entrypoint for this repository
- `custom_components/pilotsuite/` , canonical integration source
- `manifest.json` and `custom_components/pilotsuite/manifest.json` , canonical release metadata
- `docs/` , public install, user, testing, troubleshooting, and API notes
- legacy `copilot_ha` references, migration-only surfaces, not current release truth

## Installation

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for the full path.

Quick path:
1. Open HACS → Integrations → **Custom repositories**.
2. Add `https://github.com/GreenhillEfka/pilotsuite-styx-ha` as category **Integration**.
3. Install **PilotSuite HA**.
4. Restart Home Assistant.
5. Add integration **PilotSuite** in **Settings → Devices & Services**.

## First verification path

1. Confirm PilotSuite Core is already reachable.
2. Restart Home Assistant.
3. Add **PilotSuite** in **Devices & Services**.
4. Complete the config flow.
5. Confirm the integration loads from `custom_components/pilotsuite/` without legacy path guessing.

## Smoke test path

- install smoke: HACS or manual copy succeeds
- config smoke: config flow completes
- maintainer smoke: see [docs/TESTING.md](docs/TESTING.md)

## Documentation

- [Installation](docs/INSTALLATION.md)
- [User Guide](docs/USER_GUIDE.md)
- [Testing](docs/TESTING.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [API Reference](docs/API_REFERENCE.md)

## Support

- Issues: https://github.com/GreenhillEfka/pilotsuite-styx-ha/issues
- Core add-on repo: https://github.com/GreenhillEfka/pilotsuite-styx-core
- Changelog: [CHANGELOG.md](CHANGELOG.md)
