# PilotSuite Home Assistant Integration

**Version:** 1.0.0-rc2  
**Home Assistant:** 2024.4.0+  
**Integration Type:** Hub (local_push)

PilotSuite brings AI-powered home automation to Home Assistant with local-first privacy.

## Features

### 🤖 AI Core
- **Brain Graph** — Entity relationship learning and pattern detection
- **Mood Engine** — Comfort, Joy, and Frugality scoring per zone
- **Presence Detection** — Bayesian multi-sensor fusion
- **Energy Forecasting** — LSTM-based load prediction

### 🔧 Automation
- **Habitus Miner** — Behavioral pattern discovery (A→B rules)
- **Autonomy Engine** — Rule-based automation with context awareness
- **Anomaly Detection** — Sigma-deviation based alerting

### 🎙️ Voice
- **Voice Pipeline** — STT → Intent → LLM → TTS
- **Intent Router** — Routes commands to HA services or LLM
- **Multi-Language** — German and English commands

### 📊 Dashboard
- **9 Custom Lovelace Cards** — Zone, Brain, Voice, Energy, and more
- **Backend UI** — Full administrative interface
- **SOTA Theme** — Modern dark theme with accent colors

## Installation

### Via HACS (Recommended)
1. Open HACS in Home Assistant
2. Go to Integrations
3. Search for "PilotSuite"
4. Click Install

### Manual Installation
1. Copy `custom_components/copilot_ha/` to your Home Assistant's `custom_components/` folder
2. Restart Home Assistant
3. Add the PilotSuite integration via Settings → Devices & Services

## Configuration

### Quick Start (Zero-Config)
1. Add the integration
2. Enter your PilotSuite Core URL (default: `http://homeassistant.local:8909`)
3. Provide your API token
4. PilotSuite auto-discovers zones and entities

### Manual Setup
1. Enter Core endpoint URL
2. Configure zones manually
3. Select features to enable
4. Review and confirm

## Requirements

- Home Assistant 2024.4.0+
- PilotSuite Core running on your network
- API token from PilotSuite Core admin panel

## Permissions

PilotSuite requires the following Home Assistant permissions:
- `conversation` — Voice commands
- `history` — Learning from historical data
- `http` — Core communication
- `recorder` — Data persistence
- `stt` / `tts` — Speech processing
- `tag` — Entity tagging
- `webhook` — Event webhooks

## Support

- **Documentation:** https://docs.pilotsuite.ai
- **Issue Tracker:** https://github.com/GreenhillEfka/pilotsuite-styx-ha/issues
- **Discord:** https://discord.gg/pilotsuite

## License

MIT License
