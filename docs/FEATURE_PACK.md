# PilotSuite Core — Complete Feature Pack Documentation

**Version:** 1.0.0  
**Date:** 2026-04-07  
**Status:** ✅ Complete

---

## 📦 FEATURE PACK OVERVIEW

This document covers all optional features added in the Feature Pack:

1. 🎨 **Additional Lovelace Cards** (5 new cards)
2. 📈 **Advanced Analytics Dashboards**
3. 🔔 **Notification Integrations** (Pushover, Telegram)
4. 📅 **Calendar Integrations** (Google, CalDAV, iCal, HA)
5. 🌤️ **Weather-based Automations**

---

## 🎨 LOVELACE CARDS

### Installation

Cards are automatically available after installation. Add to dashboard:

```yaml
type: custom:pilotsuite-notifications
title: Notifications
show_unread_only: true
max_notifications: 10
```

### Card 1: Notification Center

**Type:** `custom:pilotsuite-notifications`

**Features:**
- Display notifications from all channels
- Filter by read/unread
- Sort by timestamp or priority
- Dismiss notifications
- Quick actions

**Configuration:**

```yaml
type: custom:pilotsuite-notifications
title: Notifications
show_unread_only: true
max_notifications: 10
sort_by: timestamp  # timestamp, priority
filter_channels:
  - pushover
  - telegram
```

**Actions:**
- `dismiss_all` — Clear all notifications
- `mark_read` — Mark all as read

---

### Card 2: Calendar Integration

**Type:** `custom:pilotsuite-calendar`

**Features:**
- Multiple calendar sources
- Upcoming events display
- Filter by calendar
- Event details on click

**Configuration:**

```yaml
type: custom:pilotsuite-calendar
title: Upcoming Events
calendars:
  - calendar.family
  - calendar.work
days_to_show: 7
max_events: 10
```

**Actions:**
- `show_today` — Jump to today
- `show_week` — Show full week

---

### Card 3: Weather Automation

**Type:** `custom:pilotsuite-weather-automation`

**Features:**
- Current weather display
- Forecast visualization
- Weather-triggered automations
- Manual trigger buttons

**Configuration:**

```yaml
type: custom:pilotsuite-weather-automation
title: Weather & Automations
weather_entity: weather.home
show_forecast: true
forecast_days: 3
show_automations: true
```

**Actions:**
- `refresh_weather` — Update weather data
- `trigger_all` — Run all weather automations

---

### Card 4: Analytics Dashboard

**Type:** `custom:pilotsuite-analytics`

**Features:**
- Multiple metric visualization
- Time range selection
- Interactive charts
- Export capabilities

**Configuration:**

```yaml
type: custom:pilotsuite-analytics
title: System Analytics
metrics:
  - presence_confidence
  - energy_savings
  - automation_count
time_range: 7d
chart_type: line  # line, bar, pie
refresh_interval: 300
```

**Actions:**
- `set_range` — Change time range (1d, 7d, 30d)
- `export_data` — Export to CSV/JSON

---

### Card 5: System Health

**Type:** `custom:pilotsuite-system-health`

**Features:**
- Resource usage (CPU, Memory, Disk)
- Service status
- Error/warning display
- Quick actions

**Configuration:**

```yaml
type: custom:pilotsuite-system-health
title: System Health
show_resources: true
show_services: true
show_errors: true
refresh_interval: 60
```

**Actions:**
- `refresh` — Refresh status
- `restart` — Restart PilotSuite
- `view_logs` — Open logs

---

## 🔔 NOTIFICATION INTEGRATIONS

### Pushover Setup

1. **Create App:**
   - Go to https://pushover.net
   - Click "Create Application"
   - Get API token

2. **Get User Key:**
   - Log in to Pushover
   - Find your User Key

3. **Configure:**

```yaml
pilotsuite:
  notifications:
    pushover:
      api_token: !secret pushover_token
      user_key: !secret pushover_user
      sound: pushover  # Optional default sound
      priority_default: normal
```

4. **Secrets:**

```yaml
# secrets.yaml
pushover_token: your_api_token_here
pushover_user: your_user_key_here
```

### Telegram Setup

1. **Create Bot:**
   - Message @BotFather on Telegram
   - `/newbot`
   - Follow prompts
   - Save bot token

2. **Get Chat ID:**
   - Add bot to group/channel
   - Send message
   - Check logs for chat ID

3. **Configure:**

```yaml
pilotsuite:
  notifications:
    telegram:
      bot_token: !secret telegram_bot_token
      chat_ids:
        - "-1001234567890"  # Group chat
        - "123456789"  # Private chat
      parse_mode: HTML  # HTML or Markdown
```

4. **Secrets:**

```yaml
telegram_bot_token: bot_token_here
```

### Usage Examples

**Send Notification:**

```yaml
# Automation
- alias: "Notify on Motion"
  trigger:
    platform: state
    entity_id: binary_sensor.door
    to: "on"
  action:
    - service: pilotsuite.notify
      data:
        title: "Motion Detected"
        message: "Front door opened"
        priority: normal
        url: "http://homeassistant.local/cameras/front"
        url_title: "View Camera"
```

**Urgent Notification:**

```yaml
- service: pilotsuite.notify_urgent
  data:
    title: "ALERT"
    message: "Water leak detected!"
```

---

## 📅 CALENDAR INTEGRATIONS

### Google Calendar

1. **Enable API:**
   - Go to Google Cloud Console
   - Enable Calendar API
   - Create OAuth credentials

2. **Download Credentials:**
   - Download JSON file
   - Save to `/config/google_creds.json`

