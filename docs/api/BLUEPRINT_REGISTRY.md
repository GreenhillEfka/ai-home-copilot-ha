# Blueprint Registration Consistency Guide

**Version:** 1.0  
**Last Updated:** 2026-03-01  
**Status:** ✅ Verified

---

## Overview

This document ensures consistent URL prefix patterns across all PilotSuite API blueprints. Proper blueprint registration prevents duplicate prefixes (e.g., `/api/v1/api/v1/...`) and maintains a clean API structure.

---

## URL Prefix Pattern

### Correct Pattern

```
/app
  └── /api/v1 (parent blueprint)
        ├── /neurons (relative)
        ├── /graph (relative)
        ├── /habitus (relative)
        └── /rag (relative)
```

**Full URL:** `/api/v1/rag/search`

---

## Blueprint Registration Rules

### Rule 1: Sub-Blueprints Use Relative Prefixes

Blueprints registered under `api_v1` must use **relative** prefixes (no `/api/v1`):

✅ **Correct:**
```python
bp = Blueprint("rag", __name__, url_prefix="/rag")
api_v1.register_blueprint(rag_bp)
# Result: /api/v1/rag/...
```

❌ **Incorrect:**
```python
bp = Blueprint("rag", __name__, url_prefix="/api/v1/rag")
api_v1.register_blueprint(rag_bp)
# Result: /api/v1/api/v1/rag/... (DUPLICATE!)
```

---

### Rule 2: Standalone Blueprints Use Absolute Prefixes

Some blueprints are registered directly on the app (not nested under `api_v1`):

✅ **Correct:**
```python
bp = Blueprint("tags", __name__, url_prefix="/api/v1/tag-system")
app.register_blueprint(tags_bp)
# Result: /api/v1/tag-system/...
```

---

## Registry: All Blueprints

### Registered Under `/api/v1` (Relative Prefixes)

| Blueprint | File | Prefix | Full Path | Status |
|-----------|------|--------|-----------|--------|
| `candidates` | `candidates.py` | `/candidates` | `/api/v1/candidates` | ✅ |
| `events` | `events.py` | `/events` | `/api/v1/events` | ✅ |
| `mood` | `mood.py` | `/mood` | `/api/v1/mood` | ✅ |
| `graph` | `graph.py` | `/graph` | `/api/v1/graph` | ✅ |
| `habitus` | `habitus.py` | `/habitus` | `/api/v1/habitus` | ✅ |
| `dashboard_cards` | `habitus_dashboard_cards.py` | `/habitus/dashboard_cards` | `/api/v1/habitus/dashboard_cards` | ✅ |
| `graph_ops` | `graph_ops.py` | `/graph` | `/api/v1/graph` | ✅ |
| `vector` | `vector.py` | `/vector` | `/api/v1/vector` | ✅ |
| `neurons` | `neurons.py` | `/neurons` | `/api/v1/neurons` | ✅ |
| `weather` | `weather.py` | `/weather` | `/api/v1/weather` | ✅ |
| `voice_context` | `voice_context_bp.py` | `/voice` | `/api/v1/voice` | ✅ |
| `swagger_ui` | `swagger_ui.py` | `/docs` | `/api/v1/docs` | ✅ |
| `user_preferences` | `user_preferences.py` | `/user` | `/api/v1/user` | ✅ |
| `dashboard` | `dashboard.py` | `/dashboard` | `/api/v1/dashboard` | ✅ |
| `knowledge_graph` | `knowledge_graph/api.py` | `/kg` | `/api/v1/kg` | ✅ |
| `search` | `search.py` | `/search` | `/api/v1/search` | ✅ |
| `notifications` | `notifications.py` | `/notifications` | `/api/v1/notifications` | ✅ |
| `user_hints` | `user_hints.py` | `/hints` | `/api/v1/hints` | ✅ |
| `conversation` | `conversation.py` | `/chat` | `/api/v1/chat` | ✅ |
| `sharing` | `sharing/api.py` | `/sharing` | `/api/v1/sharing` | ✅ |
| `federated` | `collective_intelligence/api.py` | `/collective` | `/api/v1/collective` | ✅ |
| `rag` | `rag.py` | `/rag` | `/api/v1/rag` | ✅ |
| `dev` | `dev.py` | `/dev` | `/api/v1/dev` | ✅ |

---

### Standalone Blueprints (Absolute Prefixes)

These are registered directly on the app in `core_setup.py`:

| Blueprint | File | Prefix | Full Path | Status |
|-----------|------|--------|-----------|--------|
| `energy` | `energy.py` | `/api/v1/energy` | `/api/v1/energy` | ✅ |
| `system_health` | `system_health.py` | `/api/v1/system-health` | `/api/v1/system-health` | ✅ |
| `tags` | `tag_system.py` | `/api/v1/tag-system` | `/api/v1/tag-system` | ✅ |
| `brain_graph` | `brain_graph/api.py` | `/api/v1/brain-graph` | `/api/v1/brain-graph` | ✅ |
| `dev_surface` | `dev_surface.py` | `/api/v1/dev-surface` | `/api/v1/dev-surface` | ✅ |
| `calendar` | `calendar.py` | `/api/v1/calendar` | `/api/v1/calendar` | ✅ |
| `entity_assignment` | `entity_assignment.py` | `/api/v1/entity-assignment` | `/api/v1/entity-assignment` | ✅ |
| `explain` | `explain.py` | `/api/v1/explain` | `/api/v1/explain` | ✅ |
| `haushalt` | `haushalt.py` | `/api/v1/haushalt` | `/api/v1/haushalt` | ✅ |
| `homekit` | `homekit.py` | `/api/v1/homekit` | `/api/v1/homekit` | ✅ |
| `log_fixer_tx` | `log_fixer_tx.py` | `/api/v1/log_fixer_tx` | `/api/v1/log_fixer_tx` | ✅ |
| `onyx_bridge` | `onyx_bridge.py` | `/api/v1/onyx` | `/api/v1/onyx` | ✅ |
| `presence` | `presence.py` | `/api/v1/presence` | `/api/v1/presence` | ✅ |
| `reminders` | `reminders.py` | `/api/v1` | `/api/v1` | ✅ |
| `scenes` | `scenes.py` | `/api/v1/scenes` | `/api/v1/scenes` | ✅ |
| `shopping` | `shopping.py` | `/api/v1` | `/api/v1` | ✅ |

