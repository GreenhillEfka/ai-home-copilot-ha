"""Security Overview Panel v1.0 — Slice 142.

Interactive security dashboard showing:
- Circuit breaker status
- Rate limiting status
- Auth/token health
- API performance metrics
- Anomaly alerts
- System health summary

Privacy-first: all data stays local.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import html
import json
from pathlib import Path
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant

from .client import PilotSuiteCoreClient, CoreClientConfig


@dataclass
class SecurityStatus:
    """Security status data."""
    circuit_breaker_tripped: list[str]
    rate_limit_remaining: int
    auth_valid: bool
    api_latency_ms: float
    anomaly_alerts: list[dict]
    system_health: dict


def _sanitize(value: Any) -> str:
    """Sanitize text for HTML output."""
    if value is None:
        return ""
    return html.escape(str(value))


def _generate_security_panel_html(status: dict) -> str:
    """Generate interactive security overview HTML."""
    
    cb_tripped = status.get("circuit_breaker", {}).get("tripped", [])
    cb_state = status.get("circuit_breaker", {}).get("state", "closed")
    rate_limit = status.get("rate_limit", {})
    auth = status.get("auth", {})
    perf = status.get("performance", {})
    anomalies = status.get("anomaly", {}).get("alerts", [])
    system = status.get("system", {})
    
    # Color coding
    cb_color = "green" if cb_state == "closed" else ("orange" if cb_state == "half_open" else "red")
    auth_color = "green" if auth.get("valid", False) else "red"
    anomaly_count = len(anomalies)
    anomaly_color = "green" if anomaly_count == 0 else ("orange" if anomaly_count < 5 else "red")
    
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PilotSuite Security Overview</title>
  <style>
    :root {{
      --bg-primary: #1a1a2e;
      --bg-secondary: #16213e;
      --bg-card: #0f3460;
      --text-primary: #eee;
      --text-secondary: #aaa;
      --accent-green: #00d26a;
      --accent-orange: #f5a623;
      --accent-red: #e74c3c;
      --accent-blue: #3498db;
    }}
    
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      padding: 20px;
      min-height: 100vh;
    }}
    
    .header {{
      text-align: center;
      margin-bottom: 30px;
      padding: 20px;
      background: var(--bg-secondary);
      border-radius: 12px;
    }}
    
    .header h1 {{
      font-size: 28px;
      margin-bottom: 8px;
    }}
    
    .header .subtitle {{
      color: var(--text-secondary);
      font-size: 14px;
    }}
    
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      max-width: 1400px;
      margin: 0 auto;
    }}
    
    .card {{
      background: var(--bg-card);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }}
    
    .card h2 {{
      font-size: 18px;
      margin-bottom: 15px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    
    .status-indicator {{
      width: 12px;
      height: 12px;
      border-radius: 50%;
      display: inline-block;
    }}
    
    .status-green {{ background: var(--accent-green); }}
    .status-orange {{ background: var(--accent-orange); }}
    .status-red {{ background: var(--accent-red); }}
    
    .metric {{
      display: flex;
      justify-content: space-between;
      padding: 10px 0;
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }}
    
    .metric:last-child {{ border-bottom: none; }}
    
    .metric-label {{ color: var(--text-secondary); }}
    .metric-value {{ font-weight: 600; }}
    
    .alert-list {{
      max-height: 200px;
      overflow-y: auto;
    }}
    
    .alert-item {{
      background: rgba(231, 76, 60, 0.2);
      border-left: 3px solid var(--accent-red);
      padding: 10px;
      margin: 8px 0;
      border-radius: 4px;
      font-size: 13px;
    }}
    
    .alert-item.warning {{
      background: rgba(245, 166, 35, 0.2);
      border-left-color: var(--accent-orange);
    }}
    
    .refresh-btn {{
      background: var(--accent-blue);
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
      margin-top: 20px;
    }}
    
    .refresh-btn:hover {{ opacity: 0.9; }}
    
    .timestamp {{
      text-align: center;
      color: var(--text-secondary);
      margin-top: 20px;
      font-size: 12px;
    }}
    
    .progress-bar {{
      background: rgba(255,255,255,0.1);
      border-radius: 4px;
      height: 8px;
      overflow: hidden;
      margin-top: 5px;
    }}
    
    .progress-fill {{
      height: 100%;
      background: linear-gradient(90deg, var(--accent-green), var(--accent-blue));
      transition: width 0.3s;
    }}
  </style>
</head>
<body>
  <div class="header">
    <h1>🛡️ Security Overview</h1>
    <div class="subtitle">PilotSuite Core Security Dashboard v1.0</div>
  </div>
  
  <div class="grid">
    <!-- Circuit Breaker -->
    <div class="card">
      <h2>
        <span class="status-indicator status-{cb_color}"></span>
        Circuit Breaker
      </h2>
      <div class="metric">
        <span class="metric-label">Status</span>
        <span class="metric-value">{cb_state.upper()}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Tripped Services</span>
        <span class="metric-value">{len(cb_tripped)}</span>
      </div>
      {f'<div class="alert-list">' + ''.join(f'<div class="alert-item">{_sanitize(svc)}</div>' for svc in cb_tripped[:5]) + '</div>' if cb_tripped else '<div style="color: var(--accent-green); margin-top: 10px;">✓ All services healthy</div>'}
    </div>
    
    <!-- Authentication -->
    <div class="card">
      <h2>
        <span class="status-indicator status-{auth_color}"></span>
        Authentication
      </h2>
      <div class="metric">
        <span class="metric-label">Token Status</span>
        <span class="metric-value">{'✓ Valid' if auth.get('valid') else '✗ Invalid'}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Token Type</span>
        <span class="metric-value">{_sanitize(auth.get('token_type', 'N/A'))}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Expires In</span>
        <span class="metric-value">{_sanitize(auth.get('expires_in', 'N/A'))}</span>
      </div>
    </div>
    
    <!-- Rate Limiting -->
    <div class="card">
      <h2>📊 Rate Limiting</h2>
      <div class="metric">
        <span class="metric-label">Remaining</span>
        <span class="metric-value">{rate_limit.get('remaining', 'N/A')}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Limit</span>
        <span class="metric-value">{rate_limit.get('limit', 'N/A')}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Reset</span>
        <span class="metric-value">{_sanitize(rate_limit.get('reset', 'N/A'))}</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" style="width: {min(100, int(rate_limit.get('remaining', 100) / max(1, rate_limit.get('limit', 100)) * 100))}%"></div>
      </div>
    </div>
    
    <!-- Performance -->
    <div class="card">
      <h2>⚡ Performance</h2>
      <div class="metric">
        <span class="metric-label">API Latency</span>
        <span class="metric-value">{perf.get('avg_latency_ms', 'N/A')} ms</span>
      </div>
      <div class="metric">
        <span class="metric-label">Requests/min</span>
        <span class="metric-value">{perf.get('requests_per_min', 'N/A')}</span>
      </div>
      <div class="metric">
        <span class="metric-label">Error Rate</span>
        <span class="metric-value">{perf.get('error_rate', 'N/A')}%</span>
      </div>
    </div>
    
    <!-- Anomaly Alerts -->
    <div class="card">
      <h2>
        <span class="status-indicator status-{anomaly_color}"></span>
        Anomaly Alerts
      </h2>
      <div class="metric">
        <span class="metric-label">Active Alerts</span>
        <span class="metric-value">{anomaly_count}</span>
      </div>
      {f'<div class="alert-list">' + ''.join(f'<div class="alert-item{" warning" if a.get("severity") == "warning" else ""}">{_sanitize(a.get("type", "Unknown"))}: {_sanitize(a.get("description", "")[:100])}</div>' for a in anomalies[:5]) + '</div>' if anomalies else '<div style="color: var(--accent-green); margin-top: 10px;">✓ No active alerts</div>'}
    </div>
    
    <!-- System Health -->
    <div class="card">
      <h2>🖥️ System Health</h2>
      <div class="metric">
        <span class="metric-label">Uptime</span>
        <span class="metric-value">{_sanitize(system.get('uptime', 'N/A'))}</span>
      </div>
      <div class="metric">
        <span class="metric-label">CPU Usage</span>
        <span class="metric-value">{system.get('cpu_percent', 'N/A')}%</span>
      </div>
      <div class="metric">
        <span class="metric-label">Memory</span>
        <span class="metric-value">{system.get('memory_percent', 'N/A')}%</span>
      </div>
      <div class="metric">
        <span class="metric-label">Version</span>
        <span class="metric-value">{_sanitize(system.get('version', 'N/A'))}</span>
      </div>
    </div>
  </div>
  
  <div style="text-align: center;">
    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
  </div>
  
  <div class="timestamp">
    Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  </div>
  
  <script>
    // Auto-refresh every 60 seconds
    setTimeout(() => location.reload(), 60000);
  </script>
</body>
</html>"""


