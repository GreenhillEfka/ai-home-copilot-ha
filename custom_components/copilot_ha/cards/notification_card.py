"""Notification Intelligence Lovelace Card — Slice 157.

Pushover/Telegram notification status and management.

Features:
- Multi-channel notification status (Pushover, Telegram, Email, etc.)
- Notification digest display
- Priority-based filtering
- Quick mute/unmute controls
- Notification history
- Delivery status tracking
- Responsive mobile-friendly design
- CSS animations for new notifications

Architecture:
- Card calls /api/v1/notifications endpoint
- Integrates with HA notification entities
- Supports multiple notification providers
- Real-time status updates
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

_LOGGER = logging.getLogger(__name__)


def notification_card() -> Dict[str, Any]:
    """Notification Card with multi-channel support.
    
    Features:
    - Channel status indicators
    - Pending notifications list
    - Priority badges
    - Quick actions (mute, mark read)
    - Delivery status tracking
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
                .notif-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 16px 20px;
                    background: rgba(0,0,0,0.3);
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                }
                .notif-title {
                    font-size: 18px;
                    font-weight: 600;
                    color: #fff;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .notif-count {
                    background: linear-gradient(135deg, #e74c3c, #c0392b);
                    color: #fff;
                    padding: 4px 10px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 600;
                    animation: pulse 2s ease-in-out infinite;
                }
                @keyframes pulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                }
                .channel-status {
                    display: flex;
                    gap: 8px;
                }
                .channel-indicator {
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    position: relative;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                .channel-indicator:hover {
                    transform: scale(1.2);
                }
                .channel-indicator.online {
                    background: linear-gradient(135deg, #2ecc71, #27ae60);
                    box-shadow: 0 0 10px rgba(46, 204, 113, 0.5);
                }
                .channel-indicator.offline {
                    background: #555;
                }
                .channel-indicator.error {
                    background: linear-gradient(135deg, #e74c3c, #c0392b);
                }
                .channel-tooltip {
                    position: absolute;
                    bottom: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(0,0,0,0.9);
                    color: #fff;
                    padding: 6px 10px;
                    border-radius: 6px;
                    font-size: 11px;
                    white-space: nowrap;
                    opacity: 0;
                    pointer-events: none;
                    transition: opacity 0.2s;
                }
                .channel-indicator:hover .channel-tooltip {
                    opacity: 1;
                }
                .notif-section {
                    padding: 16px;
                }
                .section-tabs {
                    display: flex;
                    gap: 8px;
                    margin-bottom: 16px;
                }
                .tab-btn {
                    padding: 8px 16px;
                    background: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 8px;
                    color: #aaa;
                    font-size: 13px;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .tab-btn.active {
                    background: rgba(52, 152, 219, 0.3);
                    border-color: #3498db;
                    color: #fff;
                }
                .tab-btn:hover {
                    background: rgba(255,255,255,0.1);
                }
                .notif-item {
                    background: rgba(255,255,255,0.05);
                    border-left: 4px solid #3498db;
                    padding: 14px 16px;
                    margin: 8px 0;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    animation: slideIn 0.3s ease-out;
                    position: relative;
                    overflow: hidden;
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
                .notif-item::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
                    transition: left 0.5s;
                }
                .notif-item:hover::before {
                    left: 100%;
                }
                .notif-item:hover {
                    background: rgba(255,255,255,0.1);
                    transform: translateX(8px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                }
                .notif-item.priority-high {
                    border-left-color: #e74c3c;
                }
                .notif-item.priority-medium {
                    border-left-color: #f39c12;
                }
                .notif-item.priority-low {
                    border-left-color: #2ecc71;
                }
                .notif-item.unread {
                    background: rgba(52, 152, 219, 0.1);
                }
                .notif-item.expanded {
                    border-left-width: 6px;
                }
                .notif-header-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 8px;
                }
                .notif-title-text {
                    color: #fff;
                    font-size: 14px;
                    font-weight: 600;
                    flex: 1;
                }
                .notif-time {
                    color: #aaa;
                    font-size: 12px;
                    margin-left: 12px;
                }
                .notif-message {
                    color: #ccc;
                    font-size: 13px;
                    line-height: 1.5;
                    margin-bottom: 10px;
                }
                .notif-meta {
                    display: flex;
                    gap: 12px;
                    font-size: 12px;
                    color: #888;
                }
                .notif-badge {
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    padding: 2px 8px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 4px;
                }
                .notif-actions {
                    display: flex;
                    gap: 8px;
                    margin-top: 12px;
                    padding-top: 12px;
                    border-top: 1px solid rgba(255,255,255,0.1);
                    display: none;
                }
                .notif-item.expanded .notif-actions {
                    display: flex;
                    animation: fadeIn 0.3s ease-out;
                }
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                .action-btn {
                    padding: 6px 12px;
                    background: rgba(255,255,255,0.1);
                    border: none;
                    border-radius: 6px;
                    color: #aaa;
                    font-size: 12px;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .action-btn:hover {
                    background: rgba(255,255,255,0.2);
                    color: #fff;
                }
                .action-btn.danger {
                    background: rgba(231, 76, 60, 0.3);
                    color: #e74c3c;
                }
                .action-btn.danger:hover {
                    background: rgba(231, 76, 60, 0.5);
                }
                .mute-banner {
                    background: rgba(243, 156, 18, 0.2);
                    border-left: 4px solid #f39c12;
                    padding: 12px 16px;
                    margin: 16px;
                    border-radius: 8px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .mute-text {
                    color: #f39c12;
                    font-size: 13px;
                }
                .unmute-btn {
                    background: #f39c12;
                    color: #000;
                    border: none;
                    padding: 6px 14px;
                    border-radius: 6px;
                    font-size: 12px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: all 0.2s;
                }
                .unmute-btn:hover {
                    background: #e67e22;
                    transform: scale(1.05);
                }
                .no-notifs {
                    text-align: center;
                    padding: 40px 20px;
                    color: #aaa;
                }
                .no-notifs-icon {
                    font-size: 48px;
                    margin-bottom: 12px;
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
                    .notif-header {
                        flex-direction: column;
                        gap: 12px;
                    }
                    .channel-status {
                        align-self: flex-end;
                    }
                }
            """
        },
        "card": {
            "type": "vertical-stack",
            "cards": [
                {
                    "type": "custom:template-entity-row",
                    "entity": "sensor.notification_status",
                    "name": "Notifications",
                    "icon": "mdi:bell"
                }
            ]
        }
    }


def _generate_notification_html() -> str:
    """Generate full Notification Card HTML/JS."""
    return """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Notifications</title>
  <style>
    :root {
      --bg-primary: #1a1a2e;
      --bg-secondary: #16213e;
      --accent-blue: #3498db;
      --accent-green: #2ecc71;
      --accent-red: #e74c3c;
      --accent-orange: #f39c12;
      --accent-purple: #9b59b6;
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
    
    .notif-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      background: rgba(0,0,0,0.3);
      border-radius: 12px;
      margin-bottom: 16px;
    }
    
    .notif-title {
      font-size: 18px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    
    .notif-count {
      background: linear-gradient(135deg, var(--accent-red), #c0392b);
      color: #fff;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.1); }
    }
    
    .channel-status {
      display: flex;
      gap: 8px;
    }
    
    .channel-indicator {
      width: 14px;
      height: 14px;
      border-radius: 50%;
      cursor: pointer;
      transition: all 0.3s;
    }
    
    .channel-indicator:hover {
      transform: scale(1.2);
    }
    
    .channel-indicator.online {
      background: linear-gradient(135deg, var(--accent-green), #27ae60);
      box-shadow: 0 0 10px rgba(46, 204, 113, 0.5);
    }
    
    .channel-indicator.offline {
      background: #555;
    }
    
    .section {
      background: rgba(255,255,255,0.05);
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 16px;
    }
    
    .section-tabs {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
    }
    
    .tab-btn {
      padding: 8px 16px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 8px;
      color: #aaa;
      cursor: pointer;
      transition: all 0.2s;
    }
    
    .tab-btn.active {
      background: rgba(52, 152, 219, 0.3);
      border-color: var(--accent-blue);
      color: #fff;
    }
    
    .notif-item {
      background: rgba(255,255,255,0.05);
      border-left: 4px solid var(--accent-blue);
      padding: 14px 16px;
      margin: 8px 0;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s;
    }
    
    .notif-item:hover {
      background: rgba(255,255,255,0.1);
      transform: translateX(8px);
    }
    
    .notif-item.priority-high {
      border-left-color: var(--accent-red);
    }
    
    .notif-item.priority-medium {
      border-left-color: var(--accent-orange);
    }
    
    .notif-item.priority-low {
      border-left-color: var(--accent-green);
    }
    
    .notif-title-text {
      color: #fff;
      font-size: 14px;
      font-weight: 600;
    }
    
    .notif-message {
      color: #ccc;
      font-size: 13px;
      margin-top: 6px;
      line-height: 1.5;
    }
    
    .notif-time {
      color: #aaa;
      font-size: 12px;
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
    <div class="notif-header">
      <div class="notif-title">
        🔔 Notifications
        <span class="notif-count" id="notifCount">0</span>
      </div>
      <div class="channel-status" id="channelStatus"></div>
    </div>
    
    <div class="section">
      <div class="section-tabs">
        <button class="tab-btn active" onclick="setFilter('all')">All</button>
        <button class="tab-btn" onclick="setFilter('unread')">Unread</button>
        <button class="tab-btn" onclick="setFilter('high')">High Priority</button>
      </div>
      <div id="notifications"></div>
    </div>
  </div>
  
  <script>
    const API_BASE = '/api/v1/notifications';
    let currentFilter = 'all';
    let notifications = [];
    let channels = {};
    
    async function loadNotifications() {
      try {
        const [notifRes, channelsRes] = await Promise.all([
          fetch(`${API_BASE}`),
          fetch(`${API_BASE}/channels`)
        ]);
        
        const notifData = await notifRes.json();
        const channelsData = await channelsRes.json();
        
        notifications = notifData.notifications || [];
        channels = channelsData.channels || {};
        
        renderChannelStatus();
        renderNotifications();
        updateCount();
      } catch (error) {
        console.error('Failed to load notifications:', error);
      }
    }
    
    function renderChannelStatus() {
      const channelNames = {
        'pushover': 'Pushover',
        'telegram': 'Telegram',
        'email': 'Email',
        'sms': 'SMS'
      };
      
      const html = Object.entries(channels).map(([id, ch]) => `
        <div class="channel-indicator ${ch.status || 'offline'}" title="${channelNames[id] || id}">
          <div class="channel-tooltip">${channelNames[id] || id}: ${ch.status || 'offline'}</div>
        </div>
      `).join('');
      
      document.getElementById('channelStatus').innerHTML = html;
    }
    
    function renderNotifications() {
      let filtered = notifications;
      
      if (currentFilter === 'unread') {
        filtered = notifications.filter(n => !n.read);
      } else if (currentFilter === 'high') {
        filtered = notifications.filter(n => n.priority === 'high');
      }
      
      if (filtered.length === 0) {
        document.getElementById('notifications').innerHTML = `
          <div class="no-notifs">
            <div class="no-notifs-icon">📭</div>
            <div>No notifications</div>
          </div>
        `;
        return;
      }
      
      const html = filtered.map(notif => `
        <div class="notif-item priority-${notif.priority || 'low'} ${notif.read ? '' : 'unread'}" 
             onclick="toggleNotif(this, '${notif.id}')">
          <div class="notif-header-row">
            <span class="notif-title-text">${escapeHtml(notif.title || 'No Title')}</span>
            <span class="notif-time">${formatTime(notif.timestamp)}</span>
          </div>
          <div class="notif-message">${escapeHtml(notif.message || '')}</div>
          <div class="notif-meta">
            <span class="notif-badge">📱 ${notif.channel || 'Unknown'}</span>
            ${notif.source ? `<span class="notif-badge">🔷 ${escapeHtml(notif.source)}</span>` : ''}
          </div>
        </div>
      `).join('');
      
      document.getElementById('notifications').innerHTML = html;
    }
    
    function toggleNotif(el, id) {
      el.classList.toggle('expanded');
    }
    
    function setFilter(filter) {
      currentFilter = filter;
      document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.toLowerCase().includes(filter) || 
          (filter === 'all' && btn.textContent === 'All') ||
          (filter === 'high' && btn.textContent.includes('High')));
      });
      renderNotifications();
    }
    
    function updateCount() {
      const unreadCount = notifications.filter(n => !n.read).length;
      document.getElementById('notifCount').textContent = unreadCount;
    }
    
    function formatTime(isoString) {
      if (!isoString) return '';
      const d = new Date(isoString);
      const now = new Date();
      const diff = now - d;
      
      if (diff < 60000) return 'Just now';
      if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
      return d.toLocaleDateString('de-DE', { day: 'numeric', month: 'short' });
    }
    
    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
    
    loadNotifications();
    
    // Auto-refresh every 30 seconds
    setInterval(loadNotifications, 30000);
  </script>
</body>
</html>"""


async def async_publish_notification_panel(hass, core_url: str, api_token: str):
    """Publish Notification panel to /config/www."""
    from pathlib import Path
    
    html = _generate_notification_html()
    panel_path = Path("/config/www/copilot_ha/notifications.html")
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    
    await hass.async_add_executor_job(panel_path.write_text, html, "utf-8")
    
    return panel_path
