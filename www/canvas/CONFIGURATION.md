# Canvas Dashboard - HA Configuration Guide

## Overview
Deployed Canvas dashboard for Home Assistant Lovelace UI with real-time zone monitoring, mood gauges, and neural network visualization.

## File Structure
```
/config/www/canvas/
├── pilotsuite_canvas_dashboard.html   # Main dashboard (all components)
├── pilotsuite_functions.html          # Original template
├── lovelace-card.yaml                 # HA integration config
├── CONFIGURATION.md                   # This file
└── README.md                          # Quick start guide
```

## Installation

### Method 1: Direct Copy (Recommended)
```bash
# Copy HTML files to HA www folder
cp /config/.openclaw/workspace-viewona/pilotsuite_canvas_dashboard.html /config/www/canvas/
cp /config/.openclaw/workspace-viewona/pilotsuite_functions.html /config/www/canvas/

# Or if using /config/.openclaw/www/
cp /config/.openclaw/workspace-viewona/pilotsuite_canvas_dashboard.html /config/.openclaw/www/canvas/
```

### Method 2: Git Clone (Development)
```bash
# If working in the repo
cd /config/.openclaw
# Changes are already in workspace, copy as needed
```

## Home Assistant Configuration

### Step 1: Add Resource
Go to **Settings** → **Devices & Services** → **Lovelace Dashboards** → **Resources**

Click **"+ ADD RESOURCE"**:
- **URL:** `/local/canvas/pilotsuite_canvas_dashboard.html`
- **Resource Type:** `module`

### Step 2: Create Dashboard Card
Add to your Lovelace dashboard using the following YAML:

```yaml
type: iframe
url: /local/canvas/pilotsuite_canvas_dashboard.html
aspect_ratio: 100%
```

Or use the provided `lovelace-card.yaml` template.

### Step 3: Alternative - Raw HTML Card
For more control, use the `custom:html-card` (requires installation):

```yaml
type: custom:html-card
content: |
  <iframe src="/local/canvas/pilotsuite_canvas_dashboard.html" 
          style="width:100%; height:800px; border:none; border-radius:16px;"
          sandbox="allow-scripts allow-same-origin">
  </iframe>
```

## Canvas Dashboard Features

### 1. Zone Dashboard
- Real-time zone status monitoring
- Temperature, humidity, device count, energy metrics
- Device online/offline indicators
- Hover animations and interactive cards

### 2. Canvas Zone Editor
- Interactive zone positioning
- Drag & drop functionality
- Grid background for alignment
- Export layout to JSON

### 3. Neuron Graph Visualization
- D3.js force-directed graph
- 14 neurons (3 input, 8 hidden, 3 output)
- 24 weighted connections
- Real-time state updates

### 4. Mood Gauges
- System mood indicator
- User mood indicator  
- Network mood indicator
- Circular progress with color coding

## Theme Integration

The dashboard uses CSS variables that can be overridden in HA themes:

```yaml
# In themes.yaml
pilot-suite-dark:
  primary-color: '#4CAF50'
  accent-color: '#FF5722'
  paper-card-background-color: '#0b0f14'
  paper-listbox-background-color: '#151a23'
  text-primary-color: '#e5e7eb'
```

## WebSocket Integration

The dashboard supports real-time updates via Home Assistant WebSocket API:

```javascript
// Connection URL: ws://<HA_URL>/api/websocket
// Subscribe to state changes for live updates
```

## Troubleshooting

### Dashboard not loading
- Check browser console for CORS errors
- Verify HTML files are in correct location
- Ensure resource is added in Lovelace settings

### WebGL errors
- Update browser to latest version
- Check graphics driver updates
- Try in different browser

### Data not updating
- Verify WebSocket connection
- Check HA API accessibility
- Ensure sensors/entities exist in HA

## URL Access

- **Local URL:** `http://<ha-ip>:8123/local/canvas/pilotsuite_canvas_dashboard.html`
- **External URL:** `https://<domain>.duckdns.org/local/canvas/pilotsuite_canvas_dashboard.html`

## Maintenance

### Updating Files
```bash
# From workspace
cp /config/.openclaw/workspace-viewona/pilotsuite_canvas_dashboard.html /config/www/canvas/

# Or from git repo
git pull origin main
# Then copy to www folder as needed
```

### Backup
```bash
cp -r /config/www/canvas /config/www/canvas.backup.$(date +%Y%m%d)
```

---

**Last Updated:** 2026-03-03 21:09 GMT+1  
**Version:** 1.0.0  
**Author:** Viewona (3D Vision Specialist)