3. **Configure:**

```yaml
pilotsuite:
  calendar:
    google:
      credentials_file: /config/google_creds.json
      calendar_ids:
        - primary
        - family@group.calendar.google.com
```

### CalDAV (Nextcloud, iCloud, etc.)

```yaml
pilotsuite:
  calendar:
    caldav:
      url: https://nextcloud.example.com/remote.php/dav
      username: !secret caldav_user
      password: !secret caldav_pass
      calendar_names:
        - Home
        - Work
```

### iCal Files

```yaml
pilotsuite:
  calendar:
    ical:
      file_paths:
        - /config/calendars/holidays.ics
        - /config/calendars/garbage_collection.ics
      refresh_interval: 300
```

### Home Assistant Calendars

```yaml
pilotsuite:
  calendar:
    home_assistant: true
```

### Usage Examples

**Get Events:**

```yaml
- service: pilotsuite.get_calendar_events
  data:
    days: 7
    source: google  # Optional: google, caldav, ical, home_assistant
```

**Automation Based on Calendar:**

```yaml
- alias: "Leave Home Reminder"
  trigger:
    platform: time
    at: "08:00:00"
  condition:
    condition: template
    value_template: "{{ states.calendar.work.attributes.message != '' }}"
  action:
    - service: pilotsuite.notify
      data:
        title: "Meeting Today"
        message: "{{ states.calendar.work.attributes.message }}"
```

---

## 🌤️ WEATHER AUTOMATIONS

### Predefined Automations

The following automations are included by default:

| Name | Trigger | Action |
|------|---------|--------|
| Blinds - Too Sunny | Clear, >25°C, UV>6 | Close blinds |
| Irrigation - Dry & Hot | Humidity<40%, >22°C, Clear | Start irrigation |
| Heating - Cold | <15°C | Set heating to 21°C |
| Windows - Rain Coming | Rainy | Close windows |
| Ventilation - Good Weather | Clear, 18-26°C, 30-70% humidity | Open windows |

### Configuration

```yaml
pilotsuite:
  weather:
    weather_entity: weather.home
    evaluation_interval: 5  # minutes
    custom_rules:
      - name: "Pool Heating"
        trigger_conditions:
          temperature_min: 25
          condition: clear
        actions:
          - service: switch.turn_on
            entity_id: switch.pool_heater
        cooldown_minutes: 120
        priority: 1
```

### Custom Rules

```yaml
pilotsuite:
  weather:
    custom_rules:
      - name: "Storm Protection"
        trigger_conditions:
          condition: stormy
          wind_speed_min: 50
        actions:
          - service: cover.close_cover
            entity_id: cover.all_awnings
          - service: switch.turn_off
            entity_id: switch.outdoor_lights
        priority: 10
        cooldown_minutes: 30
      
      - name: "Frost Protection"
        trigger_conditions:
          temperature_max: 2
        actions:
          - service: switch.turn_on
            entity_id: switch.frost_protection
        priority: 5
```

### Manual Triggers

```yaml
# Button to trigger all weather automations
- type: button
  name: Run Weather Automations
  tap_action:
    action: call-service
    service: pilotsuite.evaluate_weather
```

---

## 📈 ANALYTICS DASHBOARDS

### Built-in Dashboards

**System Overview:**
- CPU Usage
- Memory Usage
- Request Rate
- Uptime

**Energy Analytics:**
- Power Consumption
- Solar Production
- Cost Savings
- Device Distribution

**Presence Analytics:**
- Current State
- Confidence
- History
- Sensor Status

**Automation Performance:**
- Total Automations
- Executions Today
- Execution Time
- Top Automations

### Export Data

**CSV Export:**

```python
from copilot_core.analytics.advanced_analytics import DataExporter

engine = hass.data["pilotsuite_analytics_engine"]
metrics = engine.get_metrics()
DataExporter.to_csv(metrics, "/config/analytics_export.csv")
```

**JSON Export:**

```python
DataExporter.to_json(metrics, "/config/analytics_export.json")
```

**Prometheus Format:**

```python
DataExporter.to_prometheus(metrics, "/config/metrics.prom")
```

---

## 🔧 TROUBLESHOOTING

### Cards Not Showing

1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R)
3. Check browser console for errors
4. Verify card type is correct

### Notifications Not Sending

1. Check API tokens/credentials
2. Verify chat IDs (Telegram)
3. Check rate limits
4. Review logs for errors

### Calendar Not Syncing

1. Verify credentials
2. Check calendar permissions
3. Ensure refresh interval is set
4. Review authentication logs

### Weather Automations Not Triggering

1. Check weather entity exists
2. Verify trigger conditions
3. Check cooldown periods
4. Review evaluation logs

---

## 📊 METRICS REFERENCE

### System Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `system_cpu_percent` | Gauge | CPU usage |
| `system_memory_percent` | Gauge | Memory usage |
| `system_disk_percent` | Gauge | Disk usage |
| `system_uptime_seconds` | Counter | Uptime |

### API Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `api_requests_total` | Counter | Total requests |
| `api_errors_total` | Counter | Total errors |
| `api_latency_seconds` | Histogram | Response time |

### Presence Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `presence_state` | Gauge | Home/Away |
| `presence_confidence` | Gauge | Confidence score |
| `sensor_active_count` | Gauge | Active sensors |

### Energy Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `energy_power_kw` | Gauge | Current power |
| `energy_savings_ct` | Counter | Savings |
| `energy_solar_kw` | Gauge | Solar production |

---

*Last updated: 2026-04-07*
*Version: 1.0.0*
