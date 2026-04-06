# PilotSuite Core — Complete Setup Guide

**Version:** 1.0.0  
**Last Updated:** 2026-04-07

---

## 🚀 QUICK START

### Option 1: HACS Installation (Recommended)

1. **Add Repository to HACS:**
   - Open HACS in Home Assistant
   - Click **⋮** → **Custom repositories**
   - URL: `https://github.com/GreenhillEfka/pilotsuite-styx-ha`
   - Category: **Integration**
   - Click **Add**

2. **Install:**
   - Search "PilotSuite Core" in HACS
   - Click **Download**
   - **Restart Home Assistant**

3. **Configure:**
   - Settings → Devices & Services → **+ Add Integration**
   - Search "PilotSuite"
   - Follow configuration wizard

---

### Option 2: Manual Installation

```bash
# SSH into Home Assistant
cd /config/custom_components
git clone https://github.com/GreenhillEfka/pilotsuite-styx-ha.git pilotsuite

# Install dependencies
pip install -r /config/custom_components/pilotsuite/requirements.txt

# Restart Home Assistant
```

---

### Option 3: Docker (Standalone)

```bash
# Clone repository
git clone https://github.com/GreenhillEfka/pilotsuite-styx-ha.git
cd pilotsuite-styx-ha

# Start with Docker Compose
docker-compose up -d

# Check status
docker-compose ps
```

**Services:**
- PilotSuite Core: http://localhost:8080
- Flower (Worker Monitor): http://localhost:5555
- Grafana (Dashboards): http://localhost:3000 (admin/admin)
- Prometheus (Metrics): http://localhost:9090

---

## 🔧 PREREQUISITES

### Required

- Home Assistant 2024.1+
- Python 3.10+
- Redis Server (for task queue)

### Optional

- Neo4j (for knowledge graph)
- Ollama (for local LLM)
- Prometheus + Grafana (for monitoring)

---

## 📋 CONFIGURATION

### Basic Configuration

```yaml
# configuration.yaml
pilotsuite:
  debug: false
  data_dir: /config/pilotsuite
  llm_model: ollama/qwen3.5:397b-cloud
  database_url: sqlite+aiosqlite:///./pilotsuite.db
  redis_url: redis://localhost:6379/0
```

### Notifications

```yaml
pilotsuite:
  notifications:
    pushover:
      api_token: !secret pushover_token
      user_key: !secret pushover_user
    telegram:
      bot_token: !secret telegram_bot_token
      chat_ids:
        - "-1001234567890"
```

### Calendar

```yaml
pilotsuite:
  calendar:
    google:
      credentials_file: /config/google_creds.json
      calendar_ids:
        - primary
    caldav:
      url: https://nextcloud.example.com/remote.php/dav
      username: !secret caldav_user
      password: !secret caldav_pass
```

### Weather Automations

```yaml
pilotsuite:
  weather:
    weather_entity: weather.home
    evaluation_interval: 5
    custom_rules:
      - name: "Pool Heating"
        trigger_conditions:
          temperature_min: 25
          condition: clear
        actions:
          - service: switch.turn_on
            entity_id: switch.pool_heater
```

### Multi-Home Sync

```yaml
pilotsuite:
  sync:
    home_id: main
    remote_homes:
      - home_id: vacation
        name: Vacation Home
        url: https://vacation.example.com
        api_token: !secret vacation_api_token
        sync_direction: bidirectional
```

---

## 🔨 WORKER SETUP

### Install Redis

```bash
# Debian/Ubuntu
sudo apt install redis-server
sudo systemctl enable redis
sudo systemctl start redis

# Verify
redis-cli ping  # Should return "PONG"
```

### Start Workers (Manual)

```bash
cd /config/clawd

# Start worker
celery -A copilot_core.celery_app worker --loglevel info --concurrency 4

# Start beat (scheduler)
celery -A copilot_core.celery_app beat --loglevel info

# Start flower (monitor)
celery -A copilot_core.celery_app flower --port=5555
```

### Start Workers (Script)

```bash
# Start all
/config/clawd/scripts/workers.sh start-all

# With Flower
/config/clawd/scripts/workers.sh start-all 4 --flower

# Check status
/config/clawd/scripts/workers.sh status
```

### Start Workers (systemd)

```bash
# Copy service files
sudo cp /config/clawd/systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable pilotsuite-worker
sudo systemctl enable pilotsuite-beat
sudo systemctl start pilotsuite-worker
sudo systemctl start pilotsuite-beat

# Check status
sudo systemctl status pilotsuite-worker
sudo systemctl status pilotsuite-beat
```

---

## 📊 MONITORING

### Access Dashboards

1. **Grafana:** http://localhost:3000 (admin/admin)
   - Import dashboard IDs from `monitoring/grafana/dashboards/`

2. **Flower:** http://localhost:5555
   - Real-time worker monitoring
   - Task results
   - Worker statistics

3. **Prometheus:** http://localhost:9090
   - Query metrics
   - Alert management

### Metrics Endpoints

- System: `http://localhost:8080/metrics`
- API: `http://localhost:8080/api/v1/metrics`

---

## 🔧 TROUBLESHOOTING

### Workers Not Starting

1. **Check Redis:**
   ```bash
   redis-cli ping
   sudo systemctl status redis
   ```

2. **Check Logs:**
   ```bash
   tail -f /config/pilotsuite/logs/celery.log
   journalctl -u pilotsuite-worker -f
   ```

3. **Check Dependencies:**
   ```bash
   pip install -r /config/clawd/copilot_core/requirements.txt
   ```

### Integration Not Showing

1. **Clear Cache:**
   ```bash
   rm -rf /config/__pycache__
   rm -rf /config/custom_components/pilotsuite/__pycache__
   ```

2. **Restart HA:**
   ```bash
   ha core restart
   ```

### Database Errors

1. **Check Permissions:**
   ```bash
   chown -R homeassistant:homeassistant /config/pilotsuite
   ```

2. **Run Migrations:**
   ```bash
   python3 -c "from copilot_core.database.migrations import *; m = MigrationManager(); register_default_migrations(m); import asyncio; asyncio.run(m.run())"
   ```

---

## 📖 NEXT STEPS

1. **Configure Lovelace Dashboard**
   - Add custom cards from `custom_cards/`
   - Import dashboards from `dashboards/`

2. **Set Up Automations**
   - Review predefined scenes
   - Configure weather automations
   - Set up calendar triggers

3. **Enable Notifications**
   - Configure Pushover/Telegram
   - Test notification delivery

4. **Monitor Performance**
   - Access Grafana dashboards
   - Set up alerts
   - Review worker logs

---

## 🆘 SUPPORT

- **Documentation:** https://github.com/GreenhillEfka/pilotsuite-styx-ha/docs
- **Issues:** https://github.com/GreenhillEfka/pilotsuite-styx-ha/issues
- **Discussions:** https://github.com/GreenhillEfka/pilotsuite-styx-ha/discussions
- **Discord:** https://discord.gg/clawd

---

*Last updated: 2026-04-07*
*Version: 1.0.0*
