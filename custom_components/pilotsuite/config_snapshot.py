from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
# DEPRECATED: v1 - prefer v2
# from .habitus_zones_store import async_get_zones, async_set_zones_from_raw
from .habitus_zones_store_v2 import async_get_zones_v2, async_set_zones_v2_from_raw
from .config_snapshot_store import (
    async_get_state,
    async_set_last_generated,
    async_set_last_published,
)


EXPORT_DIR = "/config/pilotsuite-styx/exports"
PUBLISH_DIR = "/config/www/pilotsuite-styx"
LEGACY_EXPORT_DIR = "/config/copilot_ha/exports"
LEGACY_PUBLISH_DIR = "/config/www/copilot_ha"


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _redact_options(opts: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(opts)
    # Never export secrets by default.
    for key in ("token", "auth_token"):
        if key in redacted and redacted.get(key):
            redacted[key] = "<redacted>"
    return redacted


async def async_generate_config_snapshot(hass: HomeAssistant, entry: ConfigEntry) -> str:
    """Generate a local JSON snapshot of the integration configuration.

    Governance/privacy-first: secrets are redacted; file is written locally under /config.
    """

    os.makedirs(EXPORT_DIR, exist_ok=True)

    zones = await async_get_zones_v2(hass, entry.entry_id)
    zones_raw = [{"id": z.zone_id, "name": z.name, "entity_ids": list(z.entity_ids)} for z in zones]

    # Options contain host/port/media lists/forwarder settings; entry.data contains original setup.
    options = dict(entry.options)
    data = dict(entry.data)

    snapshot: dict[str, Any] = {
        "schema": "pilotsuite_config_snapshot",
        "version": 1,
        "generated": datetime.now(timezone.utc).isoformat(),
        "entry": {
            "title": entry.title,
            "entry_id": entry.entry_id,
        },
        "data": _redact_options(data),
        "options": _redact_options(options),
        "habitus_zones": zones_raw,
        "notes": {
            "secrets": "Tokens are redacted by default. Re-enter them manually after import if needed.",
        },
    }

    def _write_json(path: str, obj: dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2)

    fname = f"pilotsuite_snapshot_{_now_stamp()}.json"
    path = os.path.join(EXPORT_DIR, fname)
    legacy_path = os.path.join(LEGACY_EXPORT_DIR, fname)
    await hass.async_add_executor_job(lambda: os.makedirs(EXPORT_DIR, exist_ok=True))
    await hass.async_add_executor_job(lambda: os.makedirs(LEGACY_EXPORT_DIR, exist_ok=True))
    await hass.async_add_executor_job(_write_json, path, snapshot)
    await hass.async_add_executor_job(shutil.copyfile, path, legacy_path)

    await async_set_last_generated(hass, path)

    persistent_notification.async_create(
        hass,
        f"Generated config snapshot:\n{path}",
        title="PilotSuite config snapshot",
        notification_id="pilotsuite_config_snapshot",
    )

    return path


async def async_publish_last_config_snapshot(hass: HomeAssistant) -> str:
    state = await async_get_state(hass)
    src = state.last_generated_path
    if not src:
        raise ValueError("No snapshot generated yet. Click 'generate config snapshot' first.")

    os.makedirs(PUBLISH_DIR, exist_ok=True)
    os.makedirs(LEGACY_PUBLISH_DIR, exist_ok=True)
    base = os.path.basename(src)
    dst = os.path.join(PUBLISH_DIR, base)
    legacy_dst = os.path.join(LEGACY_PUBLISH_DIR, base)
    await hass.async_add_executor_job(shutil.copyfile, src, dst)
    await hass.async_add_executor_job(shutil.copyfile, src, legacy_dst)

    await async_set_last_published(hass, dst)

    url = f"/local/pilotsuite-styx/{base}"
    persistent_notification.async_create(
        hass,
        f"Published snapshot for download:\n{url}",
        title="PilotSuite config snapshot",
        notification_id="pilotsuite_config_snapshot",
    )
    return url


def _strip_redacted(opts: dict[str, Any], *, keep_existing: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for k, v in opts.items():
        if v == "<redacted>":
            # keep existing secret
            if k in keep_existing:
                cleaned[k] = keep_existing[k]
            continue
        cleaned[k] = v
    return cleaned


async def async_apply_config_snapshot(
    hass: HomeAssistant,
    entry: ConfigEntry,
    snapshot: dict[str, Any],
) -> None:
    """Apply snapshot to HA storage/options using delta-write pattern.

    - Habitus zones are written to our store.
    - Options are updated (secrets remain unchanged if redacted).
    - Only writes deltas, not full overwrites.
    - Finally reload config entry.
    """

    zones = snapshot.get("habitus_zones")
    if zones is None:
        zones = []

    if not isinstance(zones, list):
        raise ValueError("Snapshot habitus_zones must be a list")

    await async_set_zones_v2_from_raw(hass, entry.entry_id, zones)

    snap_opts = snapshot.get("options")
    if isinstance(snap_opts, dict):
        # Preserve current secrets when snapshot has redacted values.
        merged = _strip_redacted(dict(snap_opts), keep_existing=dict(entry.options))
        
        # Only update if there are actual changes (delta-write)
        if merged != dict(entry.options):
            hass.config_entries.async_update_entry(entry, options=merged)

    # entry.data is treated as setup-time config; we generally do not overwrite it.
    # But if there are changes, only write the delta
    snap_data = snapshot.get("data")
    if isinstance(snap_data, dict):
        # Preserve current secrets when snapshot has redacted values.
        merged_data = _strip_redacted(dict(snap_data), keep_existing=dict(entry.data))
        
        # Only update if there are actual changes (delta-write)
        if merged_data != dict(entry.data):
            hass.config_entries.async_update_entry(entry, data=merged_data)

    await hass.config_entries.async_reload(entry.entry_id)
