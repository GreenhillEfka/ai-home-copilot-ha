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


EXPORT_DIR = "/config/copilot_ha/exports"
PUBLISH_DIR = "/config/www/copilot_ha"


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
        "schema": "copilot_ha_config_snapshot",
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

    fname = f"copilot_ha_snapshot_{_now_stamp()}.json"
    path = os.path.join(EXPORT_DIR, fname)
    await hass.async_add_executor_job(_write_json, path, snapshot)

    await async_set_last_generated(hass, path)

    persistent_notification.async_create(
        hass,
        f"Generated config snapshot:\n{path}",
        title="PilotSuite config snapshot",
        notification_id="copilot_ha_config_snapshot",
    )

    return path


async def async_publish_last_config_snapshot(hass: HomeAssistant) -> str:
    state = await async_get_state(hass)
    src = state.last_generated_path
    if not src:
        raise ValueError("No snapshot generated yet. Click 'generate config snapshot' first.")

    os.makedirs(PUBLISH_DIR, exist_ok=True)
    base = os.path.basename(src)
    dst = os.path.join(PUBLISH_DIR, base)
    await hass.async_add_executor_job(shutil.copyfile, src, dst)

    await async_set_last_published(hass, dst)

    url = f"/local/copilot_ha/{base}"
    persistent_notification.async_create(
        hass,
        f"Published snapshot for download:\n{url}",
        title="PilotSuite config snapshot",
        notification_id="copilot_ha_config_snapshot",
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
    """Apply snapshot to HA storage/options (no silent actions beyond config storage).

    Delta-write pattern:
    - Habitus zones: merge-only write via async_set_zones_v2_from_raw(..., unmatched_fallback=True)
      Unmatched entities from snapshot route to zone:ungeordnet.
    - Options: compute delta against current entry.options, write only changed keys.
      Secrets (redacted in snapshot) are preserved from current entry.options.
    - entry.data is setup-time config; only explicitly snapshot-diff keys are written.

    Args:
        hass: HomeAssistant instance.
        entry: ConfigEntry being updated.
        snapshot: Snapshot dict from export (schema: copilot_ha_config_snapshot v1).
    """

    zones = snapshot.get("habitus_zones")
    if zones is None:
        zones = []

    if not isinstance(zones, list):
        raise ValueError("Snapshot habitus_zones must be a list")

    # ── Zones: always use unmatched_fallback routing ─────────────────────
    # async_set_zones_v2_from_raw handles deduplication internally;
    # unmatched entities (not mapped to any named zone) are routed to zone:ungeordnet.
    await async_set_zones_v2_from_raw(hass, entry.entry_id, zones, unmatched_fallback=True)

    # ── Options: delta-write against current entry.options ───────────────
    snap_opts = snapshot.get("options")
    current_opts: dict[str, Any] = dict(entry.options) if entry.options else {}

    if isinstance(snap_opts, dict):
        # Strip <redacted> sentinel values, replacing with current secret values.
        clean_opts = _strip_redacted(dict(snap_opts), keep_existing=current_opts)

        # Compute delta: only write keys that actually differ from current state.
        delta_opts: dict[str, Any] = {}
        for k, v in clean_opts.items():
            import copy
            if copy.deepcopy(current_opts.get(k)) != copy.deepcopy(v):
                delta_opts[k] = v

        # Persist only if there is a real delta.
        if delta_opts:
            hass.config_entries.async_update_entry(entry, options=delta_opts)

    # ── entry.data: setup-time config — minimal touch ───────────────────
    # Only write deltas if snapshot carries explicit data keys that differ from current.
    snap_data = snapshot.get("data")
    current_data: dict[str, Any] = dict(entry.data) if entry.data else {}

    if isinstance(snap_data, dict):
        delta_data: dict[str, Any] = {}
        for k, v in snap_data.items():
            import copy
            if copy.deepcopy(current_data.get(k)) != copy.deepcopy(v):
                delta_data[k] = v

        if delta_data:
            # Merge: new values win, existing keys not in delta are preserved.
            merged_data = {**current_data, **delta_data}
            hass.config_entries.async_update_entry(entry, data=merged_data)

    await hass.config_entries.async_reload(entry.entry_id)