async def async_publish_security_overview_panel(
    hass: HomeAssistant,
    core_url: str,
    api_token: str,
) -> Path | None:
    """Fetch security status and publish an interactive HTML panel.
    
    Args:
        hass: Home Assistant instance
        core_url: PilotSuite Core API URL
        api_token: API authentication token
    
    Returns:
        Path to generated panel HTML, or None on failure
    """
    try:
        config = CoreClientConfig(core_url=core_url, api_token=api_token)
        client = PilotSuiteCoreClient(config)
        
        # Fetch all security-related data
        security_status = await client.get("/api/v1/security/status")
        rate_limit = await client.get("/api/v1/rate_limit/status")
        auth_status = await client.get("/api/v1/auth/status")
        perf_status = await client.get("/api/v1/performance/status")
        anomaly = await client.get("/api/v1/anomaly/status")
        system = await client.get("/api/v1/system/status")
        
        # Combine into unified status
        combined_status = {
            "circuit_breaker": security_status.get("circuit_breaker", {}),
            "rate_limit": rate_limit,
            "auth": auth_status,
            "performance": perf_status,
            "anomaly": anomaly,
            "system": system,
        }
        
        await client.close()
        
    except Exception as exc:
        # Fallback with error info
        combined_status = {
            "circuit_breaker": {"tripped": [], "state": "unknown"},
            "rate_limit": {"remaining": 0, "limit": 0},
            "auth": {"valid": False, "error": str(exc)},
            "performance": {},
            "anomaly": {"alerts": []},
            "system": {},
        }
    
    html_content = _generate_security_panel_html(combined_status)
    
    panel_path = Path("/config/www/copilot_ha/security_overview_panel.html")
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    
    await hass.async_add_executor_job(panel_path.write_text, html_content, "utf-8")
    
    url_local = "/local/copilot_ha/security_overview_panel.html"
    
    await persistent_notification.async_create(
        hass,
        title="🛡️ Security Overview Panel Ready",
        message=f"Security dashboard is available:\n\n[Open Security Overview]({url_local})\n\nShows circuit breaker, rate limiting, auth, performance, and anomaly status.",
        notification_id="copilot_ha_security_overview_panel",
    )
    
    return panel_path
