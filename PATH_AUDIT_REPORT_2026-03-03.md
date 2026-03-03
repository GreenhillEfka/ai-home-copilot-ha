# PATH AUDIT REPORT — pilotsuite-styx-ha

**Audit Date:** 2026-03-03  
**Auditor:** @cowdya (subagent)  
**Scope:** manifest.json, config_flow.py, HACS configuration, *.md files  
**Focus:** Path inconsistencies, version mismatches, duplicate addon definitions, Core integration issues  

---

## 🔴 CRITICAL FINDINGS

### 1. VERSION MISMATCH — HA Integration vs Core Add-on

**Issue:** Version drift between HA integration and Core add-on

| Component | File Path | Current Version | Expected |
|-----------|-----------|-----------------|----------|
| **HA Integration** | `custom_components/copilot_ha/manifest.json` | `13.0.3` | Should match Core |
| **Core Add-on** | `pilotsuite-styx-core/copilot_core/manifest.json` | `13.0.0` | — |
| **Core Add-on** | `pilotsuite-styx-core/copilot_core/config.yaml` | `13.0.3` | — |

**Line Numbers:**
- `/config/.openclaw/workspace/pilotsuite-styx-ha/custom_components/copilot_ha/manifest.json:16` → `"version": "13.0.3"`
- `/config/.openclaw/workspace/pilotsuite-styx-core/copilot_core/manifest.json:3` → `"version": "13.0.0"`
- `/config/.openclaw/workspace/pilotsuite-styx-core/copilot_core/config.yaml:2` → `version: "13.0.3"`

**Impact:** HA may show inconsistent version information, causing confusion about which version is actually running.

**Fix Required:** Synchronize versions across all files.

---

### 2. DUPLICATE ADDON DEFINITIONS — v12.0.0-rc Directory

**Issue:** Legacy release candidate directory contains duplicate addon configuration files

**Files:**
- `/config/.openclaw/workspace/pilotsuite-styx-ha/releases/v12.0.0-rc/config.yaml` (version: "12.0.0")
- `/config/.openclaw/workspace/pilotsuite-styx-ha/releases/v12.0.0-rc/manifest.json` (version: "12.0.0")

**Problem:** These files define the same addon slug (`copilot_core`) as the current Core repository, potentially causing:
- HA to detect the addon twice (v12.x from releases/ directory, v13.x from Core repo)
- Version confusion in HA UI
- Add-on store conflicts

**Recommendation:** 
- **Option A:** Delete `/config/.openclaw/workspace/pilotsuite-styx-ha/releases/v12.0.0-rc/` directory (if only historical)
- **Option B:** Rename slug in legacy files to `copilot_core_legacy` (if must be preserved)
- **Option C:** Move to archive location outside active workspace

---

### 3. OUTDATED VERSION REFERENCES IN DOCUMENTATION

**Issue:** Multiple documentation files reference old v12.x versions while current is v13.x

#### Dashboard Files (CRITICAL — Runtime Impact)

| File | Line | Current | Should Be |
|------|------|---------|-----------|
| `dashboard/app.py` | 100 | `'version': '12.8.0'` | `'version': '13.0.3'` |
| `dashboard/api/v1/dashboard.py` | 144 | `'version': '12.8.0'` | `'version': '13.0.3'` |

#### OpenAPI Documentation Files

| File | Line | Current | Should Be |
|------|------|---------|-----------|
| `docs/openapi.yaml` | 26 | `version: 12.5.0` | `version: 13.0.3` |
| `docs/openapi-phase5-6.yaml` | 21 | `version: 12.0.0` | `version: 13.0.3` |

#### Markdown Documentation (Informational)

These files reference v12.x but are historical documentation (no code impact):
- `integration_check_v12.md` — References v12.0.0
- `integration_report_v12.md` — References v12.0.0
- `WHATSAPP_SUMMARY_V12.2.0.md` — References v12.2.0
- `fullstack_plan_v12.md` — References v12.0.0/v12.1.0
- Multiple files in `reviews/` directory reference v12.x releases
- `CHANGELOG.md` — Contains v12.x entries (expected, historical)

---

### 4. HACS CONFIGURATION INCONSISTENCY

**Issue:** HACS repository configuration differs between workspace copies

| Location | File | Name Field |
|----------|------|------------|
| `/config/.openclaw/workspace/pilotsuite-styx-ha/` | `hacs.json` | `"name": "PilotSuite"` |
| `/config/.openclaw/agents/styx/agent/pilotsuite-styx-ha/` | `hacs.json` | `"name": "PilotSuite — Styx"` |

**Impact:** Minor — HACS display name inconsistency if multiple repos are registered.

