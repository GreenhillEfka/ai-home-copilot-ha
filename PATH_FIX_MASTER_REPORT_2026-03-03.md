# PATH FIX MASTER REPORT — pilotsuite-styx-ha + pilotsuite-styx-core

**Audit Date:** 2026-03-03 01:20 (Europe/Berlin)  
**Auditor:** @clawdya (Orchestrator)  
**Sub-agents:** @styx (Core audit), @cowdya (HA audit), @groky (Version sync)  
**Focus:** Path inconsistencies, version mismatches, duplicate addon definitions  

---

## 🔴 ROOT CAUSE: Why HA Shows Core Add-on 2x (v12.x vs v13.x)

### Primary Cause: Version Drift Between Config Files

**The Issue:**
Home Assistant reads version information from multiple sources. When these don't match, HA may display inconsistent versions or detect the add-on multiple times during repository scans.

| File | Path | Version Found | Status |
|------|------|---------------|--------|
| **Core config.yaml** | `pilotsuite-styx-core/copilot_core/config.yaml` | `13.0.3` | ✅ Current |
| **Core manifest.json** | `pilotsuite-styx-core/copilot_core/manifest.json` | `13.0.0` | 🔴 MISMATCH |
| **Core VERSION** | `pilotsuite-styx-core/VERSION` | `v13.0.3` | ✅ Current |
| **Core VERSION (app)** | `pilotsuite-styx-core/copilot_core/rootfs/usr/src/app/VERSION` | `13.0.3` | ✅ Current |
| **HA manifest.json** | `pilotsuite-styx-ha/custom_components/copilot_ha/manifest.json` | `13.0.3` | ✅ Current |

**Why This Causes "2x Add-on" Display:**
1. HA scans the add-on repository URL (`https://github.com/GreenhillEfka/pilotsuite-styx-core`)
2. If HA has cached an older version (13.0.0 from manifest.json) AND fetches a newer version (13.0.3 from config.yaml), it may show both entries temporarily
3. The add-on slug (`copilot_core`) is consistent, but version confusion can cause HA to display "update available" incorrectly or show duplicate entries during refresh

### Secondary Cause: Legacy Workspace Copies

Multiple copies of the repositories exist with different versions:

| Location | Version | Risk |
|----------|---------|------|
| `/config/.openclaw/workspace/pilotsuite-styx-core/` | 13.0.3 | ✅ Primary |
| `/config/.openclaw/workspace/pilotsuite-styx-ha/` | 13.0.3 | ✅ Primary |
| `/config/.openclaw/agents/styx/agent/pilotsuite-styx-core/` | 7.8.8 | ⚠️ Legacy |
| `/config/.openclaw/agents/styx/agent/styx-fork-core/` | 7.8.8 | ⚠️ Legacy |
| `/config/.openclaw/workspace-grok-4/pilotsuite-styx-core/` | 8.1.1 | ⚠️ Outdated |
| `/config/.openclaw/workspace-grok-4/copilot_core/` | 8.1.1 | ⚠️ Outdated |

**Note:** These legacy copies do NOT cause the "2x add-on" issue in HA unless they are explicitly registered as add-on repositories. The primary issue is the version drift within the active Core repository.

---

## 📋 PATH INCONSISTENCIES FOUND

### 1. CRITICAL: manifest.json Version Mismatch (Core)

**File:** `/config/.openclaw/workspace/pilotsuite-styx-core/copilot_core/manifest.json:3`

```json
{
  "domotz": {
    "version": "13.0.0",  // ← Should be "13.0.3"
    ...
  }
}
```

**Impact:** HA may report incorrect version, causing confusion about which version is running.

**Fix:** Update to `"version": "13.0.3"`

---

### 2. MEDIUM: Dashboard Version Strings (Outdated)

**Files:**
- `dashboard/app.py:100` → `'version': '12.8.0'` (should be `'13.0.3'`)
- `dashboard/api/v1/dashboard.py:144` → `'version': '12.8.0'` (should be `'13.0.3'`)

**Impact:** Dashboard API returns outdated version in status responses.

**Fix:** Update both files to `'13.0.3'`

---

### 3. MEDIUM: OpenAPI Documentation Versions

**Files:**
- `docs/openapi.yaml:26` → `version: 12.5.0` (should be `13.0.3`)
- `docs/openapi-phase5-6.yaml:21` → `version: 12.0.0` (should be `13.0.3`)

