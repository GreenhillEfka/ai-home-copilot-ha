# 📘 Deployment Runbook — PilotSuite Production

**Version:** 15.3.38  
**Letzte Aktualisierung:** 2026-04-06  
**Branch:** takeover/main  
**Status:** ✅ PRODUCTION READY

---

## 📋 INHALT

1. [Step-by-Step Deploy-Anleitung](#1-step-by-step-deploy-anleitung)
2. [Rollback-Prozedur](#2-rollback-prozedur)
3. [Health Check Liste](#3-health-check-liste)
4. [Commit & Release Workflow](#4-commit--release-workflow)

---

## 1. STEP-BY-STEP DEPLOY-ANLEITUNG

### 1.1 Voraussetzungen prüfen

```bash
# Git Status prüfen
git -C /config/clawd status
git -C /config/clawd branch --show-current

# Aktuelle Version prüfen
cat /config/clawd/VERSION

# Remote Connectivity prüfen
git -C /config/clawd remote -v
```

**Checkliste:**
- [ ] Branch ist `takeover/main` oder Ziel-Branch
- [ ] Keine uncommitted Changes
- [ ] VERSION-Datei entspricht Release-Tag
- [ ] CHANGELOG.md ist aktuell

---

### 1.2 Pre-Deployment Checks

```bash
# 1. Repository auf aktuellstem Stand
cd /config/clawd
git fetch origin
git log --oneline -5

# 2. Dependencies prüfen
ls -la /config/clawd/custom_components/copilot_ha/
cat /config/clawd/custom_components/copilot_ha/manifest.json | jq .version

# 3. Kubernetes Manifeste validieren
cd /config/clawd/k8s/symbiosis
cat kustomization.yaml
kubectl kustomize . --dry-run=client 2>&1 | head -20

# 4. Docker Image Tag prüfen
cat /config/clawd/Dockerfile | grep "version="
```

**Checkliste:**
- [ ] Latest Commit pulled
- [ ] Component Version stimmt mit VERSION überein
- [ ] K8s Manifeste sind valide
- [ ] Docker Image Tag ist korrekt

---

### 1.3 Deployment durchführen

#### Option A: Kubernetes Deployment (Empfohlen)

```bash
# 1. Namespace prüfen/erstellen
kubectl get namespace symbiosis || kubectl create namespace symbiosis

# 2. ConfigMap anwenden
kubectl apply -k /config/clawd/k8s/symbiosis/ --namespace symbiosis

# 3. Deployment Status prüfen
kubectl get deployments -n symbiosis
kubectl get pods -n symbiosis -w

# 4. Auf Ready warten (Timeout: 300s)
kubectl wait --for=condition=available deployment/symbiosis -n symbiosis --timeout=300s
```

#### Option B: Docker/Home Assistant Deployment

```bash
# 1. Home Assistant Neustart vorbereiten
# Backup erstellen
ha backups create --name "pre-deploy-$(date +%Y%m%d-%H%M%S)"

# 2. Component Files kopieren (falls manuell)
cp -r /config/clawd/custom_components/copilot_ha/ /config/custom_components/

# 3. Home Assistant neu starten
ha core restart

# 4. Logs überwachen
ha core logs --follow
```

#### Option C: HACS Deployment (Produktion)

```bash
# 1. HACS Repository aktualisieren
# Über HA UI: HACS → Integration → PilotSuite → Update

# 2. ODER via CLI (wenn verfügbar)
hacs install --repository GreenhillEfka/pilotsuite-styx-ha --category integration

# 3. Home Assistant neu starten
ha core restart
```

---

### 1.4 Post-Deployment Verifikation

```bash
# 1. Pod Status (K8s)
kubectl get pods -n symbiosis -o wide

# 2. Service Endpoints prüfen
kubectl get svc -n symbiosis

# 3. Logs prüfen (letzte 50 Zeilen)
kubectl logs -n symbiosis deployment/symbiosis --tail=50

# 4. Health Endpoint testen
kubectl port-forward -n symbiosis svc/symbiosis 8080:8080 &
curl -f http://localhost:8080/health
curl -f http://localhost:8080/ready

# 5. Home Assistant Integration prüfen
# Über HA UI: Einstellungen → Geräte & Dienste → PilotSuite Styx
```

**Checkliste:**
- [ ] Alle Pods Running (1/1 Ready)
- [ ] Keine CrashLoopBackOff Errors
- [ ] Health Check erfolgreich (HTTP 200)
- [ ] Readiness Check erfolgreich (HTTP 200)
- [ ] HA Integration sichtbar und verbunden

---

## 2. ROLLBACK-PROZEDUR

### 2.1 Rollback Trigger

**Automatische Trigger:**
- Health Check fails > 3 consecutive times
- Pod CrashLoopBackOff > 5 minutes
- Readiness Probe fails > 300 seconds
- Error Rate > 10% in 5 minutes

**Manuelle Trigger:**
- Funktionale Regression erkannt
- Performance Degradation > 50%
- Critical Bug in Production

---

### 2.2 Kubernetes Rollback

```bash
# 1. Deployment History anzeigen
kubectl rollout history deployment/symbiosis -n symbiosis

# 2. Zurück zur vorherigen Revision
kubectl rollout undo deployment/symbiosis -n symbiosis

# 3. ODER zu spezifischer Revision
kubectl rollout undo deployment/symbiosis -n symbiosis --to-revision=<N>

# 4. Rollback Status überwachen
kubectl rollout status deployment/symbiosis -n symbiosis --timeout=300s

# 5. Verifikation
kubectl get pods -n symbiosis -w
kubectl logs -n symbiosis deployment/symbiosis --tail=100
```

---

### 2.3 Home Assistant Rollback

```bash
# 1. Backup Liste anzeigen
ha backups list

# 2. Backup restore (ACHTUNG: Vollständiger Restore!)
ha backups restore --slug <BACKUP_SLUG>

# 3. ODER nur Component zurückrollen (manuell)
# Backup-Pfad ermitteln
ls -la /config/backups/

# Alte Component Version wiederherstellen
cp -r /config/backups/<BACKUP>/custom_components/copilot_ha/ /config/custom_components/

# Home Assistant neu starten
ha core restart
```

---

### 2.4 Git Rollback

```bash
# 1. Letzten stabilen Commit identifizieren
git log --oneline -10

# 2. Branch auf stabilen Commit setzen
git checkout takeover/main
git reset --hard <STABLE_COMMIT_HASH>

# 3. Force Push (nur wenn notwendig!)
git push origin takeover/main --force

# 4. Deployment neu triggern
# (Siehe Section 1.3)
```

---

### 2.5 Rollback Verifikation

```bash
# 1. Version prüfen
cat /config/clawd/VERSION

# 2. Health Check
curl -f http://localhost:8123/api/config

# 3. Integration Status in HA
# UI: Einstellungen → Geräte & Dienste → PilotSuite Styx

# 4. Logs prüfen (keine Errors)
ha core logs --tail=200 | grep -i error
```

**Checkliste:**
- [ ] Vorherige Version aktiv
- [ ] Alle Pods healthy
- [ ] HA Integration verbunden
- [ ] Keine Errors in Logs
- [ ] Stakeholder informiert

---

## 3. HEALTH CHECK LISTE

### 3.1 Infrastructure Health

| Check | Command | Expected | Critical |
|-------|---------|----------|----------|
| **Pod Status** | `kubectl get pods -n symbiosis` | Running | NotRunning/CrashLoop |
| **Replica Count** | `kubectl get deploy symbiosis -n symbiosis` | 2/2 | < 2 |
| **CPU Usage** | `kubectl top pods -n symbiosis` | < 80% Limit | > 95% |
| **Memory Usage** | `kubectl top pods -n symbiosis` | < 80% Limit | > 95% |
| **Restart Count** | `kubectl get pods -n symbiosis -o wide` | 0-2 | > 5 |

---

### 3.2 Application Health

| Check | Command | Expected | Critical |
|-------|---------|----------|----------|
| **Liveness Probe** | `curl -f http://<POD_IP>:8080/health` | HTTP 200 | HTTP 5xx |
| **Readiness Probe** | `curl -f http://<POD_IP>:8080/ready` | HTTP 200 | HTTP 5xx |
| **Metrics Endpoint** | `curl -f http://<POD_IP>:8080/metrics` | HTTP 200 | Timeout |
| **Response Time** | `curl -w "%{time_total}" http://<POD_IP>:8080/health` | < 500ms | > 2000ms |

---

### 3.3 Home Assistant Integration Health

| Check | Command/Path | Expected | Critical |
|-------|--------------|----------|----------|
| **Config API** | `/api/config` | HTTP 200 | HTTP 5xx |
| **Integration Loaded** | `/config/custom_components/copilot_ha/` | Exists | Missing |
| **manifest.json** | `cat manifest.json \| jq .version` | = VERSION | Mismatch |
| **Core Connection** | HA UI → Devices & Services | Connected | Not Found |
| **Zone Sync** | `sensor.pilotsuite_system_health` | online | offline |

---

### 3.4 Business Logic Health

| Check | Entity/Endpoint | Expected | Critical |
|-------|-----------------|----------|----------|
| **Intelligence Score** | `sensor.pilotsuite_intelligence_score` | > 0 | unavailable |
| **Patterns Learned** | `sensor.pilotsuite_patterns_learned` | ≥ 0 | unavailable |
| **Active Automations** | `sensor.pilotsuite_active_automations` | ≥ 0 | unavailable |
| **Anomaly Detection** | `sensor.pilotsuite_anomaly_detected` | Boolean | unavailable |
| **Mood State** | `sensor.pilotsuite_mood_state` | Valid State | unavailable |

---

### 3.5 Automated Health Check Script

```bash
#!/bin/bash
# /config/clawd/scripts/healthcheck-production.sh

set -e

NAMESPACE="symbiosis"
DEPLOYMENT="symbiosis"
TIMEOUT=30

echo "🏥 Production Health Check — $(date)"
echo "======================================"

# 1. Pod Status
echo -n "✓ Pod Status: "
PODS=$(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT -o jsonpath='{.items[*].status.phase}')
if [[ "$PODS" == *"Running"* ]]; then
    echo "OK"
else
    echo "CRITICAL"
    exit 1
fi

# 2. Replica Count
echo -n "✓ Replica Count: "
READY=$(kubectl get deploy $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
if [[ "$READY" -ge 2 ]]; then
    echo "OK ($READY/2)"
else
    echo "WARNING ($READY/2)"
fi

# 3. Health Endpoint
echo -n "✓ Health Endpoint: "
if kubectl port-forward -n $NAMESPACE svc/$DEPLOYMENT 8080:8080 &>/dev/null &
then
    sleep 2
    if curl -sf --max-time $TIMEOUT http://localhost:8080/health &>/dev/null; then
        echo "OK"
    else
        echo "CRITICAL"
        exit 1
    fi
    pkill -f "port-forward.*8080" &>/dev/null || true
else
    echo "SKIP (no kubectl)"
fi

# 4. Version Check
echo -n "✓ Version Check: "
VERSION=$(cat /config/clawd/VERSION 2>/dev/null || echo "unknown")
MANIFEST_VERSION=$(cat /config/clawd/custom_components/copilot_ha/manifest.json 2>/dev/null | jq -r .version || echo "unknown")
if [[ "$VERSION" == "$MANIFEST_VERSION" ]]; then
    echo "OK ($VERSION)"
else
    echo "MISMATCH (VERSION=$VERSION, MANIFEST=$MANIFEST_VERSION)"
fi

echo "======================================"
echo "✅ Health Check Complete"
```

---

### 3.6 Health Check Frequencies

| Check Type | Frequency | Owner | Alert Channel |
|------------|-----------|-------|---------------|
| **Pod Status** | 1 min | Prometheus | Telegram |
| **Resource Usage** | 5 min | Prometheus | Telegram |
| **Health Endpoint** | 1 min | ServiceMonitor | PagerDuty |
| **Integration Status** | 15 min | HA Automation | Telegram |
| **Business Metrics** | 5 min | HA Automation | Telegram |
| **Full Audit** | Daily 03:00 | Cron Job | Email |

---

## 4. COMMIT & RELEASE WORKFLOW

### 4.1 Pre-Commit Checklist

- [ ] Alle Tests bestanden (`pytest /config/clawd/tests/`)
- [ ] CHANGELOG.md aktualisiert
- [ ] VERSION-Datei aktualisiert
- [ ] Dockerfile Version-Label aktualisiert
- [ ] manifest.json Version aktualisiert
- [ ] Dokumentation aktuell (README.md)

---

### 4.2 Commit auf takeover/main

```bash
# 1. Auf richtigen Branch wechseln
cd /config/clawd
git checkout takeover/main
git pull origin takeover/main

# 2. Changes prüfen
git status
git diff --stat

# 3. Staged Changes
git add \
    VERSION \
    CHANGELOG.md \
    Dockerfile \
    custom_components/copilot_ha/manifest.json \
    custom_components/copilot_ha/ \
    DEPLOYMENT_RUNBOOK.md

# 4. Commit mit konventionellem Message
git commit -m "release: v15.3.38 — Production Deployment Runbook

- Deployment Runbook erstellt (DEPLOYMENT_RUNBOOK.md)
- Step-by-Step Deploy-Anleitung
- Rollback-Prozedur dokumentiert
- Health Check Liste vollständig
- Alle Versionen synchronisiert

Refs: #<ISSUE_ID>"

# 5. Push mit Tags (falls Release)
git push origin takeover/main

# Optional: Tag erstellen
git tag -a v15.3.38 -m "Release v15.3.38 — Production Ready"
git push origin v15.3.38
```

---

### 4.3 Release Workflow (GitHub)

```bash
# 1. GitHub Release erstellen
gh release create v15.3.38 \
    --target takeover/main \
    --title "v15.3.38 — Production Deployment" \
    --notes-file CHANGELOG.md \
    --verify-tag

# 2. Release Notes prüfen
gh release view v15.3.38

# 3. CI/CD Status prüfen
gh run list --branch takeover/main --limit 5
```

---

### 4.4 Post-Release Actions

```bash
# 1. HACS Repository updaten
# GitHub Release → HACS auto-discover (wenn konfiguriert)

# 2. Docker Image bauen & pushen (falls verwendet)
docker build -t pilotsuite/styx-ha:v15.3.38 /config/clawd
docker push pilotsuite/styx-ha:v15.3.38
docker tag pilotsuite/styx-ha:v15.3.38 pilotsuite/styx-ha:latest
docker push pilotsuite/styx-ha:latest

# 3. Kubernetes Manifeste updaten
# Image Tag in deployment.yaml auf v15.3.38 setzen

# 4. Stakeholder informieren
# Telegram/Slack/Discord Notification
```

---

### 4.5 Release Validation

| Step | Check | Owner | Deadline |
|------|-------|-------|----------|
| **1. Commit** | takeover/main updated | Dev | T+0 |
| **2. Tag** | v15.3.38 exists | Dev | T+5min |
| **3. Release** | GitHub Release visible | Dev | T+10min |
| **4. CI/CD** | All checks green | CI | T+15min |
| **5. Deploy** | Production updated | Ops | T+30min |
| **6. Health** | All checks pass | Ops | T+35min |
| **7. Notify** | Stakeholders informed | Dev | T+40min |

---

## 📞 ESCALATION MATRIX

| Level | Contact | Response Time | Triggers |
|-------|---------|---------------|----------|
| **L1** | On-Call Dev | 15 min | Health Check Fail |
| **L2** | Tech Lead | 30 min | Rollback Required |
| **L3** | CTO/Owner | 1 hour | Data Loss Risk |
| **Emergency** | All Hands | Immediate | Complete Outage |

**Kontaktwege:**
- Telegram: @andreasbetz (A. Betz)
- Email: ops@pilotsuite.io
- PagerDuty: pilotsuite-production

---

## 📚 ANHANG

### A. Wichtige Pfade

```
/config/clawd/                          # Root Workspace
/config/clawd/VERSION                   # Versionsdatei
/config/clawd/Dockerfile                # Docker Image
/config/clawd/k8s/symbiosis/            # Kubernetes Manifeste
/config/clawd/custom_components/copilot_ha/  # HA Component
/config/clawd/scripts/                  # Deployment Scripts
```

### B. Wichtige Commands

```bash
# Quick Status
git -C /config/clawd status --short
kubectl get pods -n symbiosis
ha core info

# Quick Deploy
kubectl apply -k /config/clawd/k8s/symbiosis/ --namespace symbiosis

# Quick Rollback
kubectl rollout undo deployment/symbiosis -n symbiosis

# Quick Health
curl -f http://localhost:8123/api/config
```

### C. Version History

| Version | Date | Branch | Status |
|---------|------|--------|--------|
| 15.3.38 | 2026-04-06 | takeover/main | ✅ Current |
| 15.3.0 | 2026-04-01 | main | ✅ Stable |
| 15.2.10 | 2026-03-31 | main | ⚠️ Deprecated |

---

**🚀 PILOTSUITE — DAS LERNENDE DACHSYSTEM.**

*Dieses Runbook wird bei jedem Release aktualisiert. Letzte Prüfung: 2026-04-06*
