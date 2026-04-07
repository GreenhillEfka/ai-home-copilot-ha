"""Calendar Lovelace Card — Slice 155.

Interactive calendar display for Home Assistant events.

Features:
- Multi-calendar support (Google, CalDAV, Local)
- Day/Week/Month views
- Event color coding by calendar
- Click to expand event details
- Quick add event button
- Responsive mobile-friendly design
- CSS animations for smooth transitions

Architecture:
- Card calls /api/v1/calendar/events endpoint
- Supports multiple calendar sources
- Real-time event updates
- Integration with HA calendar entities
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta

_LOGGER = logging.getLogger(__name__)


def calendar_card() -> Dict[str, Any]:
    """Calendar Card with multi-view support.
    
    Features:
    - Day/Week/Month toggle
    - Multiple calendar sources
    - Event color coding
    - Click to expand details
    - Quick add event
    - Mobile responsive
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
                .calendar-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 16px 20px;
                    background: rgba(0,0,0,0.3);
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                }
                .calendar-title {
                    font-size: 18px;
                    font-weight: 600;
                    color: #fff;
                }
                .view-toggle {
                    display: flex;
                    gap: 8px;
                }
                .view-btn {
                    padding: 6px 12px;
                    background: rgba(255,255,255,0.1);
                    border: 1px solid rgba(255,255,255,0.2);
                    border-radius: 6px;
                    color: #aaa;
                    font-size: 13px;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .view-btn.active {
                    background: linear-gradient(135deg, #3498db, #2ecc71);
                    color: #fff;
                    border-color: transparent;
                }
                .view-btn:hover {
                    background: rgba(255,255,255,0.2);
                }
                .calendar-nav {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                .nav-btn {
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    background: rgba(255,255,255,0.1);
                    border: none;
                    color: #fff;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }
                .nav-btn:hover {
                    background: rgba(52, 152, 219, 0.5);
                    transform: scale(1.1);
                }
                .current-date {
                    color: #fff;
                    font-size: 16px;
                    font-weight: 500;
                    min-width: 180px;
                    text-align: center;
                }
                .calendar-grid {
                    padding: 16px;
                }
                .day-view, .week-view, .month-view {
                    display: none;
                }
                .day-view.active, .week-view.active, .month-view.active {
                    display: block;
                }
                .event-item {
                    background: rgba(255,255,255,0.05);
                    border-left: 4px solid #3498db;
                    padding: 14px 16px;
                    margin: 8px 0;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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
                .event-item:hover {
                    background: rgba(255,255,255,0.1);
                    transform: translateX(8px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                }
                .event-item.expanded {
                    border-left-width: 6px;
                }
                .event-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 8px;
                }
                .event-title {
                    color: #fff;
                    font-size: 15px;
                    font-weight: 600;
                }
                .event-time {
                    color: #3498db;
                    font-size: 13px;
                    font-weight: 500;
                }
                .event-location {
                    color: #aaa;
                    font-size: 13px;
                    margin-top: 6px;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                .event-description {
                    color: #ccc;
                    font-size: 13px;
                    line-height: 1.5;
                    margin-top: 10px;
                    padding-top: 10px;
                    border-top: 1px solid rgba(255,255,255,0.1);
                    display: none;
                }
                .event-item.expanded .event-description {
                    display: block;
                    animation: fadeIn 0.3s ease-out;
                }
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                .calendar-filters {
                    display: flex;
                    gap: 8px;
                    padding: 12px 16px;
                    flex-wrap: wrap;
                    border-top: 1px solid rgba(255,255,255,0.1);
                }
                .filter-chip {
                    padding: 6px 12px;
                    background: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.2);
                    border-radius: 20px;
                    font-size: 12px;
                    color: #aaa;
                    cursor: pointer;
                    transition: all 0.2s;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                .filter-chip.active {
                    background: rgba(52, 152, 219, 0.3);
                    border-color: #3498db;
                    color: #fff;
                }
                .filter-chip:hover {
                    background: rgba(255,255,255,0.1);
                }
                .filter-color {
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                }
                .add-event-btn {
                    background: linear-gradient(135deg, #2ecc71, #27ae60);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    cursor: pointer;
                    font-weight: 600;
                    margin: 16px;
                    transition: all 0.2s;
                }
                .add-event-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(46, 204, 113, 0.4);
                }
                .no-events {
                    text-align: center;
                    padding: 40px 20px;
                    color: #aaa;
                }
                .no-events-icon {
                    font-size: 48px;
                    margin-bottom: 12px;
                }
                .month-grid {
                    display: grid;
                    grid-template-columns: repeat(7, 1fr);
                    gap: 4px;
                }
                .month-day-header {
                    text-align: center;
                    padding: 8px;
                    color: #aaa;
                    font-size: 12px;
                    font-weight: 600;
                }
                .month-day {
                    aspect-ratio: 1;
                    background: rgba(255,255,255,0.03);
                    border-radius: 6px;
                    padding: 4px;
                    font-size: 12px;
                    color: #fff;
                    position: relative;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .month-day:hover {
                    background: rgba(255,255,255,0.1);
                }
                .month-day.today {
                    background: rgba(52, 152, 219, 0.3);
                    border: 1px solid #3498db;
                }
                .month-day.other-month {
                    opacity: 0.3;
                }
                .month-day .event-dot {
                    position: absolute;
                    bottom: 4px;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 6px;
                    height: 6px;
                    border-radius: 50%;
                    background: #3498db;
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
                    .calendar-header {
                        flex-direction: column;
                        gap: 12px;
                    }
                    .view-toggle {
                        order: 2;
                    }
                    .calendar-nav {
                        order: 1;
                        width: 100%;
                        justify-content: space-between;
                    }
                    .current-date {
                        min-width: auto;
                        flex: 1;
                    }
                }
            """
        },
        "card": {
            "type": "vertical-stack",
            "cards": [
                {
                    "type": "custom:template-entity-row",
                    "entity": "sensor.calendar_status",
                    "name": "Calendar",
                    "icon": "mdi:calendar"
                }
            ]
        }
    }


def _generate_calendar_html() -> str:
    """Generate full Calendar Card HTML/JS."""
    return """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Calendar</title>
  <style>
    :root {
      --bg-primary: #1a1a2e;
      --bg-secondary: #16213e;
      --bg-card: #0f3460;
      --text-primary: #eee;
      --text-secondary: #aaa;
      --accent-blue: #3498db;
      --accent-green: #2ecc71;
      --accent-purple: #9b59b6;
      --accent-orange: #e67e22;
      --accent-red: #e74c3c;
    }
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      padding: 20px;
    }
    
    .calendar-container {
      max-width: 900px;
      margin: 0 auto;
    }
    
    .calendar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      background: rgba(0,0,0,0.3);
      border-radius: 12px;
      margin-bottom: 16px;
    }
    
    .calendar-title {
      font-size: 20px;
      font-weight: 600;
    }
    
    .view-toggle {
      display: flex;
      gap: 8px;
    }
    
    .view-btn {
      padding: 8px 16px;
      background: rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 8px;
      color: #aaa;
      cursor: pointer;
      transition: all 0.2s;
    }
    
    .view-btn.active {
      background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
      color: #fff;
    }
    
    .calendar-nav {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    
    .nav-btn {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: rgba(255,255,255,0.1);
      border: none;
      color: #fff;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    }
    
    .nav-btn:hover {
      background: var(--accent-blue);
      transform: scale(1.1);
    }
    
    .current-date {
      font-size: 16px;
      font-weight: 500;
      min-width: 180px;
      text-align: center;
    }
    
    .calendar-content {
      background: rgba(255,255,255,0.05);
      border-radius: 12px;
      padding: 16px;
    }
    
    .event-item {
      background: rgba(255,255,255,0.05);
      border-left: 4px solid var(--accent-blue);
      padding: 14px 16px;
      margin: 8px 0;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s;
    }
    
    .event-item:hover {
      background: rgba(255,255,255,0.1);
      transform: translateX(8px);
    }
    
    .event-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
    }
    
    .event-title {
      font-weight: 600;
    }
    
    .event-time {
      color: var(--accent-blue);
      font-size: 13px;
    }
    
    .event-description {
      display: none;
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid rgba(255,255,255,0.1);
      font-size: 13px;
      color: #ccc;
    }
    
    .event-item.expanded .event-description {
      display: block;
    }
    
    .month-grid {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 4px;
    }
    
    .month-day {
      aspect-ratio: 1;
      background: rgba(255,255,255,0.03);
      border-radius: 6px;
      padding: 4px;
      font-size: 12px;
      position: relative;
    }
    
    .month-day.today {
      background: rgba(52, 152, 219, 0.3);
      border: 1px solid var(--accent-blue);
    }
    
    .event-dot {
      position: absolute;
      bottom: 4px;
      left: 50%;
      transform: translateX(-50%);
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--accent-blue);
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
  <div class="calendar-container">
    <div class="calendar-header">
      <div class="calendar-nav">
        <button class="nav-btn" onclick="navigate(-1)">◀</button>
        <span class="current-date" id="currentDate"></span>
        <button class="nav-btn" onclick="navigate(1)">▶</button>
      </div>
      <div class="view-toggle">
        <button class="view-btn active" data-view="day" onclick="setView('day')">Day</button>
        <button class="view-btn" data-view="week" onclick="setView('week')">Week</button>
        <button class="view-btn" data-view="month" onclick="setView('month')">Month</button>
      </div>
    </div>
    
    <div class="calendar-content" id="calendarContent">
      <div class="loading">
        <div class="spinner"></div>
        <div>Loading events...</div>
      </div>
    </div>
  </div>
  
  <script>
    const API_BASE = '/api/v1/calendar';
    let currentDate = new Date();
    let currentView = 'day';
    let events = [];
    let calendars = [];
    
    async function loadEvents() {
      document.getElementById('calendarContent').innerHTML = `
        <div class="loading">
          <div class="spinner"></div>
          <div>Loading events...</div>
        </div>
      `;
      
      try {
        const start = getCurrentStart();
        const end = getCurrentEnd();
        
        const response = await fetch(`${API_BASE}/events?start=${start.toISOString()}&end=${end.toISOString()}`);
        const data = await response.json();
        events = data.events || [];
        calendars = data.calendars || [];
        
        renderCalendar();
        updateDateDisplay();
      } catch (error) {
        document.getElementById('calendarContent').innerHTML = `
          <div class="loading">
            <div>❌ Failed to load events: ${error.message}</div>
          </div>
        `;
      }
    }
    
    function getCurrentStart() {
      const d = new Date(currentDate);
      if (currentView === 'day') {
        d.setHours(0, 0, 0, 0);
      } else if (currentView === 'week') {
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? -6 : 1);
        d.setDate(diff);
        d.setHours(0, 0, 0, 0);
      } else if (currentView === 'month') {
        d.setDate(1);
        d.setHours(0, 0, 0, 0);
      }
      return d;
    }
    
    function getCurrentEnd() {
      const d = getCurrentStart();
      if (currentView === 'day') {
        d.setDate(d.getDate() + 1);
      } else if (currentView === 'week') {
        d.setDate(d.getDate() + 7);
      } else if (currentView === 'month') {
        d.setMonth(d.getMonth() + 1);
      }
      return d;
    }
    
    function updateDateDisplay() {
      const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      };
      if (currentView === 'month') {
        options.day = undefined;
      }
      document.getElementById('currentDate').textContent = currentDate.toLocaleDateString('de-DE', options);
    }
    
    function navigate(delta) {
      if (currentView === 'day') {
        currentDate.setDate(currentDate.getDate() + delta);
      } else if (currentView === 'week') {
        currentDate.setDate(currentDate.getDate() + (delta * 7));
      } else if (currentView === 'month') {
        currentDate.setMonth(currentDate.getMonth() + delta);
      }
      loadEvents();
    }
    
    function setView(view) {
      currentView = view;
      document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
      });
      loadEvents();
    }
    
    function renderCalendar() {
      if (currentView === 'month') {
        renderMonthView();
      } else {
        renderEventsView();
      }
    }
    
    function renderMonthView() {
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();
      const firstDay = new Date(year, month, 1);
      const lastDay = new Date(year, month + 1, 0);
      const startDay = firstDay.getDay() || 7;
      
      let html = '<div class="month-grid">';
      ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].forEach(day => {
        html += `<div class="month-day-header">${day}</div>`;
      });
      
      const today = new Date();
      for (let i = 1 - startDay + 1; i <= lastDay.getDate(); i++) {
        const day = i > 0 ? i : lastDay.getDate() + i;
        const isToday = i === today.getDate() && month === today.getMonth() && year === today.getFullYear();
        const hasEvents = events.some(e => {
          const eDate = new Date(e.start);
          return eDate.getDate() === day && eDate.getMonth() === month && eDate.getFullYear() === year;
        });
        
        html += `
          <div class="month-day ${i > 0 ? '' : 'other-month'} ${isToday ? 'today' : ''}">
            ${day}
            ${hasEvents ? '<div class="event-dot"></div>' : ''}
          </div>
        `;
      }
      html += '</div>';
      document.getElementById('calendarContent').innerHTML = html;
    }
    
    function renderEventsView() {
      if (!events || events.length === 0) {
        document.getElementById('calendarContent').innerHTML = `
          <div class="no-events">
            <div class="no-events-icon">📅</div>
            <div>No events for this period</div>
          </div>
        `;
        return;
      }
      
      const html = events.map(event => `
        <div class="event-item" onclick="toggleEvent(this)" style="border-left-color: ${event.calendar_color || '#3498db'}">
          <div class="event-header">
            <span class="event-title">${escapeHtml(event.title || 'No Title')}</span>
            <span class="event-time">${formatTime(event.start)} - ${formatTime(event.end)}</span>
          </div>
          ${event.location ? `<div class="event-location">📍 ${escapeHtml(event.location)}</div>` : ''}
          <div class="event-description">${escapeHtml(event.description || '')}</div>
        </div>
      `).join('');
      
      document.getElementById('calendarContent').innerHTML = html;
    }
    
    function toggleEvent(el) {
      el.classList.toggle('expanded');
    }
    
    function formatTime(isoString) {
      if (!isoString) return '';
      const d = new Date(isoString);
      return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
    }
    
    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
    
    // Initialize
    loadEvents();
  </script>
</body>
</html>"""


async def async_publish_calendar_panel(hass, core_url: str, api_token: str):
    """Publish Calendar panel to /config/www."""
    from pathlib import Path
    
    html = _generate_calendar_html()
    panel_path = Path("/config/www/copilot_ha/calendar.html")
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    
    await hass.async_add_executor_job(panel_path.write_text, html, "utf-8")
    
    return panel_path