**Fix:** Standardize to `"name": "PilotSuite"` across all copies.

---

### 5. LEGACY DOMAIN NAME IN AGENT COPY

**Issue:** Agent workspace copy uses old domain name

**File:** `/config/.openclaw/agents/styx/agent/pilotsuite-styx-ha/custom_components/ai_home_copilot/manifest.json:2`
- `"domain": "ai_home_copilot"` (should be `copilot_ha`)
- `"version": "7.8.9"` (severely outdated)

**Impact:** This appears to be a legacy/development copy. If actively used, it would create a conflicting integration.

**Recommendation:** Verify if this directory is still in use. If not, archive or delete.

---

## 🟡 MEDIUM PRIORITY FINDINGS

### 6. VERSION REFERENCE IN RELEASE DEPLOYMENT GUIDE

**File:** `docs/RELEASE_DEPLOYMENT_GUIDE.md:173`
```
jq '.version' /path/to/pilotsuite-styx-core/addons/copilot_core/config.json
```

**Issue:** Path reference uses `addons/` directory structure which doesn't match current layout (`copilot_core/`).

**Fix:** Update to:
```
jq '.version' /path/to/pilotsuite-styx-core/copilot_core/config.yaml
```

---

### 7. MULTIPLE WORKSPACE COPIES

**Issue:** Multiple copies of the repository exist with potentially different versions:

1. `/config/.openclaw/workspace/pilotsuite-styx-ha/` — Primary workspace (v13.0.3)
2. `/config/.openclaw/workspace-grok-4/pilotsuite-styx-ha/` — Grok workspace (unknown version)
3. `/config/.openclaw/agents/styx/agent/pilotsuite-styx-ha/` — Agent copy (v7.8.9 legacy)
4. `/config/.openclaw/workspace-grok-4/pilotsuite-dev/pilotsuite-styx-ha/` — Dev copy (unknown)

**Risk:** Version drift, confusion about which is authoritative.

**Recommendation:** Designate one as primary, archive or sync others.

---

## ✅ CORRECT CONFIGURATIONS

### config_flow.py — NO ISSUES FOUND

**File:** `/config/.openclaw/workspace/pilotsuite-styx-ha/custom_components/copilot_ha/config_flow.py`

- ✅ Correctly imports from `const.py`
- ✅ Uses `DOMAIN` constant (not hardcoded)
- ✅ Version is read from `manifest.json` at runtime
- ✅ No path inconsistencies detected
- ✅ Proper integration with Core endpoint discovery

### const.py — NO ISSUES FOUND

**File:** `/config/.openclaw/workspace/pilotsuite-styx-ha/custom_components/copilot_ha/const.py`

- ✅ `DOMAIN = "copilot_ha"` (correct)
- ✅ `DEFAULT_PORT = 8909` (matches Core)
- ✅ No hardcoded version strings
- ✅ Proper namespace isolation

---

## 🎯 ROOT CAUSE ANALYSIS: Why HA Shows Core Add-on 2x (v12.x vs v13.x)

### Primary Cause: Legacy Release Directory

The `/config/.openclaw/workspace/pilotsuite-styx-ha/releases/v12.0.0-rc/` directory contains:
- `config.yaml` with `slug: copilot_core` and `version: "12.0.0"`
- `manifest.json` with `"slug": "copilot_core"` and `"version": "12.0.0"`

If this directory is:
1. **Mounted** as an addon source in HA
2. **Symlinked** to the HA addons directory
3. **Referenced** in a local addon repository configuration

Then HA will detect the addon twice:
- Once from the active Core repository (v13.0.x)
- Once from the releases/v12.0.0-rc/ directory (v12.0.0)

### Secondary Cause: Version Drift

Version inconsistencies across files may cause HA to report different versions depending on which file it reads:
- HA integration manifest: 13.0.3
- Core manifest: 13.0.0
- Core config.yaml: 13.0.3

---

## 📋 RECOMMENDED FIXES (Priority Order)

### P0 — CRITICAL (Do Immediately)

1. **Remove or Archive Legacy RC Directory**
   ```bash
   # Option A: Delete (if only historical)
   rm -rf /config/.openclaw/workspace/pilotsuite-styx-ha/releases/v12.0.0-rc/
   
   # Option B: Archive (if must preserve)
   mv /config/.openclaw/workspace/pilotsuite-styx-ha/releases/v12.0.0-rc/ \
      /config/.openclaw/workspace/pilotsuite-styx-ha/archive/v12.0.0-rc/
   ```

