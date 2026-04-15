# PilotSuite — Home Assistant Integration

**Version:** 20.0.8  
**License:** MIT  
**Author:** GreenhillEfka

## Overview

PilotSuite is an AI-powered home automation copilot that brings brain architecture, neural sensors, and local LLM conversation to Home Assistant.

## Features

- 🧠 **Brain Architecture** — Neural network-based home state understanding
- 🎯 **Presence Detection** — Multi-sensor fusion (Wi-Fi, BLE, mmWave)
- ⚡ **Energy Forecasting** — LSTM-based energy prediction & optimization
- 🗣️ **Voice Assistant** — Local STT/TTS with Whisper & Piper
- 📊 **Analytics Dashboard** — Real-time insights & recommendations
- 🔔 **Smart Notifications** — Context-aware alerts via Pushover & Telegram

## Installation

### Via HACS (Recommended)

1. Open HACS → Integrations
2. Search for "PilotSuite"
3. Click "Download"
4. Restart Home Assistant
5. Go to Settings → Devices & Services → Add Integration → PilotSuite

### Manual Installation

1. Copy `custom_components/pilotsuite/` to `/config/custom_components/`
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration → PilotSuite

## Requirements

- Home Assistant ≥ 2024.4.0
- [PilotSuite Core Add-on](https://github.com/GreenhillEfka/pilotsuite-styx-core) (for full functionality)

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [User Guide](docs/USER_GUIDE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

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
