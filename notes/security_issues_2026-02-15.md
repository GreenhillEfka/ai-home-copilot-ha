# Security Issues - Core Add-on (2026-02-15)

## 🔴 CRITICAL: Missing Authentication on log_fixer_tx API

**File:** `addons/copilot_core/rootfs/usr/src/app/api/v1/log_fixer_tx.py`

**Issue:** All endpoints lack `@require_api_key` decorator

**Impact:** Anyone can create/rollback transactions, potentially modify system files

**Fix:**
```python
@require_api_key
def status():
    ...

@require_api_key
def transactions():
    ...

@require_api_key
def recover():
    ...

@require_api_key
def create_transaction():
    ...
```

**Priority:** P0

---

## 🔴 CRITICAL: Arbitrary File Operations in Transactions

**File:** `log_fixer_tx.py:219-248`

**Issue:** `create_transaction` accepts `rename` operations with arbitrary paths

**Impact:** Could be exploited for privilege escalation or data exfiltration

**Fix:**
```python
ALLOWED_PATHS = [
    "/config/homeassistant",
    "/config/.openclaw/workspace",
    "/config/www"
]

def validate_path(path: str) -> bool:
    return any(path.startswith(allowed) for allowed in ALLOWED_PATHS)
```

**Priority:** P0

---

## 🟠 HIGH: Error Information Leakage

**File:** `brain_graph/api.py:105-115`

**Issue:** Returns full exception messages: `{"error": f"Internal error: {str(e)}"}`

**Impact:** Could leak internal paths, database info, stack traces

**Fix:**
```python
except Exception as e:
    logger.error(f"Error: {e}")
    return {"error": "Internal server error"}, 500
```

**Priority:** P1

---

## 🟡 MEDIUM: Idempotency Cache Not Thread-Safe

**File:** `graph_ops.py:34-56`

**Issue:** Global `_IDEM_CACHE` dict without locking

**Impact:** Race conditions in concurrent requests

**Fix:**
```python
import threading
_IDEM_CACHE = {}
_IDEM_LOCK = threading.Lock()

def idempotent(key: str, ttl: int = 3600):
    with _IDEM_LOCK:
        if key in _IDEM_CACHE:
            return False
        _IDEM_CACHE[key] = time.time()
        return True
```

**Priority:** P2

---

## Next Steps

1. Add `@require_api_key` to all log_fixer_tx endpoints
2. Implement path allowlist validation
3. Generic error messages for API responses
4. Add threading.Lock() to idempotency cache