---

### OpenAI-Compatible Endpoints

These use the `/v1` prefix for OpenAI SDK compatibility:

| Blueprint | File | Prefix | Full Path | Status |
|-----------|------|--------|-----------|--------|
| `openai_compat` | `conversation.py` | `/v1` | `/v1` | ✅ |
| `conversation` | `conversation.py` | `/chat` | `/api/v1/chat` | ✅ |

**OpenAI Endpoints:**
- `/v1/chat/completions`
- `/v1/models`
- `/v1/completions`

---

## Verification Checklist

### For New Blueprints

When adding a new API blueprint:

- [ ] **Determine registration type:**
  - Will it be nested under `/api/v1`? → Use **relative** prefix
  - Will it be standalone? → Use **absolute** prefix (`/api/v1/...`)

- [ ] **Check prefix pattern:**
  - Relative: `url_prefix="/my-feature"`
  - Standalone: `url_prefix="/api/v1/my-feature"`

- [ ] **Register in correct location:**
  - Nested: Add to `blueprint.py` → `api_v1.register_blueprint()`
  - Standalone: Add to `core_setup.py` → `app.register_blueprint()`

- [ ] **Update documentation:**
  - Add to this registry
  - Update `API_REFERENCE.md`
  - Add endpoint examples

- [ ] **Test endpoints:**
  - Verify no duplicate prefixes
  - Test with authentication
  - Check Swagger UI (`/api/v1/docs`)

---

## Common Mistakes

### Mistake 1: Double Prefix

❌ **Wrong:**
```python
# In blueprint.py (nested under api_v1)
bp = Blueprint("myapi", __name__, url_prefix="/api/v1/myapi")
```

✅ **Correct:**
```python
# In blueprint.py (nested under api_v1)
bp = Blueprint("myapi", __name__, url_prefix="/myapi")
```

---

### Mistake 2: Wrong Registration Location

❌ **Wrong:**
```python
# Standalone blueprint with absolute prefix registered under api_v1
api_v1.register_blueprint(energy_bp)  # energy_bp has url_prefix="/api/v1/energy"
```

✅ **Correct:**
```python
# Standalone blueprint registered directly on app
app.register_blueprint(energy_bp)  # energy_bp has url_prefix="/api/v1/energy"
```

---

### Mistake 3: Inconsistent Naming

❌ **Inconsistent:**
```python
url_prefix="/my-feature"      # kebab-case
url_prefix="/my_feature"      # snake_case
url_prefix="/myFeature"       # camelCase
```

✅ **Consistent:**
```python
url_prefix="/my-feature"      # kebab-case (preferred)
url_prefix="/tag-system"
url_prefix="/user-preferences"
```

---

## Testing Blueprint Registration

### Manual Test

```bash
# Test nested blueprint
curl http://localhost:8909/api/v1/rag/stats \
  -H "X-Auth-Token: your-token"

# Test standalone blueprint
curl http://localhost:8909/api/v1/tag-system/tags \
  -H "X-Auth-Token: your-token"

# Test OpenAI-compatible endpoint
curl http://localhost:8909/v1/models \
  -H "Authorization: Bearer your-token"
```

### Automated Test

```python
def test_blueprint_prefixes():
    """Verify all blueprints have correct URL prefixes."""
    expected_nested = [
        "/api/v1/rag",
        "/api/v1/neurons",
        "/api/v1/graph",
        # ... add all nested blueprints
    ]
    
    expected_standalone = [
        "/api/v1/tag-system",
        "/api/v1/energy",
        # ... add all standalone blueprints
    ]
    
    for prefix in expected_nested + expected_standalone:
        response = client.get(f"{prefix}/health")  # or appropriate endpoint
        assert response.status_code in [200, 401]  # 401 is OK (auth required)
```

---

## Migration Guide

### Migrating Standalone → Nested

If moving a blueprint from standalone to nested:

1. **Update prefix:**
   ```python
   # Before
   bp = Blueprint("tags", __name__, url_prefix="/api/v1/tag-system")
   
   # After
   bp = Blueprint("tag_system", __name__, url_prefix="/tag-system")
   ```

2. **Update registration:**
   ```python
   # Before: core_setup.py
   app.register_blueprint(tags_bp)
   
   # After: blueprint.py
   api_v1.register_blueprint(tags_bp)
   ```

3. **Update all references:**
   - API documentation
   - Client code
   - Tests
   - Swagger UI

---

## Related Documentation

- [API Reference](./API_REFERENCE.md)
- [RAG Hybrid Search API](./RAG_HYBRID_SEARCH.md)
- [HA Notify Adapter](./HA_NOTIFY_ADAPTER.md)
- [Architecture](../ARCHITECTURE.md)

---

**Maintained by:** @cowdya  
**Last Audit:** 2026-03-01  
**Next Audit:** 2026-03-15 (bi-weekly)
