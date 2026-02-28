# 🎯 PILOTSUITE DEV-ITERATION 1 — @groky Review-Bericht

**Datum:** 2026-02-28 18:34 CET  
**Reviewer:** @groky (Claude Code CLI)  
**Review-Dauer:** ~12 Minuten  

---

## 📊 Executive Summary

| Datei | Status | HIGH | MEDIUM | LOW |
|-------|--------|------|--------|-----|
| `forwarder_n3.py` | ⚠️ Bedenken | 5 | 7 | 14 |
| `habitus_zones_store_v2.py` | ⚠️ Bedenken | 2 | 3 | 8 |

**CI/CD Status:**
- ✅ **pilotsuite-styx-ha:** 608 passed, 1 skipped (4.65s)
- ⚠️ **pilotsuite-styx-core:** 2009 passed, **16 failed**, 1 skipped (54.13s)

---

## 🔍 1. forwarder_n3.py Review

**Pfad:** `custom_components/ai_home_copilot/forwarder_n3.py` (791 Zeilen)  
**Tests:** `tests/test_forwarder_n3.py` (10 Test-Methoden)

### 1.1 Performance-Issues (7 findings)

| ID | Severity | Issue | Lines |
|----|----------|-------|-------|
| P1 | MEDIUM | `_debounce_cache` unbounded growth (memory leak) | 86, 528 |
| P2 | LOW | `_seen_events` cleanup uses size threshold, not time-based | 539 |
| P3 | MEDIUM | User presence/action dicts never pruned | 97-99 |
| P4 | MEDIUM | Re-queue without backoff; bypasses circuit breaker on inline flush | 728, 733 |
| P5 | LOW | Full list copy on every flush; use list swap instead | 705 |
| P6 | LOW | `_entity_cache` instantiated but never used (dead code) | 94 |
| P7 | LOW | Zone mapping built once, never refreshed | 551 |

**Key Finding P1:** `_debounce_cache` speichert einen Eintrag für jede Entity, die jemals ein State-Change feuert. Cleanup nur beim Shutdown. Bei tausenden Entities kann dies zu signifikantem Memory-Wachstum führen.

**Empfehlung:** Periodic pruning im `_flush_loop` oder nach Size-Threshold hinzufügen.

### 1.2 Security-Issues (8 findings)

| ID | Severity | Issue | Lines |
|----|----------|-------|-------|
| S1 | **HIGH** | **All attrs leak for unknown domains** (empty-set falsy check) | 430-434 |
| S2 | LOW | `friendly_name` PII risk when keep_friendly_names=True | 124 |
| S3 | MEDIUM | Context ID truncation is not hashing; hashlib imported but unused | 462-463 |
| S4 | LOW | hashlib imported but unused | 11 |
| S5 | MEDIUM | person/device_tracker zone names can reveal identity | 587-596 |
| S6 | LOW | media_title/media_artist reveal personal habits | 38 |
| S7 | LOW | No TLS enforcement for non-localhost core URLs | 680, 710 |
| S8 | LOW | SENSITIVE_KEY_PATTERN incomplete (misses credential, auth, etc.) | 55 |

**🚨 CRITICAL S1:** Wenn eine Domain nicht in `DOMAIN_PROJECTIONS` ist, ist `allowed_attrs` ein leeres Set. Die Bedingung `if allowed_attrs and key not in allowed_attrs` evaluiert zu `False` (weil leeres Set falsy ist). **Alle Attribute werden für unbekannte Domains durchgereicht!**

**Fix:** Logic auf default-deny für unbekannte Domains ändern oder empty-set case explizit behandeln.

### 1.3 Code-Qualität (11 findings)

| ID | Severity | Issue | Lines |
|----|----------|-------|-------|
| Q1 | **HIGH** | `_heartbeat_task` not initialized in `__init__` (AttributeError risk) | 157 |
| Q2 | **HIGH** | `_flush_loop` exits permanently on first non-cancel exception | 638-639 |
| Q3 | **HIGH** | `_heartbeat_loop` exits permanently on first non-cancel exception | 649-650 |
| Q4 | MEDIUM | Listens to ALL entity state changes; wastes CPU on filtered-out domains | 208-209 |
| Q5 | **HIGH** | Race condition: re-queue outside lock can lose/reorder events | 728, 733 |
| Q6 | LOW | Import inside async function body | 616 |
| Q7 | LOW | Module-level mock patch never stopped (test:17) | — |
| Q8 | MEDIUM | Missing coverage for lifecycle, HTTP, concurrency, edge cases | tests |
| Q9 | LOW | core_url exposed in stats (potential credential leak) | 783 |
| Q10 | LOW | Redundant EVENT_STATE_CHANGED check | 220 |
| Q11 | LOW | Unused import: Set from typing | 18 |