2. **Synchronize Versions**
   - Update `pilotsuite-styx-core/copilot_core/manifest.json` to `13.0.3`
   - OR update all files to match `13.0.0` (if that's the intended release version)

3. **Update Dashboard Version Strings**
   - `dashboard/app.py:100` → Change `'12.8.0'` to `'13.0.3'`
   - `dashboard/api/v1/dashboard.py:144` → Change `'12.8.0'` to `'13.0.3'`

4. **Update OpenAPI Documentation**
   - `docs/openapi.yaml:26` → Change `12.5.0` to `13.0.3`
   - `docs/openapi-phase5-6.yaml:21` → Change `12.0.0` to `13.0.3`

### P1 — HIGH (Do Within 24 Hours)

5. **Standardize HACS Configuration**
   - Update all `hacs.json` files to use consistent `"name": "PilotSuite"`

6. **Archive or Delete Legacy Agent Copy**
   - Verify `/config/.openclaw/agents/styx/agent/pilotsuite-styx-ha/` usage
   - If unused, archive or delete to prevent conflicts

7. **Update Release Deployment Guide**
   - Fix path reference in `docs/RELEASE_DEPLOYMENT_GUIDE.md:173`

### P2 — MEDIUM (Do Within 1 Week)

8. **Consolidate Workspace Copies**
   - Designate primary workspace
   - Sync or archive other copies
   - Document authoritative location

9. **Update Historical Documentation**
   - Add version disclaimers to v12.x documentation files
   - Or move to `archive/` directory

---

## 📊 SUMMARY STATISTICS

| Category | Count |
|----------|-------|
| **Critical Issues** | 4 |
| **Medium Issues** | 3 |
| **Files Requiring Changes** | 9 |
| **Version Mismatches** | 7 |
| **Duplicate Addon Definitions** | 2 (in v12.0.0-rc/) |
| **Outdated Documentation** | 10+ (mostly historical) |

---

## 🔍 FILES AUDITED

### Core Configuration Files
- ✅ `custom_components/copilot_ha/manifest.json`
- ✅ `custom_components/copilot_ha/config_flow.py`
- ✅ `custom_components/copilot_ha/const.py`
- ✅ `hacs.json`
- ✅ `pilotsuite-styx-core/copilot_core/manifest.json`
- ✅ `pilotsuite-styx-core/copilot_core/config.yaml`

### Release Configuration Files
- ⚠️ `releases/v12.0.0-rc/manifest.json` (DUPLICATE)
- ⚠️ `releases/v12.0.0-rc/config.yaml` (DUPLICATE)

### Documentation Files
- ⚠️ `dashboard/app.py` (outdated version)
- ⚠️ `dashboard/api/v1/dashboard.py` (outdated version)
- ⚠️ `docs/openapi.yaml` (outdated version)
- ⚠️ `docs/openapi-phase5-6.yaml` (outdated version)
- ⚠️ `docs/RELEASE_DEPLOYMENT_GUIDE.md` (outdated path)
- ℹ️ `CHANGELOG.md` (historical, expected)
- ℹ️ `README.md` (current)
- ℹ️ 60+ markdown files in `reviews/`, `docs/`, `iterations/` (historical)

### Legacy/Agent Copies
- ⚠️ `/config/.openclaw/agents/styx/agent/pilotsuite-styx-ha/custom_components/ai_home_copilot/manifest.json` (outdated domain + version)
- ℹ️ `/config/.openclaw/workspace-grok-4/pilotsuite-styx-ha/` (status unknown)

---

## ✅ VERIFICATION STEPS (After Fixes)

1. **Check for duplicate slugs:**
   ```bash
   grep -r "slug: copilot_core" /config/.openclaw/workspace/pilotsuite-styx-ha/ --include="*.yaml" --include="*.json"
   ```
   Expected: Only 1 result (in Core repo, not in releases/)

2. **Verify version consistency:**
   ```bash
   grep -r '"version":' /config/.openclaw/workspace/pilotsuite-styx-ha/custom_components/copilot_ha/manifest.json
   grep -r '"version":' /config/.openclaw/workspace/pilotsuite-styx-core/copilot_core/manifest.json
   grep -r '^version:' /config/.openclaw/workspace/pilotsuite-styx-core/copilot_core/config.yaml
   ```
   Expected: All show same version (13.0.3 or whatever is agreed)

3. **Check dashboard API:**
   ```bash
   curl http://localhost:8766/api/status | jq .version
   ```
   Expected: Returns `13.0.3`

4. **Restart Home Assistant** and verify:
   - Only ONE PilotSuite Core add-on appears
   - Version matches across UI, manifest, and config

---

**Audit Complete.**  
**Next Steps:** Apply P0 fixes immediately, then proceed with P1 and P2.
