# Chaos Engineering Tests für PilotSuite

## Übersicht

Dieses Verzeichnis enthält Chaos Mesh Manifeste für automatisierte Resilienz-Tests der PilotSuite-Komponenten.

## Installation

### Voraussetzungen

- Kubernetes Cluster (v1.20+)
- Chaos Mesh installiert: `helm install chaos-mesh chaos-mesh/chaos-mesh -n chaos-mesh`
- kubectl Zugriff auf den Cluster

### Deployment

```bash
# Alle Chaos-Experiments deployen
kubectl apply -k .

# Oder einzeln
kubectl apply -f namespace.yaml
kubectl apply -f pod-kill-experiment.yaml
kubectl apply -f network-latency-experiment.yaml
kubectl apply -f stress-test-experiment.yaml
kubectl apply -f resilience-validation.yaml
```

## Failure Scenarios

### 1. Pod Kill Experiments (`pod-kill-experiment.yaml`)

| Experiment | Ziel | Modus | Dauer | Frequenz |
|------------|------|-------|-------|----------|
| pilotclaw-pod-kill | PilotClaw Pods | one | 0s | Alle 30 Min |
| copilot-pod-kill | Copilot HA Pods | 50% random | 30s | Stündlich |
| openclaw-gateway-pod-kill | Gateway Pods | one | 15s | Alle 45 Min |
| symbiosis-pod-kill | Symbiosis Pods | 33% random | 60s | Alle 2 Std |

### 2. Network Latency Experiments (`network-latency-experiment.yaml`)

| Experiment | Quelle | Ziel | Latenz | Jitter | Dauer |
|------------|--------|------|--------|--------|-------|
| pilotclaw-network-latency | PilotClaw | Home Assistant | 100ms | 50ms | 5 Min |
| gateway-backend-latency | Gateway | Agent | 250ms | 100ms | 10 Min |
| symbiosis-metrics-latency | Symbiosis | Prometheus | 500ms | 200ms | 15 Min |
| network-partition-test | PilotClaw | Home Assistant | Partition | - | 60s |

### 3. Stress Test Experiments (`stress-test-experiment.yaml`)

| Experiment | Typ | Intensität | Dauer |
|------------|-----|-----------|-------|
| pilotclaw-cpu-stress | CPU | 80% Load, 2 Workers | 2 Min |
| openclaw-memory-stress | Memory | 256MB, 50% Pods | 3 Min |
| home-assistant-io-stress | IO | 128MB, 2 Workers | 5 Min |
| symbiosis-combined-stress | CPU+Memory | 60% CPU, 512MB | 4 Min |

## Resilience Validation

### Automatisierte Validierung (`resilience-validation.yaml`)

- **CronJob**: Tägliche Health-Checks um 6:00 Uhr
- **Workflow**: Orchestrierte Test-Sequenz mit Validation
- **Schedule**: Automatische Ausführung täglich um Mitternacht

### Manuelle Validierung

```bash
# Workflow manuell starten
kubectl create job --from=cronjob/resilience-validator manual-validation -n chaos-mesh

# Workflow Status prüfen
kubectl get workflow resilience-test-workflow -n chaos-mesh -o yaml

# Logs ansehen
kubectl logs -l app=resilience-validator -n chaos-mesh --tail=100
```

## Monitoring

### Chaos Mesh Dashboard

```bash
# Dashboard port-forwarden
kubectl port-forward svc/chaos-dashboard 23333:23333 -n chaos-mesh
```

Unter http://localhost:23333 einsehen.

### Prometheus Integration

```yaml
# ServiceMonitor für Chaos Mesh Metrics
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: chaos-mesh
  namespace: chaos-mesh
spec:
  selector:
    matchLabels:
      app.kubernetes.io/component: chaos-mesh
  endpoints:
    - port: metrics
      interval: 30s
```

## Wichtige Commands

```bash
# Alle laufenden Experiments anzeigen
kubectl get chaos -n chaos-mesh

# Spezifisches Experiment anzeigen
kubectl get podchaos pilotclaw-pod-kill -n chaos-mesh -o yaml

# Experiment pausieren
kubectl patch podchaos pilotclaw-pod-kill -n chaos-mesh -p '{"spec":{"suspend":true}}'

# Experiment fortsetzen
kubectl patch podchaos pilotclaw-pod-kill -n chaos-mesh -p '{"spec":{"suspend":false}}'

# Experiment löschen
kubectl delete podchaos pilotclaw-pod-kill -n chaos-mesh

# Alle Chaos-Resources löschen
kubectl delete -k .
```

## Sicherheitshinweise

1. **Nicht in Production einsetzen** ohne vorherige Validierung in Staging
2. **Backup-Strategie** vor ersten Tests sicherstellen
3. **Alerting konfigurieren** für schnelle Reaktion bei echten Ausfällen
4. **Time-Window beachten**: Experiments laufen in Low-Traffic-Zeiten (0-6 Uhr)

## Troubleshooting

### Chaos Mesh installiert?

```bash
kubectl get pods -n chaos-mesh
helm list -n chaos-mesh
```

### Experiment startet nicht?

```bash
# Events prüfen
kubectl describe podchaos pilotclaw-pod-kill -n chaos-mesh

# Chaos Mesh Logs
kubectl logs -l app.kubernetes.io/component=controller-manager -n chaos-mesh
```

### Validation schlägt fehl?

```bash
# Manuelle Health-Checks
curl http://pilotclaw.pilotsuite.svc/health
curl http://openclaw-gateway.pilotsuite.svc:8080/health
curl http://symbiosis.pilotsuite.svc/health
```

## Nächste Schritte

1. [ ] Chaos Mesh im Staging-Cluster installieren
2. [ ] Erste Experiments manuell testen
3. [ ] Alerting-Regeln für Chaos-Events definieren
4. [ ] Automatisierte Reports einrichten
5. [ ] Production-Readiness Review durchführen