**🚨 CRITICAL Q2/Q3:** Ein einzelner unexpected exception in den Loops beendet diese permanent — der Forwarder stoppt ohne Recovery.

**🚨 CRITICAL Q5:** Re-queue außerhalb des `async with self._queue_lock` Blocks kann zu Event-Verlust führen.

---

## 🔍 2. habitus_zones_store_v2.py Review

**Pfad:** `custom_components/ai_home_copilot/habitus_zones_store_v2.py` (1092 Zeilen)

### 2.1 Datenkonsistenz (5 findings)

| ID | Severity | Issue | Lines |
|----|----------|-------|-------|
| D1 | **HIGH** | **Read-modify-write race on storage** (no locking) | 616-642, 846-877 |
| D2 | MEDIUM | Conflict resolver cache never invalidated | 1000-1002, 1035 |
| D3 | MEDIUM | Conflict resolution evicts entire zone for single-entity overlap | 271-278 |
| D4 | LOW | `_conflict_history` unbounded growth | 196, 290 |
| D5 | LOW | Frozen dataclass with mutable dict fields | 84, 103 |

**🚨 CRITICAL D1:** Beide Funktionen (`async_set_zones_v2` und `async_set_zone_state`) folgen einem `load → mutate → save` Pattern ohne Locking. Wenn zwei Coroutines parallel für verschiedene zones im gleichen entry schreiben, überschreibt die zweite Save die erste Änderung.

**Empfehlung:** `asyncio.Lock` pro entry_id oder mindestens pro Store-Instance verwenden.

**D3 Beispiel:** Zone A (50 Entities) und Zone B (50 Entities) teilen 1 Entity. Zone B gewinnt, Zone A wird komplett aus dem active set entfernt.

### 2.2 Error-Handling (6 findings)

| ID | Severity | Issue | Lines |
|----|----------|-------|-------|
| E1 | **HIGH** | `int()` on priority can raise on bad input | 551 |
| E2 | MEDIUM | Dead code: `default_floor` extraction unreachable | 750-755 |
| E3 | LOW | `import time` inside functions instead of top-level | 264, 844, 908 |
| E4 | LOW | `_validate_zone_v2` scans only `entity_ids`, not full entity set | 715-716 |
| E5 | LOW | Exception swallow without logging | 683 |
| E6 | LOW | No error handling for missing DOMAIN key in hass.data | 577-584 |

**🚨 CRITICAL E1:** `priority = int(obj.get("priority", 0))` wirft `ValueError` bei nicht-numerischen Strings (z.B. `"high"`). Dies führt zum kompletten Fail der Zone-List-Load.

**E2 Dead Code:** Nach dem `raise` auf Line 751 ist `raw` garantiert eine List. Der `isinstance(raw, dict)` Check auf Line 754 ist immer `False`. `default_floor` ist immer `None`.

### 2.3 Documentation (4 findings)

| ID | Severity | Issue | Lines |
|----|----------|-------|-------|
| DOC1 | MEDIUM | No `_LOGGER` defined (HA convention) | — |
| DOC2 | LOW | `async_migrate_from_v1` type hint misleading | 1070 |
| DOC3 | LOW | No docstring on `_ROLE_ALIASES` | 390 |
| DOC4 | LOW | Type narrowing lost in `_normalize_zone_v2` | 495 |

---

## 🧪 3. CI/CD Check Ergebnisse

### pilotsuite-styx-ha
```
✅ 608 passed, 1 skipped in 4.65s
```
**Status:** ✅ PASS

### pilotsuite-styx-core
```
❌ 16 failed, 2009 passed, 1 skipped in 54.13s
```
**Status:** ⚠️ FAIL

**Failed Tests:**
- `test_core_endpoints.py::TestErrorBoundaries::test_error_boundary_imports`
- `test_core_endpoints.py::TestErrorBoundaries::test_error_status_imports`
- `test_core_endpoints.py::TestCoreEndpoints::test_health_endpoint`
- `test_core_endpoints.py::TestCoreEndpoints::test_ready_endpoint`
- `test_core_endpoints.py::TestCoreEndpoints::test_version_endpoint`
- `test_llm_provider_fallback.py` (8 tests) — LLM provider fallback tests
- `test_tag_api.py::test_list_tags_endpoint`
- `test_tag_api.py::test_assignments_crud_flow`

