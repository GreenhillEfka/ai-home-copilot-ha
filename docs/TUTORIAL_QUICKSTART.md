# PilotSuite Core — Quick Start Tutorial

**Time:** 30 minutes  
**Difficulty:** Beginner  
**Prerequisites:** Home Assistant 2024.1+

---

## Step 1: Installation (5 minutes)

### Option A: HACS (Recommended)

1. Open Home Assistant
2. Go to **HACS** → **Integrations**
3. Click **⋮** → **Custom repositories**
4. Add: `https://github.com/GreenhillEfka/pilotsuite-styx-ha`
5. Category: **Integration**
6. Click **Add**
7. Search "PilotSuite Core" → **Download**
8. **Restart Home Assistant**

### Option B: Manual

```bash
# SSH into Home Assistant
cd /config/custom_components
git clone https://github.com/GreenhillEfka/pilotsuite-styx-ha.git pilotsuite
```

---

## Step 2: Basic Configuration (5 minutes)

Add to `/config/configuration.yaml`:

```yaml
pilotsuite:
  debug: false
  data_dir: /config/pilotsuite
```

**Restart Home Assistant**

---

## Step 3: Verify Installation (2 minutes)

1. Go to **Settings** → **Devices & Services**
2. Verify "PilotSuite Core" is listed
3. Check **Settings** → **System** → **Logs**
4. No errors = Success! ✅

---

## Step 4: Enable Presence Detection (5 minutes)

### Add Motion Sensors

```yaml
# configuration.yaml
pilotsuite:
  presence:
    sensors:
      - binary_sensor.living_room_motion
      - binary_sensor.bedroom_motion
      - binary_sensor.kitchen_motion
```

### Check Presence Status

1. Go to **Developer Tools** → **States**
2. Search for `presence.home`
3. Should show `home` or `away`

---

## Step 5: Create First Automation (5 minutes)

### Habit Learning Automation

```yaml
# automations.yaml
- alias: "PilotSuite Learn Morning Routine"
  trigger:
    platform: time
    at: "07:00:00"
  action:
    - service: light.turn_on
      target:
        entity_id: light.living_room
    - service: climate.set_temperature
      target:
        entity_id: climate.living_room
      data:
        temperature: 22
    - service: pilotsuite.learn_pattern
      data:
        user_id: user_1
        trigger:
          type: time
          at: "07:00"
        action:
          entity_id: light.living_room
          service: light.turn_on
```

### Let It Learn

Run this automation for 3-5 days. PilotSuite will:
- Learn the pattern
- Suggest automations
- Eventually auto-execute

---

## Step 6: Enable Energy Optimization (5 minutes)

### Configure Energy Devices

```yaml
# configuration.yaml
pilotsuite:
  energy:
    forecasting_enabled: true
    scheduler_enabled: true
    devices:
      - entity_id: sensor.wallbox_power
        type: ev_charger
      - entity_id: climate.heat_pump
        type: heat_pump
```

### Run Optimization

```yaml
# Add this automation
- alias: "PilotSuite Optimize Energy"
  trigger:
    platform: time
    at: "20:00:00"
  action:
    - service: pilotsuite.optimize_energy
      data:
        horizon_hours: 24
```

### Check Results

1. Go to **Developer Tools** → **Services**
2. Call `pilotsuite.get_energy_forecast`
3. View optimization schedule

---

## Step 7: Enable REST API (3 minutes)

### Configure API

```yaml
# configuration.yaml
pilotsuite:
  api:
    enabled: true
    host: 0.0.0.0
    port: 8080
```

### Get API Token

```bash
curl -X POST http://localhost:8080/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "test_key_12345", "scope": "read"}'
```

### Test API

```bash
curl -X GET http://localhost:8080/api/v1/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Step 8: Install Lovelace Cards (5 minutes)

### Add to Dashboard

1. Open Dashboard
2. Click **⋮** → **Edit Dashboard**
3. Click **+** → **Manual**
4. Add card:

```yaml
type: custom:pilotsuite-brain-graph
title: Knowledge Graph
height: 400
```

### Available Cards

- `pilotsuite-brain-graph` — Graph visualization
- `pilotsuite-habit-pattern` — Pattern display
- `pilotsuite-energy-optimization` — Energy dashboard
- `pilotsuite-presence` — Presence status
- `pilotsuite-suggestions` — Automation suggestions

---

## 🎉 YOU'RE DONE!

### What You Have Now:

✅ Presence detection with multi-sensor fusion  
✅ Habit learning automation  
✅ Energy optimization  
✅ REST API access  
✅ Lovelace dashboard cards  

---

## Next Steps

### Week 1: Let It Learn
- Run your normal routines
- PilotSuite observes and learns
- Check suggestions daily

### Week 2: Review & Refine
- Review learned patterns
- Accept/reject suggestions
- Fine-tune configuration

### Week 3: Advanced Features
- Enable voice pipeline
- Configure knowledge graph
- Set up multi-home sync

### Month 1: Optimization
- Review energy savings
- Analyze automation efficiency
- Share feedback on GitHub

---

## Troubleshooting

### Presence Not Working

1. Check sensor entities exist
2. Verify sensor states change
3. Lower Wilson threshold: `wilson_confidence: 0.8`

### API Not Responding

1. Check port 8080 is free
2. Verify firewall allows traffic
3. Check logs for errors

### Lovelace Cards Not Showing

1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R)
3. Check HACS installation

---

## Getting Help

- **Documentation:** https://github.com/GreenhillEfka/pilotsuite-styx-ha/docs
- **Issues:** https://github.com/GreenhillEfka/pilotsuite-styx-ha/issues
- **Discussions:** https://github.com/GreenhillEfka/pilotsuite-styx-ha/discussions

---

**Congratulations! You're now a PilotSuite power user!** 🚀

*Last updated: 2026-04-07*
*Version: 1.0.0*
