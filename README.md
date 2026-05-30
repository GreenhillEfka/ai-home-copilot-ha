# PilotSuite — Home Assistant Integration

**Version:** 20.0.8  
**License:** MIT  
**Author:** GreenhillEfka

## Overview

PilotSuite is an AI-powered home automation copilot that brings brain architecture, neural sensors, and local LLM conversation to Home Assistant.

## Product surface

PilotSuite HA should feel like one coherent Home Assistant product:
- **Home / Haushalt** for the operator overview
- **Suggestions** for next-step guidance
- **Voice** for state and settings coherence
- **PilotSuite Core** as the runtime companion behind richer features

## Features

- 🧠 **Brain Architecture** — Neural network-based home state understanding
- 🎯 **Presence Detection** — Multi-sensor fusion (Wi-Fi, BLE, mmWave)
- ⚡ **Energy Forecasting** — LSTM-based energy prediction & optimization
- 🗣️ **Voice Assistant** — Local STT/TTS with Whisper & Piper
- 📊 **Analytics Dashboard** — Real-time insights & recommendations
- 🔔 **Smart Notifications** — Context-aware alerts via Pushover & Telegram

## Installation

### Via HACS Custom Repository (recommended tester path)

1. Open HACS → Integrations → menu (⋮) → **Custom repositories**
2. Add `https://github.com/GreenhillEfka/pilotsuite-styx-ha`
3. Category: **Integration**
4. Search for **PilotSuite HA** in HACS and install it
5. Restart Home Assistant
6. Go to Settings → Devices & Services → Add Integration → **PilotSuite**
7. Choose one setup path in the config flow:
   - **Zero Config** for the default local Styx/Core endpoint
   - **Quick Start** for the guided path
   - **Manual Setup** for explicit host, port, and token control
8. If Core is offline, keep the created entry and use **Configure** later when Core becomes reachable

### Manual Installation fallback

1. Download the current GitHub release asset, or copy `custom_components/pilotsuite/` into `/config/custom_components/pilotsuite/`
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration → **PilotSuite**
4. Pair it with the PilotSuite Core add-on if you want full runtime features

## Exact tester path

Use this order for a clean external test:
1. HACS custom repository install
2. Restart Home Assistant
3. Add **PilotSuite** integration
4. Validate one of the three setup paths
5. Reconfigure later if Core is intentionally offline on first setup

## Requirements

- Home Assistant ≥ 2024.4.0
- [PilotSuite Core Add-on](https://github.com/GreenhillEfka/pilotsuite-styx-core) (for full functionality)

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Tester Journey](docs/TESTER_JOURNEY.md)
- [User Guide](docs/USER_GUIDE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Release honesty for testers

- The first public test line should be installed through the HACS custom-repository path above, unless normal HACS discovery is explicitly confirmed for that release.
- Public install wording should consistently read as: GitHub repo `pilotsuite-styx-ha`, HACS package **PilotSuite HA**, Home Assistant integration **PilotSuite**, domain `pilotsuite`.
- Legacy `copilot_ha` references may still exist internally for migration compatibility, but the installable product name and domain are **PilotSuite** / `pilotsuite`.

## Entity Naming Standard

For all new integration-owned Home Assistant entities, the canonical object-id prefix is `pilotsuite_`.

Examples:
- `sensor.pilotsuite_mood`
- `button.pilotsuite_backup`
- `binary_sensor.pilotsuite_online`

Legacy `copilot_ha_` IDs remain migration-only compatibility references and should not be introduced in new code.

## Support

- Issues: https://github.com/GreenhillEfka/pilotsuite-styx-ha/issues
- Discord: PilotSuite Community
- Documentation: https://docs.pilotsuite.ai

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

**Built with ❤️ by the PilotSuite Team**
