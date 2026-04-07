"""Weather Automation Lovelace Card — Slice 156.

Weather-based automation triggers and displays.

Features:
- Current weather conditions display
- Weather-based automation rules
- Forecast integration
- Automatic trigger suggestions
- Seasonal automation patterns
- Responsive mobile-friendly design
- CSS animations for weather effects

Architecture:
- Card calls /api/v1/weather/current and /api/v1/weather/forecast
- Integrates with HA weather entities
- Supports multiple weather providers
- Real-time condition updates
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

_LOGGER = logging.getLogger(__name__)


def weather_automation_card() -> Dict[str, Any]:
    """Weather Automation Card with trigger management.
    
    Features:
    - Current weather display with animations
    - Automation rule list
    - Quick toggle automations
    - Forecast integration
    - Weather-based suggestions
    """
    return {
        "type": "custom:mod-card",
        "card_mod": {
            "style": """
                ha-card {
                    padding: 0;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    border-radius: 16px;
                    overflow: hidden;
                }
                .weather-header {
                    padding: 24px 20px;
                    background: linear-gradient(135deg, #3498db 0%, #2ecc71 100%);
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                }
                .weather-header::before {
                    content: '';
                    position: absolute;
                    top: -50%;
                    left: -50%;
                    width: 200%;
                    height: 200%;
                    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                    animation: pulse 4s ease-in-out infinite;
                }
                @keyframes pulse {
                    0%, 100% { transform: scale(1); opacity: 0.5; }
                    50% { transform: scale(1.1); opacity: 0.8; }
                }
                .weather-temp {
                    font-size: 48px;
                    font-weight: 300;
                    color: #fff;
                    position: relative;
                    z-index: 1;
                }
                .weather-condition {
                    font-size: 18px;
                    color: rgba(255,255,255,0.9);
                    margin-top: 8px;
                    position: relative;
                    z-index: 1;
                }
                .weather-icon {
                    font-size: 64px;
                    margin-bottom: 12px;
                    position: relative;
                    z-index: 1;
                    animation: float 3s ease-in-out infinite;
                }
                @keyframes float {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-10px); }
                }
                .weather-details {
                    display: flex;
                    justify-content: center;
                    gap: 24px;
                    padding: 16px;
                    background: rgba(0,0,0,0.2);
                    position: relative;
                    z-index: 1;
                }
                .weather-detail {
                    text-align: center;
                }
                .weather-detail-label {
                    font-size: 12px;
                    color: rgba(255,255,255,0.7);
                    text-transform: uppercase;
                }
                .weather-detail-value {
                    font-size: 16px;
                    color: #fff;
                    font-weight: 600;
                    margin-top: 4px;
                }
                .automation-section {
                    padding: 20px;
                }
                .section-title {
                    font-size: 16px;
                    font-weight: 600;
                    color: #fff;
                    margin-bottom: 16px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .automation-item {
                    background: rgba(255,255,255,0.05);
                    border-radius: 10px;
                    padding: 14px 16px;
                    margin: 8px 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    transition: all 0.3s;
                    animation: slideIn 0.3s ease-out;
                }
                @keyframes slideIn {
                    from {
                        opacity: 0;
                        transform: translateX(-20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
                .automation-item:hover {
                    background: rgba(255,255,255,0.1);
                    transform: translateX(4px);
                }
                .automation-info {
                    flex: 1;
                }
                .automation-name {
                    color: #fff;
                    font-size: 14px;
                    font-weight: 600;
                    margin-bottom: 4px;
                }
                .automation-trigger {
                    color: #aaa;
                    font-size: 12px;
                }
                .automation-toggle {
                    position: relative;
                    width: 50px;
                    height: 26px;
                }
                .automation-toggle input {
                    opacity: 0;
                    width: 0;
                    height: 0;
                }
                .toggle-slider {
                    position: absolute;
                    cursor: pointer;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-color: rgba(255,255,255,0.2);
                    transition: 0.3s;
                    border-radius: 26px;
                }
                .toggle-slider:before {
                    position: absolute;
                    content: "";
                    height: 20px;
                    width: 20px;
                    left: 3px;
                    bottom: 3px;
                    background-color: white;
                    transition: 0.3s;
                    border-radius: 50%;
                }
                input:checked + .toggle-slider {
                    background: linear-gradient(135deg, #2ecc71, #27ae60);
                }
                input:checked + .toggle-slider:before {
                    transform: translateX(24px);
                }
                .forecast-section {
                    padding: 20px;
                    border-top: 1px solid rgba(255,255,255,0.1);
                }
                .forecast-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
                    gap: 12px;
                }
                .forecast-item {
                    background: rgba(255,255,255,0.05);
                    border-radius: 10px;
                    padding: 12px;
                    text-align: center;
                    transition: all 0.3s;
                }
                .forecast-item:hover {
                    background: rgba(255,255,255,0.1);
                    transform: translateY(-4px);
                }
                .forecast-day {
                    font-size: 12px;
                    color: #aaa;
                    margin-bottom: 8px;
                }
                .forecast-icon {
                    font-size: 32px;
                    margin-bottom: 8px;
                }
                .forecast-temp {
                    font-size: 14px;
                    color: #fff;
                    font-weight: 600;
                }
                .forecast-temp-low {
                    font-size: 12px;
                    color: #aaa;
                    margin-top: 4px;
                }
                .suggestion-banner {
                    background: linear-gradient(135deg, rgba(155, 89, 182, 0.3), rgba(52, 152, 219, 0.3));
                    border-left: 4px solid #9b59b6;
                    padding: 16px;
                    margin: 16px 20px;
                    border-radius: 8px;
                    animation: glow 2s ease-in-out infinite;
                }
                @keyframes glow {
                    0%, 100% { box-shadow: 0 0 10px rgba(155, 89, 182, 0.3); }
                    50% { box-shadow: 0 0 20px rgba(155, 89, 182, 0.6); }
                }
                .suggestion-title {
                    color: #fff;
                    font-size: 14px;
                    font-weight: 600;
                    margin-bottom: 6px;
                }
                .suggestion-text {
                    color: #ccc;
                    font-size: 13px;
                    line-height: 1.5;
                }
                .suggestion-action {
                    background: #9b59b6;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 13px;
                    cursor: pointer;
                    margin-top: 10px;
                    transition: all 0.2s;
                }
                .suggestion-action:hover {
                    background: #8e44ad;
                    transform: scale(1.05);
                }
                .loading {
                    text-align: center;
                    padding: 40px;
                    color: #aaa;
                }
                .spinner {
                    border: 3px solid rgba(255,255,255,0.1);
                    border-top-color: #3498db;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 16px;
                }
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                @media (max-width: 600px) {
                    .weather-details {
                        flex-wrap: wrap;
                        gap: 16px;
                    }
                    .forecast-grid {
                        grid-template-columns: repeat(3, 1fr);
                    }
                }
            """
        },
        "card": {
            "type": "vertical-stack",
            "cards": [
                {
                    "type": "custom:template-entity-row",
                    "entity": "sensor.weather_status",
                    "name": "Weather Automation",
                    "icon": "mdi:weather-partly-cloudy"
                }
            ]
        }
    }


def _generate_weather_automation_html() -> str:
    """Generate full Weather Automation Card HTML/JS."""
    return """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Weather Automation</title>
  <style>
    :root {
      --bg-primary: #1a1a2e;
      --bg-secondary: #16213e;
      --accent-blue: #3498db;
      --accent-green: #2ecc71;
      --accent-purple: #9b59b6;
      --accent-orange: #e67e22;
      --text-primary: #eee;
      --text-secondary: #aaa;
    }
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      padding: 20px;
    }
    
    .container {
      max-width: 800px;
      margin: 0 auto;
    }
    
    .weather-header {
      padding: 32px 20px;
      background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
      border-radius: 16px;
      text-align: center;
      margin-bottom: 20px;
      position: relative;
      overflow: hidden;
    }
    
    .weather-icon {
      font-size: 72px;
      margin-bottom: 16px;
      animation: float 3s ease-in-out infinite;
    }
    
    .weather-temp {
      font-size: 56px;
      font-weight: 300;
      color: #fff;
    }
    
    .weather-condition {
      font-size: 20px;
      color: rgba(255,255,255,0.9);
      margin-top: 8px;
    }
    
    .weather-details {
      display: flex;
      justify-content: center;
      gap: 24px;
      margin-top: 20px;
    }
    
    .weather-detail {
      text-align: center;
    }
    
    .weather-detail-label {
      font-size: 12px;
      color: rgba(255,255,255,0.7);
      text-transform: uppercase;
    }
    
    .weather-detail-value {
      font-size: 16px;
      color: #fff;
      font-weight: 600;
      margin-top: 4px;
    }
    
    @keyframes float {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-10px); }
    }
    
    .section {
      background: rgba(255,255,255,0.05);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 20px;
    }
    
    .section-title {
      font-size: 16px;
      font-weight: 600;
      color: #fff;
      margin-bottom: 16px;
    }
    
    .automation-item {
      background: rgba(255,255,255,0.05);
      border-radius: 10px;
      padding: 14px 16px;
      margin: 8px 0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: all 0.3s;
    }
    
    .automation-item:hover {
      background: rgba(255,255,255,0.1);
      transform: translateX(4px);
    }
    
    .automation-name {
      color: #fff;
      font-size: 14px;
      font-weight: 600;
    }
    
    .automation-trigger {
      color: #aaa;
      font-size: 12px;
      margin-top: 4px;
    }
    
    .toggle {
      position: relative;
      width: 50px;
      height: 26px;
    }
    
    .toggle input {
      opacity: 0;
      width: 0;
      height: 0;
    }
    
    .toggle-slider {
      position: absolute;
      cursor: pointer;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: rgba(255,255,255,0.2);
      transition: 0.3s;
      border-radius: 26px;
    }
    
    .toggle-slider:before {
      position: absolute;
      content: "";
      height: 20px;
      width: 20px;
      left: 3px;
      bottom: 3px;
      background-color: white;
      transition: 0.3s;
      border-radius: 50%;
    }
    
    input:checked + .toggle-slider {
      background: linear-gradient(135deg, var(--accent-green), #27ae60);
    }
    
    input:checked + .toggle-slider:before {
      transform: translateX(24px);
    }
    
    .forecast-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
      gap: 12px;
    }
    
    .forecast-item {
      background: rgba(255,255,255,0.05);
      border-radius: 10px;
      padding: 12px;
      text-align: center;
      transition: all 0.3s;
    }
    
    .forecast-item:hover {
      background: rgba(255,255,255,0.1);
      transform: translateY(-4px);
    }
    
    .forecast-icon {
      font-size: 32px;
      margin-bottom: 8px;
    }
    
    .forecast-temp {
      font-size: 14px;
      color: #fff;
      font-weight: 600;
    }
    
    .loading {
      text-align: center;
      padding: 40px;
    }
    
    .spinner {
      border: 3px solid rgba(255,255,255,0.1);
      border-top-color: var(--accent-blue);
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin: 0 auto 16px;
    }
    
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="container">
    <div class="weather-header" id="weatherHeader">
      <div class="loading">
        <div class="spinner"></div>
        <div>Loading weather...</div>
      </div>
    </div>
    
    <div class="section">
      <h3 class="section-title">⚡ Weather Automations</h3>
      <div id="automations"></div>
    </div>
    
    <div class="section">
      <h3 class="section-title">📅 7-Day Forecast</h3>
      <div class="forecast-grid" id="forecast"></div>
    </div>
  </div>
  
  <script>
    const API_BASE = '/api/v1/weather';
    
    const weatherIcons = {
      'clear-day': '☀️',
      'clear-night': '🌙',
      'cloudy': '☁️',
      'partly-cloudy-day': '⛅',
      'partly-cloudy-night': '☁️',
      'rain': '🌧️',
      'snow': '❄️',
      'fog': '🌫️',
      'wind': '💨',
      'thunderstorm': '⛈️'
    };
    
    async function loadWeather() {
      try {
        const [currentRes, forecastRes, autoRes] = await Promise.all([
          fetch(`${API_BASE}/current`),
          fetch(`${API_BASE}/forecast?days=7`),
          fetch(`${API_BASE}/automations`)
        ]);
        
        const current = await currentRes.json();
        const forecast = await forecastRes.json();
        const automations = await autoRes.json();
        
        renderWeather(current);
        renderForecast(forecast);
        renderAutomations(automations);
      } catch (error) {
        console.error('Failed to load weather:', error);
      }
    }
    
    function renderWeather(data) {
      const icon = weatherIcons[data.condition] || '🌡️';
      document.getElementById('weatherHeader').innerHTML = `
        <div class="weather-icon">${icon}</div>
        <div class="weather-temp">${Math.round(data.temperature)}°C</div>
        <div class="weather-condition">${data.condition.replace('-', ' ')}</div>
        <div class="weather-details">
          <div class="weather-detail">
            <div class="weather-detail-label">Humidity</div>
            <div class="weather-detail-value">${data.humidity}%</div>
          </div>
          <div class="weather-detail">
            <div class="weather-detail-label">Wind</div>
            <div class="weather-detail-value">${data.wind_speed} km/h</div>
          </div>
          <div class="weather-detail">
            <div class="weather-detail-label">Pressure</div>
            <div class="weather-detail-value">${data.pressure} hPa</div>
          </div>
        </div>
      `;
    }
    
    function renderForecast(data) {
      const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const forecast = data.forecast || [];
      
      const html = forecast.map((day, i) => `
        <div class="forecast-item">
          <div class="forecast-day">${i === 0 ? 'Today' : days[new Date(day.date).getDay()]}</div>
          <div class="forecast-icon">${weatherIcons[day.condition] || '🌡️'}</div>
          <div class="forecast-temp">${Math.round(day.temp_max)}°</div>
          <div class="forecast-temp-low">${Math.round(day.temp_min)}°</div>
        </div>
      `).join('');
      
      document.getElementById('forecast').innerHTML = html;
    }
    
    function renderAutomations(data) {
      const automations = data.automations || [];
      
      if (automations.length === 0) {
        document.getElementById('automations').innerHTML = `
          <div style="text-align: center; color: #aaa; padding: 20px;">
            No weather automations configured
          </div>
        `;
        return;
      }
      
      const html = automations.map(auto => `
        <div class="automation-item">
          <div class="automation-info">
            <div class="automation-name">${escapeHtml(auto.name)}</div>
            <div class="automation-trigger">Trigger: ${escapeHtml(auto.trigger)}</div>
          </div>
          <label class="toggle">
            <input type="checkbox" ${auto.enabled ? 'checked' : ''} 
                   onchange="toggleAutomation('${auto.id}', this.checked)"/>
            <span class="toggle-slider"></span>
          </label>
        </div>
      `).join('');
      
      document.getElementById('automations').innerHTML = html;
    }
    
    async function toggleAutomation(id, enabled) {
      try {
        await fetch(`${API_BASE}/automations/${id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled })
        });
      } catch (error) {
        console.error('Failed to toggle automation:', error);
      }
    }
    
    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
    
    loadWeather();
  </script>
</body>
</html>"""


async def async_publish_weather_panel(hass, core_url: str, api_token: str):
    """Publish Weather Automation panel to /config/www."""
    from pathlib import Path
    
    html = _generate_weather_automation_html()
    panel_path = Path("/config/www/copilot_ha/weather_automation.html")
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    
    await hass.async_add_executor_job(panel_path.write_text, html, "utf-8")
    
    return panel_path
