# Decision Matrix — AI Home CoPilot (2026-02-14 21:10)

**Status:** RUN #10 | **Version:** 1.1 | **Urgency:** 🔴 CRITICAL

---

## 🚨 CRITICAL — Test Import Failures (Blocker)

### Problem Statement
Core tests fail at collection with 5 import errors:

```
ERROR tests/test_app_smoke.py
ERROR tests/test_events_idempotency.py  
ERROR tests/test_graph_api.py
ERROR tests/test_graph_feeding_events.py
ERROR tests/test_tag_api.py
```

### Root Causes

| Issue | File | Error | Severity |
|-------|------|-------|----------|
| **R1: Naming Mismatch** | `brain_graph/provider.py:6` | Imports `BrainGraphStore` but `store.py` exports `GraphStore` | 🔴 HIGH |
| **R2: Framework Mismatch** | `tags/api.py:17` | Uses `aiohttp` but Core is Flask-based | 🔴 HIGH |
| **R3: Missing Deps** | Test env | `aiohttp` not in Core deps | 🟡 MEDIUM |

### Decision: Fix Naming + Convert Tag API to Flask

**Option A: Quick Fix (Recommended)**
- Fix `provider.py` import: `BrainGraphStore` → `GraphStore`
- Convert `tags/api.py` to Flask Blueprint
- Effort: ~1-2h
- Risk: Low

**Option B: Dual Framework**
- Add aiohttp as async server alongside Flask
- Effort: ~4-6h
- Risk: Medium (two HTTP stacks, complexity)

**Option C: Remove Tag API from Core**
- Keep tag logic in HA integration only
- Effort: ~30min
- Risk: Medium (feature regression)

**Recommendation:** **Option A** — Quick fix, minimal risk, restores test ability.

---

## P1 — Tag System v0.2 Integration Status

### Current State
- ✅ Tag Registry implemented
- ✅ Tag Service implemented  
- ✅ HA Labels sync implemented
- 🔴 **Tag API broken** (aiohttp in Flask app)

### Required Fix

```python
# tags/api.py - Convert from aiohttp to Flask

# BEFORE (broken):
from aiohttp import web
async def api_create_tag(request: web.Request):
    ...

# AFTER (Flask):
from flask import Blueprint, request, jsonify
tags_bp = Blueprint("tags_v2", __name__, url_prefix="/api/v1/tags2")
@tags_bp.route("/", methods=["POST"])
def create_tag():
    ...
```

### Impact
- Core tests will pass after conversion
- HA Integration Tag System v0.2 remains functional (uses TagRegistry directly)
- REST API for tags becomes available

---

## P2 — Brain Graph Visualization

### Status: Implemented ✅

| Component | Location | Status |
|-----------|----------|--------|
| Graph Service | `brain_graph/service.py` | ✅ Working |
| Graph Store | `brain_graph/store.py` (GraphStore) | ✅ Working |
| Graph Render | `brain_graph/render.py` | ✅ Working |
| Graph API | `brain_graph/api.py` | ✅ Working |
| HA Viz Button | `brain_graph_viz.py` | ✅ Implemented |
| Tests | `test_brain_graph_*.py` | ⚠️ Import error (R1) |

### No decision needed — fix R1 to enable tests.

---

## P3 — Next Milestone Planning

### After P0/P1 Fixes:

| Feature | Effort | Value | Dependencies |
|---------|--------|-------|--------------|
| Multi-user preference learning | Medium | High | Brain Graph stable |
| Interactive Brain Graph Panel | Medium | Medium | Graph Viz working |
| Performance optimization | Low | Medium | Profiling data |

### Recommendation
No immediate action. Wait for user input on priorities.

---

## Summary & Action Items

| Priority | Issue | Action | Owner | ETA |
|----------|-------|--------|-------|-----|
| **P0** | Test import failures | Fix provider.py + tags/api.py | Dev | Immediate |
| P0.1 | `BrainGraphStore` → `GraphStore` | Edit line 6, 10, 24 in provider.py | Dev | 5min |
| P0.2 | aiohttp → Flask | Rewrite tags/api.py | Dev | 30-60min |
| **P1** | Tag API integration | Follows P0.2 | Dev | — |
| **P2** | Graph Viz tests | Follows P0.1 | Dev | — |
| P3 | Future features | Wait for user | — | — |

---

## Code Fix Details

### Fix 1: brain_graph/provider.py

```python
# Line 6: Change import
-from copilot_core.brain_graph.store import BrainGraphStore
+from copilot_core.brain_graph.store import GraphStore

# Line 10: Change type hint
-_STORE: BrainGraphStore | None = None
+_STORE: GraphStore | None = None

# Line 24: Change constructor
-_STORE = BrainGraphStore(json_path=json_path, persist=persist)
+_STORE = GraphStore(json_path=json_path, persist=persist)
```

### Fix 2: tags/api.py (Full Rewrite to Flask)

See separate implementation plan if Option A chosen.

---

*Decision Matrix updated: 2026-02-14 21:10 UTC+1*
*Worker: AI Home CoPilot Decision Matrix*
*Run: #10*