# Safety-Point Backup + Confirm Flow Spec (Update/Rollback UX)

## Overview
This spec defines a privacy-first safety point backup mechanism and a confirm flow for updates/rollbacks in the `ai-home-copilot-ha` repository. The goal is to capture a minimal, encrypted snapshot of critical system state before any update or rollback operation, present it to the user for explicit confirmation, and provide a reliable rollback path if the update fails.

## Goals
- **Safety:** Ensure the user can recover to a known good state after any update.
- **Privacy:** Keep all backup data local (no external cloud storage or external API calls).
- **Transparency:** Show a concise summary of what will be backed up and what will be affected.
- **Simplicity:** Keep the UX lightweight with clear actions (Yes / No) and fallback options.

## Safety-Point Backup

### What is backed up?
- **Home Assistant configuration** (`configuration.yaml`, `secrets.yaml`, custom component files).
- **OpenClaw knowledge files** (`memory/*.md`, `agenda.md`, `sessions/.*`).
- **Current service state** (critical services like MQTT, Zigbee2MQTT, Sonos, etc.) – captured via a snapshot of relevant entity states (no historical data).
- **Shell environment state** (selected environment variables, installed Python packages for HA).
- **Agent logs** (last 50 lines of main agent log, useful for debugging).

### How it is captured
- A dedicated script `scripts/safety_point_backup.py` will be added.
- The script runs under a **sandboxed Python environment** (isolated from the main agent) to avoid polluting the workspace.
- Backup files are stored in `/config/.openclaw/workspace/backup/safety_point/` with filenames containing the timestamp and a SHA256 hash of the backup data for integrity.
- Data is **encrypted locally** using libsodium (e.g., via `pynacl`):
  - Encryption key is derived from the user’s passphrase stored in `secrets.yaml` under `backup_encryption_passphrase`.
  - Encrypted files have a `.enc` suffix (e.g., `state_2026-02-11_13-10-54.enc`).
- The script also creates a **manifest** (`manifest.json`) listing:
  - list of files backed up
  - original sizes
  - SHA256 hash of each file
  - encryption key identifier

### Performance & Frequency
- Backup is **non-blocking**: executed in the background (`exec` tool with `background=True`).
- Takes ~10-15 seconds on typical home server; can be run via a cron job or as part of the update flow.

## Confirm Flow

### User Interaction
- After the backup completes, the main agent sends a **Telegram** message with a summary:
  ```markdown
  **Safety Point Backup Completed**
  - Date: 2026-02-11 13:10:54 CET
  - Files backed up: 12 (total ~2.3 MB)
  - Backup stored locally at: /config/.openclaw/workspace/backup/safety_point/state_2026-02-11_13-10-54.enc
  - Encryption: libsodium (passphrase stored in secrets.yaml)
  ```
- Two inline buttons are attached:
  - **✅ Continue** – proceeds with the update/rollback.
  - **❌ Cancel** – aborts the operation, discards backup, and leaves the system unchanged.

### Confirm Dialog Implementation
- Use OpenClaw’s `message` tool to send the message with interactive buttons.
- The dialog respects **privacy-first**: the backup path is never revealed to external services; only the Telegram user sees it.
- If the user presses **❌ Cancel**, the backup files are deleted (`shutil.rmtree`) and the operation terminates cleanly.

## Rollback Mechanism

### Trigger
- Automatic detection of failure during update (e.g., exit code != 0 from `exec`).
- Manual trigger via a special command `/rollback safety_point <backup_id>` (where `<backup_id>` is the timestamp part of the backup file).

### Process
1. Verify backup exists (`manifest.json` + encrypted payload).
2. Decrypt the payload using the same passphrase.
3. Replace relevant files (`configuration.yaml`, `memory/*.md`, etc.) with the restored versions.
4. Restart affected services (`home-assistant`, `openclaw`).
5. Send a confirmation message to the user.