**Analyse:** Die 16 Failures betreffen hauptsächlich Core-Endpoints und LLM-Provider-Fallback-Tests. Diese sind wahrscheinlich Konfigurations-bedingt (fehlende Ollama/Cloud-Konfiguration in Test-Umgebung) und nicht direkt mit den reviewed Files verknüpft.

---

## 🎯 4. Release-Empfehlung

### Gesamtbewertung

| Kriterium | Bewertung |
|-----------|-----------|
| forwarder_n3.py Stabilität | ⚠️ **Bedenken** (5 HIGH-Issues) |
| habitus_zones_store_v2.py Stabilität | ⚠️ **Bedenken** (2 HIGH-Issues) |
| CI/CD styx-ha | ✅ PASS |
| CI/CD styx-core | ⚠️ FAIL (16 Tests) |
| Security (PII-Redaktion) | ⚠️ **Kritische Lücke** (S1) |

### 🚨 Release-Empfehlung: **NO-GO** (mit Auflagen)

**Begründung:**

1. **Security-Lücke S1 (forwarder_n3.py):** Die PII-Redaktion ist **unvollständig**. Unbekannte Domains leiten alle Attribute durch. Dies ist ein privacy-kritisches Problem.

2. **Stabilitätsrisiko Q2/Q3 (forwarder_n3.py):** Beide Loops (`_flush_loop`, `_heartbeat_loop`) beenden sich permanent bei der ersten Exception. Der Forwarder würde im Production-Betrieb bei unerwarteten Fehlern stillstehen.

3. **Data-Race D1 (habitus_zones_store_v2.py):** Read-modify-write ohne Locking kann zu Datenverlust führen.

4. **Crash-Risiko E1 (habitus_zones_store_v2.py):** Unguarded `int()` cast kann Zone-Loading komplett crashen.

### ✅ Go-Kriterien (vor Release zu beheben)

**P0 (Blocker):**
- [ ] **S1 fixen:** Default-deny für unbekannte Domains in `_project_attributes`
- [ ] **Q2/Q3 fixen:** Exception-Handling in Loops so ändern, dass nur der innere flush call wrapped ist, nicht die äußere Schleife
- [ ] **E1 fixen:** `priority` parsing mit try/except oder `int_or_default` helper

**P1 (Empfohlen vor Release):**
- [ ] **D1 fixen:** asyncio.Lock für read-modify-write operations
- [ ] **Q5 fixen:** Re-queue innerhalb des queue_lock blocks verschieben
- [ ] **D2 fixen:** Conflict resolver cache invalidation bei Zone-Änderungen

**P2 (Post-Release):**
- [ ] P1: `_debounce_cache` periodic pruning
- [ ] S3: Context ID hashing statt truncation
- [ ] Test-coverage Lücken schließen (Q8)

---

## 📋 5. Zusammenfassung nach Priorität

### HIGH Priority (7 items — Blocker)
| Datei | ID | Issue |
|-------|----|-------|
| forwarder_n3.py | S1 | All attrs leak for unknown domains |
| forwarder_n3.py | Q1 | `_heartbeat_task` not initialized in `__init__` |
| forwarder_n3.py | Q2 | `_flush_loop` exits permanently on exception |
| forwarder_n3.py | Q3 | `_heartbeat_loop` exits permanently on exception |
| forwarder_n3.py | Q5 | Race condition in re-queue |
| habitus_zones_store_v2.py | D1 | Read-modify-write race on storage |
| habitus_zones_store_v2.py | E1 | `int()` on priority can raise |

### MEDIUM Priority (10 items)
| Datei | ID | Issue |
|-------|----|-------|
| forwarder_n3.py | P1 | `_debounce_cache` unbounded growth |
| forwarder_n3.py | P3 | User presence/action dicts never pruned |
| forwarder_n3.py | P4 | Re-queue without backoff |
| forwarder_n3.py | S3 | Context ID truncation not hashing |
| forwarder_n3.py | S5 | person/device_tracker zone names reveal identity |
| forwarder_n3.py | Q4 | Listens to ALL entity state changes |
| forwarder_n3.py | Q8 | Missing test coverage |
| habitus_zones_store_v2.py | D2 | Conflict resolver cache never invalidated |
| habitus_zones_store_v2.py | D3 | Conflict resolution evicts entire zone |
| habitus_zones_store_v2.py | E2 | Dead code: default_floor extraction |

---

**Erstellt von:** @groky  
**Review-Tool:** Claude Code CLI  
**Nächster Schritt:** P0-Issues beheben, dann Re-Review
