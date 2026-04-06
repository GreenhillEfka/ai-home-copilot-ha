# PilotSuite Core — Installation Guide

## Prerequisites

- Home Assistant 2024.1.0 or newer
- Python 3.10+
- 2GB free disk space
- 4GB RAM recommended

---

## Installation Methods

### Method 1: HACS (Recommended)

#### Step 1: Add Custom Repository

1. Open Home Assistant
2. Go to **HACS** → **Integrations**
3. Click **⋮** (three dots) → **Custom repositories**
4. Enter:
   - **Repository:** `https://github.com/GreenhillEfka/pilotsuite-styx-ha`
   - **Category:** `Integration`
5. Click **Add**

#### Step 2: Install PilotSuite Core

1. Search for "PilotSuite Core" in HACS
2. Click on it
3. Click **Download**
4. Select version: `1.0.0-rc2` (or latest)
5. Click **Download** again
6. **Restart Home Assistant**

#### Step 3: Configure

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "PilotSuite Core"
4. Follow configuration wizard

---

### Method 2: Manual Installation

#### Step 1: Clone Repository

```bash
# SSH into Home Assistant
ssh homeassistant

# Navigate to custom_components
cd /config/custom_components

# Clone repository
git clone https://github.com/GreenhillEfka/pilotsuite-styx-ha.git pilotsuite
```

#### Step 2: Add Configuration

Add to `/config/configuration.yaml`:

```yaml
pilotsuite:
  debug: false
  data_dir: /config/pilotsuite
  llm_model: ollama/qwen3.5:397b-cloud
```

#### Step 3: Restart Home Assistant

```bash
# In Home Assistant UI
Settings → System → Restart
```

---

## Post-Installation

### Verify Installation

1. Go to **Settings** → **Devices & Services**
2. Verify "PilotSuite Core" is listed
3. Check **Settings** → **System** → **Logs** for errors

### Initial Configuration

#### 1. Configure LLM (Optional)

```yaml
pilotsuite:
  llm:
    provider: ollama
    model: qwen3.5:397b-cloud
    base_url: http://localhost:11434
```

#### 2. Configure Presence Sensors

```yaml
pilotsuite:
  presence:
    sensors:
      - binary_sensor.living_room_motion
      - binary_sensor.bedroom_motion
      - sensor.wifi_presence
```

#### 3. Configure Energy Devices

```yaml
pilotsuite:
  energy:
    devices:
      - entity_id: sensor.wallbox_power
        type: ev_charger
      - entity_id: climate.heat_pump
        type: heat_pump
      - entity_id: sensor.battery_soc
        type: battery
```

---

## Dependencies

### Required

Installed automatically:
- `aiohttp>=3.9.0`
- `numpy>=1.24.0`
- `scikit-learn>=1.3.0`
- `fastapi>=0.104.0`
- `pyjwt>=2.8.0`

### Optional

For full functionality:

#### Ollama (Local LLM)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull qwen3.5:397b-cloud
```

#### OR-Tools (Energy Optimization)

```bash
pip install ortools>=9.8.0
```

#### Neo4j (Knowledge Graph)

```bash
# Docker
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  neo4j:latest
```

---

## Troubleshooting

### Installation Fails

**Problem:** HACS shows "Download failed"

**Solution:**
```bash
# Check disk space
df -h /config

# Check permissions
ls -la /config/custom_components/

# Manual install as fallback
cd /config/custom_components
git clone https://github.com/GreenhillEfka/pilotsuite-styx-ha.git pilotsuite
```

### Integration Not Showing

**Problem:** PilotSuite Core not in integrations list

**Solution:**
1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R)
3. Check logs: **Settings** → **System** → **Logs**
4. Restart Home Assistant

### API Server Won't Start

**Problem:** Port 8080 already in use

**Solution:**
```yaml
pilotsuite:
  api:
    port: 8081  # Change port
```

### Memory Issues

**Problem:** Out of memory errors

**Solution:**
```yaml
pilotsuite:
  ml:
    max_cache_size: 1000  # Reduce cache
  rag:
    max_vectors: 10000    # Limit vectors
```

---

## Update

### Via HACS

1. Go to **HACS** → **Integrations**
2. Find "PilotSuite Core"
3. Click **Update** (if available)
4. Restart Home Assistant

### Manual Update

```bash
cd /config/custom_components/pilotsuite
git pull
```

---

## Uninstall

### Via HACS

1. Go to **HACS** → **Integrations**
2. Click "PilotSuite Core"
3. Click **⋮** → **Uninstall**

### Manual

```bash
# Remove integration
rm -rf /config/custom_components/pilotsuite

# Remove data
rm -rf /config/pilotsuite

# Remove from configuration.yaml
# Edit /config/configuration.yaml and remove pilotsuite: section
```

---

## Next Steps

After installation:

1. **Configure sensors** — Presence, energy, environment
2. **Set up automations** — Habit learning, patterns
3. **Enable API** — For external integrations
4. **Install Lovelace cards** — Dashboard visualization
5. **Configure voice** — STT/TTS pipeline

---

## Support

- **GitHub Issues:** https://github.com/GreenhillEfka/pilotsuite-styx-ha/issues
- **Discussions:** https://github.com/GreenhillEfka/pilotsuite-styx-ha/discussions
- **Documentation:** https://github.com/GreenhillEfka/pilotsuite-styx-ha/tree/main/docs