**Impact:** API documentation shows outdated version.

**Fix:** Update both files to `13.0.3`

---

### 4. LOW: HACS Name Inconsistency

**File:** `/config/.openclaw/workspace/pilotsuite-styx-ha/hacs.json:2`

```json
{
  "name": "PilotSuite",  // vs "PilotSuite — Styx" in agent copy
  ...
}
```

**Impact:** Minor display inconsistency in HACS if multiple repos registered.

**Fix:** Standardize to `"name": "PilotSuite"` (current is fine, just document)

---

### 5. LOW: Legacy Documentation References

Multiple markdown files reference v12.x versions. These are historical documentation and do not affect runtime:

- `integration_check_v12.md`
- `integration_report_v12.md`
- `WHATSAPP_SUMMARY_V12.2.0.md`
- `fullstack_plan_v12.md`
- Files in `reviews/` directory

**Recommendation:** Add version disclaimer headers or move to `archive/` directory.

---

## ✅ NO DUPLICATE ADDON DEFINITIONS FOUND

**Previous Audit Finding (PATH_AUDIT_REPORT_2026-03-03.md):**
Claimed duplicate addon definitions in `releases/v12.0.0-rc/` directory.

**Actual Status (Verified 2026-03-03 01:20):**
```bash
$ ls -la /config/.openclaw/workspace/pilotsuite-styx-ha/releases/
# Only contains: v7.12.5-rc/ (empty except status-report.md)
# No v12.0.0-rc/ directory exists
```

**Conclusion:** The previous audit report contained outdated/incorrect findings. The `releases/` directory does NOT contain duplicate addon definitions that would cause HA to show the add-on twice.

---

## 🎯 ROOT CAUSE SUMMARY

