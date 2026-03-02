# 🚀 RELEASE-PIPELINE v4.0 — HA+Core Sync

**Erstellt:** 2026-03-02 14:50 CET  
**Status:** 🟢 AKTIV  
**Prinzip:** **IMMER HA+Core gemeinsam releasen!**

---

## 🎯 PROBLEM (Bisher):

❌ **HA zeigt v11.2.3** während **Core auf v12.x.x** ist  
❌ **Keine Sync** vor Releases  
❌ **Getrennte Workflows** führen zu Version-Chaos  

---

## ✅ LÖSUNG (Ab sofort):

### **GOLDENE REGEL:**
> **"KEIN RELEASE OHNE HA+Core SYNC!"**

Jedes Release muss **BEIDE Repos** auf gleiche Version bringen:
- `pilotsuite-styx-core`: v12.15.0
- `pilotsuite-styx-ha`: v12.15.0 (NICHT v11.2.3!)

---

## 🔄 RELEASE-WORKFLOW (Synchronisiert)

### **Phase 1: Pre-Release Sync Check** (5 Min)

```bash
# @toolix prüft vor JEDEM Release:

# 1. Core Version lesen
CORE_VERSION=$(cat pilotsuite-styx-core/VERSION)

# 2. HA Version lesen  
HA_VERSION=$(cat pilotsuite-styx-ha/VERSION)

# 3. Sync prüfen
if [ "$CORE_VERSION" != "$HA_VERSION" ]; then
    echo "🚨 VERSION MISMATCH! Core: $CORE_VERSION, HA: $HA_VERSION"
    echo "🔧 Starte Auto-Sync..."
    
    # HA Version auf Core setzen
    echo "$CORE_VERSION" > pilotsuite-styx-ha/VERSION
    
    # CHANGELOG syncen
    cp pilotsuite-styx-core/CHANGELOG.md pilotsuite-styx-ha/CHANGELOG.md
    
    # Commit
    git add VERSION CHANGELOG.md
    git commit -m "chore: Sync HA version to Core v$CORE_VERSION"
    git push
fi

echo "✅ HA+Core synchron: v$CORE_VERSION"
```

---

### **Phase 2: Parallele Tests** (10 Min)

```bash
# @groky läuft Tests in BEIDEN Repos parallel:

# Core Tests
cd pilotsuite-styx-core && pytest -q tests/ --tb=short

# HA Tests (parallel)
cd pilotsuite-styx-ha && pytest -q tests/ --tb=short

# Beide müssen grün sein für Release!
```

---

### **Phase 3: Dual-Release** (5 Min)

```bash
# @clawdya erstellt Releases in BEIDEN Repos:

# 1. Core Release
cd pilotsuite-styx-core
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin --tags
gh release create "v$VERSION" --title "v$VERSION" --notes-file CHANGELOG.md

# 2. HA Release (sofort danach)
cd pilotsuite-styx-ha
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin --tags
gh release create "v$VERSION" --title "v$VERSION" --notes-file CHANGELOG.md

# 3. WhatsApp-Summary (BEIDE Repos)
send_whatsapp("📦 RELEASE v$VERSION:
✅ Core: https://github.com/GreenhillEfka/pilotsuite-styx-core/releases/tag/v$VERSION
✅ HA: https://github.com/GreenhillEfka/Home-Assistant-Copilot/releases/tag/v$VERSION
🔒 HA+Core synchron!")
```

---

## 📊 VERSION-MATRIX (Live)

| Repo | Aktuell | Ziel | Status |
|------|---------|------|--------|
| **Core** | v12.14.0 | v12.15.0 | 🟢 Nächste Iteration |
| **HA** | v11.2.3 ❌ | v12.15.0 | 🔴 **MUST SYNC!** |

---

## 🚨 AUTO-SYNC BEI MISMATCH

### **Trigger:**
- Vor JEDEM Release
- Bei `git push` zu main
- Alle 20 Min (Cron-Job)