### Safety Checks
- **Integrity check:** Verify SHA256 hash of each restored file matches the manifest.
- **Conflict resolution:** If a file has changed locally since backup, prompt the user (via a **modal confirmation** with options: overwrite, merge, abort). For simplicity, default to **abort** unless the user explicitly chooses overwrite.

## Implementation Plan (PR Slice)

| File | Change | Reason |
|------|-------|--------|
| `scripts/safety_point_backup.py` | New script – captures and encrypts critical state | Centralize backup logic, reusable for manual backups as well. |
| `scripts/safety_point_rollback.py` | New script – decrypts and restores state | Enables rollback via CLI and webhook. |
| `ai_home_copilot/__main__.py` (or equivalent agent entry) | Add `backup = True` flag to update flow; invoke backup script before `exec` | Guarantees backup runs before any destructive change. |
| `secrets.yaml` | Add `backup_encryption_passphrase` field | Store encryption key securely. |
| `README.md` (or `docs/upgrade.md`) | Add a section **"Safety-Point Backup + Confirm Flow"** with usage instructions | Documentation for maintainers and users. |
| `tests/unit/test_safety_point_backup.py` | Unit tests for backup/encryption/decryption | Ensure reliability and avoid regression. |
| `tests/integration/test_update_flow.py` | Add test cases for confirm flow and rollback handling | Verify full UX path works. |
| `config/tasks.yaml` | Optional: add a cron entry `0 4 * * * python scripts/safety_point_backup.py` (daily auto‑backup) | Provide long‑term safety without extra UX. |

### Minimal PR Size
- All new scripts and config changes are encapsulated in a single PR. Approx. **200–300 lines of code** across 5–6 files.
- No external dependencies added; only `pynacl` (already listed in `requirements.txt` if not, add it with a minimal version).
- No releases or tags are required; the change is scoped to the `ai-home-copilot-ha` repo only.

## Privacy‑First Design Details
- **No external communication:** The backup and rollback scripts never call any cloud API; they only read/write local files.
- **Data minimisation:** Only essential files are backed up; no logs, no system binaries.
- **Encryption at rest:** All backup files are encrypted before persisting.
- **Passphrase storage:** The passphrase is stored only in the user’s `secrets.yaml` (already encrypted on disk). No plaintext passphrase is ever printed or logged.
- **User consent:** The confirm flow requires explicit user action (`Continue` or `Cancel`). No auto‑apply.

## UI / Telegram Interaction Mockup

```markdown
--- safety point backup completed ---

🗂️ Backup location: /config/.openclaw/workspace/backup/safety_point/state_2026-02-11_13-10-54.enc
🔒 Encryption: libsodium (passphrase from secrets.yaml)
📅 Date: 2026-02-11 13:10:54 CET
📂 Files: 12 (~2.3 MB)

[✅ Continue]  [❌ Cancel]
```

- Buttons are implemented via `message` tool (`action: send`, `interaction: inlineKeyboard`).
- If user selects `❌ Cancel`, the agent automatically removes the backup directory (`exec rm -rf …`) and replies with a friendly message.

## Risks & Mitigations
- **Encryption key loss:** If the user loses the passphrase, the backup becomes unrecoverable. Mitigate by documenting the need to store the passphrase securely and optionally offering a **separate encrypted backup** (outside scope).
- **Partial backup on failure:** Backup script writes temporary files atomically; if it crashes, nothing is left behind. Implemented via temp directories (`tempfile.TemporaryDirectory`). | 

## Timeline
- **Day 1:** Draft scripts, add encryption, and test locally.
- **Day 2:** Implement Telegram confirm flow, add unit tests.
- **Day 3:** Add rollback script, test end‑to‑end flow.
- **Day 4:** Update documentation and README.
- **Day 5:** Run integration tests on a staging VM; merge PR.

## Next Steps
- Review PR for security compliance.
- After merge, enable the backup flag for future `openclaw update` commands.
- Provide a small user guide (`README` note) on how to manually trigger safety‑point backup.

---

*Generated by OpenClaw (Sun 2026‑02‑11) – privacy‑first spec.*