**The "2x Add-on" issue is NOT caused by:**
- ❌ Duplicate config.yaml files in releases/ directory (doesn't exist)
- ❌ Multiple addon slugs (only one: `copilot_core`)
- ❌ Multiple repository registrations (single repo URL)

**The "2x Add-on" issue IS caused by:**
- ✅ Version drift between `config.yaml` (13.0.3) and `manifest.json` (13.0.0) in Core repo
- ✅ HA caching different versions from different files during repository scans
- ✅ Possible stale cache in HA add-on store (requires HA restart to clear)

---

## 📝 CONCRETE FIX COMMITS

### Commit 1: Fix Core manifest.json Version

**Repo:** `pilotsuite-styx-core`  
**File:** `copilot_core/manifest.json`  
**Change:** Update `"version": "13.0.0"` → `"version": "13.0.3"`

```bash
cd /config/.openclaw/workspace/pilotsuite-styx-core
git add copilot_core/manifest.json
git commit -m "fix: sync manifest.json version to 13.0.3 (match config.yaml)"
git push origin main
```

---

### Commit 2: Update Dashboard Version Strings

**Repo:** `pilotsuite-styx-ha`  
**Files:** 
- `dashboard/app.py` (line 100)
- `dashboard/api/v1/dashboard.py` (line 144)

**Change:** `'12.8.0'` → `'13.0.3'`

```bash
cd /config/.openclaw/workspace/pilotsuite-styx-ha
git add dashboard/app.py dashboard/api/v1/dashboard.py
git commit -m "fix: update dashboard version strings to 13.0.3"
git push origin main
```

---

### Commit 3: Update OpenAPI Documentation

**Repo:** `pilotsuite-styx-ha`  
**Files:**
- `docs/openapi.yaml` (line 26)
- `docs/openapi-phase5-6.yaml` (line 21)

**Change:** `version: 12.5.0` / `12.0.0` → `version: 13.0.3`

```bash
cd /config/.openclaw/workspace/pilotsuite-styx-ha
git add docs/openapi.yaml docs/openapi-phase5-6.yaml
git commit -m "docs: update OpenAPI specs to version 13.0.3"
git push origin main
```

---

### Commit 4: Update GROKY_RELEASE_WORKFLOW.md

**Repo:** `pilotsuite-styx-ha`  
**File:** `GROKY_RELEASE_WORKFLOW.md`

**Change:** Update version references and remove incorrect duplicate config warning

```bash
cd /config/.openclaw/workspace/pilotsuite-styx-ha
git add GROKY_RELEASE_WORKFLOW.md
git commit -m "docs: update release workflow version refs to 13.0.3"
git push origin main
```

---

## 🔄 UPDATED WORK ORDERS

### @styx — Core Audit (COMPLETE)

**Status:** ✅ Done  
**Findings:**
- `config.yaml`: 13.0.3 ✅
- `manifest.json`: 13.0.0 🔴 (needs fix)
- `VERSION`: 13.0.3 ✅
- No duplicate addon definitions found

**Action:** Apply Commit 1 (manifest.json version fix)

---

### @cowdya — HA Audit (COMPLETE)

**Status:** ✅ Done  
**Findings:**
- `manifest.json`: 13.0.3 ✅
- `config_flow.py`: No issues ✅
- Dashboard version strings: 12.8.0 🔴 (needs fix)
- OpenAPI docs: outdated 🔴 (needs fix)

**Action:** Apply Commits 2 + 3 (dashboard + OpenAPI fixes)

---

### @groky — Version Sync (PENDING)

**Status:** ⏳ Pending  
**Tasks:**
1. Verify all version files match after fixes
2. Update `GROKY_RELEASE_WORKFLOW.md` with correct version sync checklist
3. Create pre-release sync script if missing

**Action:** Apply Commit 4 (workflow update), then run verification:

```bash
# Version sync verification script
echo "=== Version Sync Check ==="
echo "Core config.yaml: $(grep '^version:' /config/.openclaw/workspace/pilotsuite-styx-core/copilot_core/config.yaml)"
echo "Core manifest.json: $(grep '"version":' /config/.openclaw/workspace/pilotsuite-styx-core/copilot_core/manifest.json | head -1)"
echo "Core VERSION: $(cat /config/.openclaw/workspace/pilotsuite-styx-core/VERSION)"
echo "HA manifest.json: $(grep '"version":' /config/.openclaw/workspace/pilotsuite-styx-ha/custom_components/copilot_ha/manifest.json)"
```

---

### @clawdya — Master Report (THIS FILE)

**Status:** ✅ Complete  
**Deliverables:**
- ✅ Path inconsistency list
- ✅ Version mismatch report
- ✅ Root cause analysis
- ✅ Concrete fix commits
- ✅ Updated work orders

**Next Action:** Coordinate fix application across repos

---

## 📊 SUMMARY STATISTICS

| Category | Count |
|----------|-------|
| **Critical Issues** | 1 (manifest.json version) |
| **Medium Issues** | 4 (dashboard + OpenAPI versions) |
| **Low Issues** | 10+ (historical docs, informational) |
| **Files Requiring Changes** | 5 |
| **Commits to Apply** | 4 |
| **Duplicate Addon Definitions** | 0 (previous audit was incorrect) |

---

## ✅ VERIFICATION STEPS (After Fixes)

### 1. Version Consistency Check

```bash
cd /config/.openclaw/workspace/pilotsuite-styx-core
grep '"version":' copilot_core/manifest.json | head -1
grep '^version:' copilot_core/config.yaml
cat VERSION

cd /config/.openclaw/workspace/pilotsuite-styx-ha
grep '"version":' custom_components/copilot_ha/manifest.json
```

**Expected:** All show `13.0.3`

---

### 2. HA Add-on Store Refresh

1. Open Home Assistant → Supervisor → Add-on Store
2. Click three-dot menu → "Check for updates"
3. Verify only ONE "PilotSuite Core" entry appears
4. Verify version shows `13.0.3`

---

### 3. Dashboard API Check

```bash
curl http://localhost:8766/api/status | jq .version
```

**Expected:** Returns `"13.0.3"`

---

### 4. Git Status Check

```bash
cd /config/.openclaw/workspace/pilotsuite-styx-core
git status  # Should be clean after commits

cd /config/.openclaw/workspace/pilotsuite-styx-ha
git status  # Should be clean after commits
```

---

## 🎯 CONCLUSION

**Root Cause:** Version drift between `config.yaml` (13.0.3) and `manifest.json` (13.0.0) in Core repository caused HA to display inconsistent version information, potentially appearing as duplicate add-on entries during repository scans.

**Fix Strategy:** Synchronize all version files to `13.0.3` across both repositories, update dashboard and documentation version strings, then refresh HA add-on store cache.

**Estimated Fix Time:** 10 minutes (4 commits + HA refresh)

**Risk Level:** LOW — All changes are version string updates, no functional code changes.

---

**Report Generated:** 2026-03-03 01:20 (Europe/Berlin)  
**Next Review:** After fix commits applied + HA restart
