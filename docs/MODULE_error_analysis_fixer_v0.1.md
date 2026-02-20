# Error Analysis + Fixer Module (v0.1)

## Intent
A Home Assistant module that:
1) reads local logs,
2) detects known failure patterns,
3) turns them into **governed, actionable fixes** (Repairs),
4) can apply fixes via **buttons / fix flows**, and
5) supports **rollback** for any state-changing action.

**Privacy-first:** No log shipping. No cloud/LLM requirement. Everything runs locally.

**Governance-first:** Nothing is applied automatically. Every fix is explicit and reversible where possible.

## Scope v0.1 (what we’ll likely need soon)
### Inputs (log sources)
- `/config/home-assistant.log` (+ optional `.log.1`)
- Optional later: Supervisor/Add-on logs (requires Supervisor API access; keep out of v0.1)

### Outputs
- A “Run log analysis” button.
- Findings presented as:
  - Repairs issues (`is_fixable=true`) with clear explanation
  - Optional sensors showing counts only (avoid >16KB attribute warnings)

### Fix execution
A Fix is a small reversible operation, executed only after confirmation:
- Disable/enable an automation (rollback = re-enable)
- Disable/enable a config entry (rollback = re-enable)
- Rename a broken custom integration folder (rollback = rename back)
- Trigger HACS update/downgrade via `update.install` (rollback = install previous tag)

### Rollback model
- Every applied fix writes a transaction record to `.storage/ai_home_copilot_fixes.json`:
  - timestamp
  - fix_id
  - parameters
  - inverse action parameters
- Provide a “Rollback last fix” button (and later: pick from history).

## Findings (pattern library)
Start with high-signal patterns we already saw in your logs:
- `Error parsing manifest.json file at /config/custom_components/<x>/manifest.json`
  - Suggested fix: disable that custom integration (rename folder)
- `Setup failed for custom integration '<x>': Unable to import component: ...`
  - Suggested fix: downgrade/upgrade that integration (HACS) OR disable
- `Detected blocking call to import_module ... custom integration '<x>'`
  - Suggested fix: warn + propose update; no auto fix
- `State attributes for sensor.<x> exceed maximum size 16384 bytes`
  - Suggested fix: warn + propose entity exclusion from recorder (manual) OR advise integration settings
- Repeated auth failures (`could not authenticate`)
  - Suggested fix: guided steps; no auto action

## UX in HA
- Button: `button.ai_home_copilot_analyze_logs`
- Button: `button.ai_home_copilot_rollback_last_fix`
- Repairs issue per finding:
  - “Apply fix” / “Ignore” / “Defer”
  - After “Apply”, show what was changed and how to rollback

## Safety rules
- Any file operation must be:
  - within `/config/` only
  - implemented as rename (not delete)
  - executor-job (no blocking in event loop)
- Never touch secrets/tokens.
- Never rewrite HA `.storage` except via HA APIs or our own `.storage` namespace.
- Default allowlist for automated actions (v0.1): only `automation.*`, `config_entry disable/enable`, and `/config/custom_components/<x>` renames.

## v0.2 ideas
- Supervisor diagnostics: add-on crash loops, port conflicts
- Per-integration fix packs (Zigbee/Z-Wave/Unifi/Energy)
- Optional “explain” summaries (still local), and later optional LLM rephrasing (explicit opt-in)
