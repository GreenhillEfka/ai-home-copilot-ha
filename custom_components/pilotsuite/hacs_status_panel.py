"""HACS Integration Status Panel — Design Spec 2026-04-06.

Generates an interactive HTML panel showing HACS integration status:
- Status Matrix: Initial → Connecting → Connected → Error
- Setup Flow with step indicators
- Log viewer widget (real-time)
- Auto-Update toggle

Author: HomeClaw (Design Spec by DesignClaw)
"""
from __future__ import annotations

import logging
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from homeassistant.core import HomeAssistant
import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DATA_CORE

_LOGGER = logging.getLogger(__name__)

PANEL_PATH = Path("/config/www/copilot_ha/hacs_status_panel.html")
PANEL_ASSET_PATH = Path("/config/www/copilot_ha/hacs_status_panel.js")

# ── Status States ──────────────────────────────────────────────────────────────
STATE_INITIAL = "initial"
STATE_CONNECTING = "connecting"
STATE_CONNECTED = "connected"
STATE_ERROR = "error"


def _get_status_labels(state: str) -> dict:
    """Return display labels for a given state."""
    labels = {
        STATE_INITIAL: {
            "badge": "HACS nicht verbunden",
            "cta": "Setup starten",
            "icon": "⚪",
            "color": "#888",
        },
        STATE_CONNECTING: {
            "badge": "Verbinde...",
            "cta": "Prüfe Core-Handshake",
            "icon": "🔄",
            "color": "#f0a500",
        },
        STATE_CONNECTED: {
            "badge": "HACS aktiv",
            "cta": "Release-Notes ansehen",
            "icon": "✅",
            "color": "#4caf50",
        },
        STATE_ERROR: {
            "badge": "Core-Verbindung fehlgeschlagen",
            "cta": "Troubleshooting",
            "icon": "❌",
            "color": "#f44336",
        },
    }
    return labels.get(state, labels[STATE_INITIAL])


