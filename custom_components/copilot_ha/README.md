# PilotSuite Home Assistant Integration

**Version:** 15.4.11  
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

## Installation

### Via HACS (Recommended)

1. Open HACS
2. Click "Integrations"
3. Click "+" (Custom Repository)
4. Add repository: `https://github.com/GreenhillEfka/pilotsuite-styx-ha`
5. Category: Integration
6. Search for "PilotSuite"
7. Click "Download"
8. Restart Home Assistant
9. Go to Settings → Devices & Services → Add Integration → Search "PilotSuite"

### Manual Installation

1. Copy `custom_components/copilot_ha` to your HA `custom_components` folder
2. Restart Home Assistant
3. Add integration via UI

## Configuration

Configure via UI:
1. Settings → Devices & Services → Add Integration → PilotSuite
2. Enter Core API URL (default: `http://localhost:8909`)
3. Enter API Token (if configured)
4. Complete wizard

## Support

- GitHub: https://github.com/GreenhillEfka/pilotsuite-styx-ha
- Issues: https://github.com/GreenhillEfka/pilotsuite-styx-ha/issues
