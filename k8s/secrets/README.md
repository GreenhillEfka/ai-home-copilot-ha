# Secrets Management - PilotSuite

## Overview

This directory contains Kubernetes manifests for comprehensive secrets management using the External Secrets Operator (ESO). The implementation provides:

1. **External Secrets Operator** - Syncs secrets from external secret managers (Vault, AWS Secrets Manager, Azure Key Vault)
2. **Secret Rotation Policy** - Automated rotation schedules with approval workflows
3. **Audit Logging** - Complete audit trail for all secret operations
4. **Monitoring & Alerting** - Prometheus metrics and Grafana dashboards

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Vault / AWS /  │────▶│ External Secrets     │────▶│  Kubernetes     │
│  Azure Key Vault│     │ Operator             │     │  Secrets        │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────────┐
                        │  Rotation Scheduler  │
                        │  Audit Logger        │
                        │  Monitoring          │
                        └──────────────────────┘
```

## Components

### 1. External Secrets Operator (`external-secrets-operator.yaml`)
- HelmRelease for ESO installation via Flux
- ServiceMonitor for Prometheus metrics
- Webhook and cert-controller for validation

### 2. Secret Stores (`external-secret-store.yaml`, `cluster-secret-store.yaml`)
- **SecretStore**: Namespace-scoped (Vault backend)
- **ClusterSecretStore**: Cluster-wide access to:
  - HashiCorp Vault (primary)
  - AWS Secrets Manager (fallback)
  - Azure Key Vault (fallback)

### 3. External Secrets (`external-secrets.yaml`)
Pre-configured ExternalSecret resources:
- `db-credentials`: Database connection strings (30d rotation)
- `api-keys`: Third-party API tokens (90d rotation)
- `tls-certificates`: TLS certificates (365d rotation)
- `oauth-credentials`: OAuth client secrets (180d rotation)

### 4. Secret Rotation (`secret-rotation-policy.yaml`)
- PushSecret configuration for rotation policies
- CronJob for daily rotation checks
- PrometheusRule alerts for:
  - Secrets approaching rotation deadline (80% threshold)
  - Failed rotation attempts
  - ESO downtime
- Rotation scripts with approval workflows

### 5. Audit Logging (`audit-logging-config.yaml`)
- Kubernetes Audit Policy for secret operations
- Fluentd/Fluentbit log forwarding to Elasticsearch
- Grafana dashboard for visualization
- RBAC for audit log access

## Installation

### Prerequisites
- Kubernetes 1.25+
- Flux CD installed
- Vault/AWS/Azure configured
- Prometheus Operator installed

### Deploy

```bash
# Navigate to secrets directory
cd /config/clawd/k8s/secrets

# Apply all manifests
kubectl apply -k .

# Or apply individually
kubectl apply -f external-secrets-operator.yaml
kubectl apply -f external-secret-store.yaml
kubectl apply -f cluster-secret-store.yaml
kubectl apply -f external-secrets.yaml
kubectl apply -f secret-rotation-policy.yaml
kubectl apply -f audit-logging-config.yaml
```

### Verify Installation

```bash
# Check ESO pods
kubectl get pods -n external-secrets

# Check ExternalSecrets status
kubectl get externalsecrets -n pilot-suite

# Check SecretStores
kubectl get secretstores -n pilot-suite
kubectl get clustersecretstores

# View synced secrets
kubectl get secrets -n pilot-suite -l managed-by=external-secrets
```

## Rotation Policies

| Secret Type | Rotation Interval | Auto-Rotate | Approval Required |
|-------------|------------------|-------------|-------------------|
| Database    | 30 days          | Yes         | No                |
| API Keys    | 90 days          | Yes         | Yes               |
| OAuth       | 180 days         | No          | Yes               |
| TLS         | 365 days         | Yes         | No                |
| Service Accounts | 60 days     | Yes         | No                |

## Audit Logging

All secret operations are logged with:
- **RequestResponse level**: Full request and response for mutations
- **Metadata level**: Request metadata for reads by ESO
- **Retention**: 365 days in Elasticsearch
- **Alerting**: Telegram notifications for sensitive operations

### Query Audit Logs

```bash
# View recent secret operations
kubectl logs -n kube-system -l component=kube-apiserver | \
  jq 'select(.objectRef.resource=="secrets")'

# Search Elasticsearch (via Kibana)
resource:secrets AND verb:delete
```

## Monitoring

### Prometheus Metrics

- `external_secrets_secret_sync_calls_total`: Sync attempts
- `external_secrets_secret_sync_duration_seconds`: Sync latency
- `external_secrets_secret_last_sync_timestamp_seconds`: Last successful sync

### Grafana Dashboard

Import the dashboard from `audit-logging-config.yaml` ConfigMap or access via:
```
https://grafana.pilot-suite.internal/d/secrets-audit
```

## Security Considerations

1. **RBAC**: ServiceAccount `external-secrets-sa` has minimal required permissions
2. **Network Policies**: Restrict ESO to Vault/API endpoints only
3. **Encryption**: Audit logs encrypted at rest in Elasticsearch
4. **Backup**: Secrets backed up before rotation (see `backup-secret.sh`)
5. **No Git Storage**: Actual secret values NEVER committed to Git

## Troubleshooting

### ESO not syncing secrets

```bash
# Check ESO logs
kubectl logs -n external-secrets -l app.kubernetes.io/name=external-secrets

# Check ExternalSecret events
kubectl describe externalsecret <name> -n pilot-suite

# Verify SecretStore connectivity
kubectl get secretstore vault-backend -n pilot-suite -o yaml
```

### Rotation failing

```bash
# Check rotation CronJob logs
kubectl logs job.batch/secret-rotation-checker -n pilot-suite

# Verify Vault token validity
kubectl get secret vault-token -n pilot-suite -o jsonpath='{.data.token}' | base64 -d
```

### Audit logs missing

```bash
# Check audit policy applied
kubectl get configmap secrets-audit-config -n pilot-suite -o jsonpath='{.data.audit-policy\.yaml}'

# Verify Fluentd pods running
kubectl get pods -n pilot-suite -l app=fluent-bit
```

## References

- [External Secrets Operator Docs](https://external-secrets.io/latest/)
- [Kubernetes Audit Logging](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
- [HashiCorp Vault Kubernetes Auth](https://www.vaultproject.io/docs/auth/kubernetes)