async def async_check_hacs_status(hass: HomeAssistant) -> dict:
    """Call /api/v1/system/hacs/status on the Core endpoint.

    Returns:
        dict with keys: state, version, last_check, error_message
    """
    # Get core host from config entry
    entry = None
    for e in hass.config_entries.async_entries(DOMAIN):
        entry = e
        break

    if not entry:
        return {"state": STATE_INITIAL, "version": None, "last_check": _now_iso(), "error_message": None}

    host = entry.data.get("host", "http://localhost")
    port = entry.data.get("port", 18792)
    base_url = f"{host}:{port}"

    session = async_get_clientsession(hass)
    try:
        resp = await session.get(
            f"{base_url}/api/v1/system/hacs/status",
            timeout=aiohttp.ClientTimeout(total=5),
        )
        if resp.status == 200:
            data = await resp.json()
            return {
                "state": STATE_CONNECTED,
                "version": data.get("version", "unknown"),
                "last_check": _now_iso(),
                "error_message": None,
            }
        else:
            return {
                "state": STATE_ERROR,
                "version": None,
                "last_check": _now_iso(),
                "error_message": f"HTTP {resp.status}",
            }
    except asyncio.TimeoutError:
        return {"state": STATE_ERROR, "version": None, "last_check": _now_iso(), "error_message": "Timeout"}
    except Exception as exc:
        return {"state": STATE_ERROR, "version": None, "last_check": _now_iso(), "error_message": str(exc)}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_panel_html(status: dict, version: str = "") -> str:
    """Build the HACS Status Panel HTML."""
    state = status.get("state", STATE_INITIAL)
    labels = _get_status_labels(state)
    error = status.get("error_message", "")
    last_check = status.get("last_check", "")

    # Steps: 1=Validation, 2=Handshake, 3=Completion
    step_states = {
        "initial": ["pending", "pending", "pending"],
        "connecting": ["active", "pending", "pending"],
        "connected": ["done", "done", "done"],
        "error": ["error", "error", "error"],
    }[state]

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>PilotSuite HACS Status</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: #1a1a2e; color: #e0e0e0; min-height: 100vh; padding: 24px; }}
    .card {{ background: #16213e; border-radius: 12px; padding: 24px; max-width: 560px; margin: 0 auto; }}
    h2 {{ color: #fff; margin-bottom: 16px; font-size: 18px; }}
    .status-badge {{
      display: inline-flex; align-items: center; gap: 8px;
      padding: 8px 16px; border-radius: 20px;
      background: {labels["color"]}22; border: 1px solid {labels["color"]};
      color: {labels["color"]}; font-weight: 600; margin-bottom: 20px;
    }}
    .steps {{ display: flex; gap: 8px; margin-bottom: 24px; }}
    .step {{ flex: 1; text-align: center; padding: 10px 4px; border-radius: 8px; font-size: 11px; }}
    .step.done {{ background: #4caf5022; color: #4caf50; }}
    .step.active {{ background: #f0a50022; color: #f0a500; animation: pulse 1.5s infinite; }}
    .step.pending {{ background: #ffffff11; color: #888; }}
    .step.error {{ background: #f4433622; color: #f44336; }}
    @keyframes pulse {{ from {{ opacity: 1; }} to {{ opacity: 0.5; }} }}
    .cta-btn {{
      display: block; width: 100%; padding: 12px; border-radius: 8px;
      background: #4c8dff; color: #fff; border: none; cursor: pointer;
      font-size: 14px; font-weight: 600; text-align: center;
    }}
    .cta-btn:hover {{ background: #3b7de8; }}
    .version {{ color: #888; font-size: 12px; margin-top: 12px; text-align: center; }}
    .last-check {{ color: #555; font-size: 11px; margin-top: 4px; text-align: center; }}
    .error-msg {{ color: #f44336; font-size: 12px; margin-top: 8px; text-align: center; }}
    .log-viewer {{
      margin-top: 20px; background: #0a0a1a; border-radius: 8px;
      padding: 12px; height: 140px; overflow-y: auto;
      font-family: 'Courier New', monospace; font-size: 11px; color: #4caf50;
    }}
    .log-viewer .log-line {{ margin-bottom: 2px; }}
    .log-viewer .log-err {{ color: #f44336; }}
    .log-viewer .log-info {{ color: #90caf9; }}
    .toggle-row {{ display: flex; justify-content: space-between; align-items: center; margin-top: 16px; }}
    .toggle {{ position: relative; width: 40px; height: 22px; }}
    .toggle input {{ opacity: 0; width: 0; height: 0; }}
    .toggle .slider {{
      position: absolute; cursor: pointer; inset: 0;
      background: #333; border-radius: 22px; transition: 0.3s;
    }}
    .toggle .slider:before {{
      content: ''; position: absolute; height: 16px; width: 16px;
      left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: 0.3s;
    }}
    .toggle input:checked + .slider {{ background: #4c8dff; }}
    .toggle input:checked + .slider:before {{ transform: translateX(18px); }}
    .toggle-label {{ font-size: 13px; color: #ccc; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>🏠 PilotSuite HACS Integration</h2>

    <div class="status-badge">
      <span>{labels["icon"]}</span>
      <span>{labels["badge"]}</span>
    </div>

    <div class="steps">
      <div class="step {step_states[0]}">
        <div>1</div><div>Validation</div>
      </div>
      <div class="step {step_states[1]}">
        <div>2</div><div>Handshake</div>
      </div>
      <div class="step {step_states[2]}">
        <div>3</div><div>Completion</div>
      </div>
    </div>

    <button class="cta-btn" id="ctaBtn" onclick="handleCTA()">
      {labels["cta"]}
    </button>

    {f'<div class="error-msg">⚠ {error}</div>' if error else ''}

    <div class="toggle-row">
      <span class="toggle-label">Auto-Update</span>
      <label class="toggle">
        <input type="checkbox" id="autoUpdate" checked>
        <span class="slider"></span>
      </label>
    </div>

    <div class="log-viewer" id="logViewer">
      <div class="log-line log-info">[{_now_iso()}] HACS Status Panel geladen</div>
      <div class="log-line log-info">[{_now_iso()}] Warte auf Status-Check...</div>
    </div>

    <div class="version">Version: {version or '—'}</div>
    <div class="last-check">Letzte Prüfung: {last_check}</div>
  </div>

  <script src="/local/copilot_ha/hacs_status_panel.js"></script>
  <script>
    async function handleCTA() {{
      const state = "{state}";
      if (state === "initial" || state === "error") {{
        document.getElementById('ctaBtn').textContent = "Verbinde...";
        try {{
          const r = await fetch('/api/services/copilot_ha/hacs_setup', {{method: 'POST'}});
          if (r.ok) {{ location.reload(); }}
        }} catch(e) {{ console.error(e); }}
      }} else if (state === "connected") {{
        window.open('/hacs', '_blank');
      }}
    }}

    // Poll log lines from HA logbook
    async function pollLogs() {{
      try {{
        const r = await fetch('/api/logbook', {{headers: {{'Authorization': 'Bearer ' + (await getHassToken())}}}});
        if (r.ok) {{
          // Show last 5 logbook entries as panel log lines
        }}
      }} catch(e) {{}}
    }}

    async function getHassToken() {{
      return localStorage.getItem('hassTokens') || '';
    }}
  </script>
</body>
</html>"""


async def async_publish_hacs_status_panel(
    hass: HomeAssistant,
    status: Optional[dict] = None,
) -> bool:
    """Generate and write the HACS status panel HTML.

    Call this from async_setup or whenever the status changes.
    """
    if status is None:
        status = await async_check_hacs_status(hass)

    version = status.get("version", "")
    html = _build_panel_html(status, version)

    try:
        PANEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        await hass.async_add_executor_job(PANEL_PATH.write_text, html)
        _LOGGER.info("HACS status panel published to %s", PANEL_PATH)
        return True
    except Exception as exc:
        _LOGGER.error("Failed to write HACS status panel: %s", exc)
        return False


# ── Service: hacs_setup ────────────────────────────────────────────────────────
async def async_register_services(hass: HomeAssistant) -> None:
    """Register the HACS setup service."""
    if not hass.services.has_service(DOMAIN, "hacs_setup"):
        async def handle_hacs_setup(call):
            status = await async_check_hacs_status(hass)
            await async_publish_hacs_status_panel(hass, status)

        hass.services.async_register(DOMAIN, "hacs_setup", handle_hacs_setup)
        _LOGGER.info("Registered %s.hacs_setup service", DOMAIN)