### **Auto-Fix:**
```yaml
# .github/workflows/sync-versions.yml
name: Sync HA+Core Versions

on:
  push:
    branches: [main]
  schedule:
    - cron: '*/20 * * * *'  # Alle 20 Min

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Check Version Sync
        run: |
          CORE_VER=$(cat pilotsuite-styx-core/VERSION)
          HA_VER=$(cat pilotsuite-styx-ha/VERSION)
          
          if [ "$CORE_VER" != "$HA_VER" ]; then
            echo "::warning::Version mismatch! Core: $CORE_VER, HA: $HA_VER"
            echo "::warning::Auto-fixing HA version..."
            
            # HA Version auf Core setzen
            echo "$CORE_VER" > pilotsuite-styx-ha/VERSION
            echo "$CORE_VER" > pilotsuite-styx-ha/copilot_core/VERSION
            
            # Auto-commit wenn Changes
            git config --local user.email "action@github.com"
            git config --local user.name "GitHub Action"
            git add pilotsuite-styx-ha/VERSION
            git commit -m "chore: Auto-sync HA version to Core v$CORE_VER" || echo "No changes to commit"
            git push || echo "Push failed (expected for PRs)"
          else
            echo "✅ Versions synchron: v$CORE_VER"
          fi
```

---

## 📱 WHATSAPP-ALERT BEI MISMATCH

```python
# @clawdya sendet Alert bei Version-Mismatch:

def check_version_sync():
    core_ver = read_version('pilotsuite-styx-core/VERSION')
    ha_ver = read_version('pilotsuite-styx-ha/VERSION')
    
    if core_ver != ha_ver:
        alert = f"""
🚨 VERSION MISMATCH DETECTED!

Core: v{core_ver}
HA:   v{ha_ver} ❌

🔧 Auto-Sync wird gestartet...
⏰ Release verzögert sich um ~5 Min

@toolix übernimmt die Sync!
"""
        send_whatsapp(alert)
        trigger_auto_sync()
    else:
        send_whatsapp(f"✅ HA+Core synchron: v{core_ver}")
```

---

## ✅ CHECKLISTE PRO RELEASE

### **Vor Release (@toolix):**
- [ ] Core Version lesen
- [ ] HA Version lesen
- [ ] Bei Mismatch: Auto-Sync starten
- [ ] HA CHANGELOG mit Core syncen
- [ ] Sync-Commit pushen
- [ ] WhatsApp: "Sync complete"

### **Während Release (@groky):**
- [ ] Core Tests laufen (müssen grün sein)
- [ ] HA Tests laufen (müssen grün sein)
- [ ] BEIDE grün? → Release GO
- [ ] Eines rot? → Release BLOCKED, Fix first

### **Nach Release (@clawdya):**
- [ ] Core Tag + GitHub Release
- [ ] HA Tag + GitHub Release (sofort danach)
- [ ] WhatsApp-Summary mit BEIDEN Links
- [ ] Version in TASK_QUEUE.md aktualisieren
- [ ] Nächste Iteration starten

---

## 🎯 AKTUELLE AKTION (SOFORT):

### **HA Version fixen (v11.2.3 → v12.14.0):**

```bash
# @toolix macht das JETZT:

cd /config/.openclaw/workspace/pilotsuite-styx-ha

# 1. Version auf Core setzen
echo "v12.14.0" > VERSION
echo "v12.14.0" > copilot_core/VERSION

# 2. CHANGELOG syncen
cp ../pilotsuite-styx-core/CHANGELOG.md CHANGELOG.md

# 3. Commit + Push
git add VERSION copilot_core/VERSION CHANGELOG.md
git commit -m "chore: Sync HA version to Core v12.14.0 (Fix v11.2.3 mismatch)"
git push origin main

# 4. WhatsApp
send_whatsapp("✅ HA Version fixiert: v11.2.3 → v12.14.0
🔒 HA+Core jetzt synchron!
📦 Nächste Iteration: v12.15.0")
```

---

## 📈 METRIKEN

| Metrik | Ziel | Aktuell |
|--------|------|---------|
| **HA+Core Sync** | 100% | ❌ 0% (v11.2.3 vs v12.14.0) |
| **Auto-Sync Time** | <5 Min | - |
| **Version Mismatches/Tag** | 0 | ~5 |
| **Release-Blocker durch Sync** | 0 | ~3 |

---

**Erstellt:** 2026-03-02 14:50 CET  
**Status:** 🟢 AKTIV  
**Nächste Aktion:** HA Version fixen (v11.2.3 → v12.14.0)

---

💋✨ **AB JETZT: KEIN RELEASE OHNE HA+Core SYNC!** 🚀
