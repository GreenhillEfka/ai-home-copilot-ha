# CHANGELOG_DEV (WIP)

Kurzliste von Änderungen im Branch `dev`, die noch nicht als Add-on Release getaggt sind.

- Stable Releases: `CHANGELOG.md` (Tags `copilot_core-vX.Y.Z`).

## Unreleased (dev)

### Event Ingest Endpoint (2026-02-10)
- **`POST /api/v1/events`**: Receives batched event envelopes from HA Events Forwarder. Validates schema, deduplicates (TTL-based), normalizes both current forwarder format and N3-spec envelope format.
- **`GET /api/v1/events`**: Query stored events with filters (domain, entity_id, zone_id, kind, since, limit).
- **`GET /api/v1/events/stats`**: Store diagnostics (buffer size, accepted/rejected/deduped totals).
- **`EventStore`** (`copilot_core/ingest/event_store.py`): Thread-safe bounded ring buffer + JSONL persistence. Privacy-first: validates source allowlist, truncates context IDs to 12 chars.
- **19 unit tests** (validation, ingest, dedup, query, normalization) all passing ✓.
- This completes the HA→Core data pipeline: Forwarder (HA) → Ingest (Core) → Store (ring buffer + JSONL).

### Candidate: v0.4.0-rc.1 (Tag System v0.1 Beta)
**Status:** Release-ready for approval (all tests passing, code-complete, awaiting explicit go-ahead).

#### Added
- **Tag System Module (`copilot_core/tagging/`):** Complete privacy-first tag registry scaffolding.
  - `tag_registry.py`: YAML-based canonical tag definitions with i18n support + alias validation.
  - `assignments.py`: Persisted tag-assignment store (JSON-backed) with CRUD operations, subject-kind validation, and filtered list/upsert.
  - Default tags: `aicp.kind.light`, `aicp.role.safety_critical`, `aicp.state.needs_repair`, `sys.debug.no_export`.
  - Configurable store path via `COPILOT_TAG_ASSIGNMENTS_PATH` env var.

- **Tag System API (`/api/v1/tag-system`):** Production-ready HTTP endpoints.
  - `GET /api/v1/tag-system/tags`: Canonical registry (language-aware, translation opt-in via query).
  - `GET /api/v1/tag-system/assignments`: Filtered assignments (by subject/tag/materialized status + limit).
  - `POST /api/v1/tag-system/assignments`: Upsert assignment with validation + tag-registry checks.

- **Shared Auth Helper (`copilot_core/api/security.py`):** Reusable JWT token validation.

#### Tests
- `test_tag_registry.py`: Registry loader + serializer + reserved-namespace validation.
- `test_tag_assignment_store.py`: Persisted store CRUD, validation, filtering, pruning.
- Both Core test suites **passing** ✓.
- HA integration test scaffolding ready (`test_tag_utils.py`, `test_tag_sync_integration.py`).

#### Security
- No raw HA attributes stored; only whitelisted scalars in assignment metadata.
- Subject kinds restricted to: `entity`, `device`, `area`, `automation`, `scene`, `script`, `helper`.
- Learned/candidate tags are `pending` by default (no materialization without explicit confirmation).

#### Breaking Changes
- None (new module).

#### Notes
- Integration tests for HA label materialization require full HA test runner (pytest + HA framework).
- Release recommended when HA integration is fully tested in CI.

### In Arbeit
- Forwarder Event Schema (Worker N3 report): minimal stable envelope, attribute projections, redaction policy, implementation checklist.
