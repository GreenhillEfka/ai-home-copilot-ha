# Backup & Recovery Guide

## Backup Strategy

### What to Backup

| Component | Priority | Frequency | Size Estimate |
|-----------|----------|-----------|---------------|
| Patterns & Habits | Critical | Daily | 10-100 MB |
| Vector Store | Critical | Daily | 100 MB - 1 GB |
| Knowledge Graph | Critical | Daily | 50-500 MB |
| Configurations | High | Weekly | < 1 MB |
| Preferences | High | Weekly | < 10 MB |
| Logs | Low | Weekly | 100 MB - 1 GB |
| Cache | None | - | - |

---

## Automated Backups

### Enable Automated Backups

```yaml
# configuration.yaml
pilotsuite:
  backup:
    enabled: true
    destination: /config/pilotsuite/backups
    schedule: "0 2 * * *"  # Daily at 2 AM
    retention:
      daily: 7
      weekly: 4
      monthly: 12
    compression: true
    encryption: true
```

### Backup Contents

Each backup includes:
- `patterns/` — Learned patterns and habits
- `vectors/` — Vector store index
- `graph/` — Knowledge graph data
- `preferences/` — User preferences
- `config/` — Configuration files
- `manifest.json` — Backup metadata

---

## Manual Backups

### Create Backup via Service

```yaml
# automations.yaml
- alias: "PilotSuite Create Backup"
  trigger:
    platform: time
    at: "02:00:00"
  action:
    - service: pilotsuite.create_backup
      data:
        include_patterns: true
        include_vectors: true
        include_graph: true
        include_configs: true
        compress: true
```

### Create Backup via API

```bash
curl -X POST http://localhost:8080/api/v1/backup/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "include_patterns": true,
    "include_vectors": true,
    "include_graph": true,
    "compress": true
  }'
```

### Backup via Script

```bash
#!/bin/bash
# /config/pilotsuite/scripts/backup.sh

BACKUP_DIR="/config/pilotsuite/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/pilotsuite_backup_$DATE.tar.gz"

# Create backup
tar -czf "$BACKUP_FILE" \
  /config/pilotsuite/patterns \
  /config/pilotsuite/vectors \
  /config/pilotsuite/graph \
  /config/pilotsuite/preferences \
  /config/pilotsuite/configs

# Remove old backups (keep 7 days)
find "$BACKUP_DIR" -name "pilotsuite_backup_*.tar.gz" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE"
```

---

## Remote Backups

### S3 Backup

```yaml
# configuration.yaml
pilotsuite:
  backup:
    remote:
      enabled: true
      type: s3
      bucket: pilotsuite-backups
      region: us-east-1
      access_key: ${AWS_ACCESS_KEY}
      secret_key: ${AWS_SECRET_KEY}
      prefix: backups/
      encryption: true
```

### Google Drive Backup

```yaml
pilotsuite:
  backup:
    remote:
      enabled: true
      type: gdrive
      folder_id: ${GDRIVE_FOLDER_ID}
      credentials_file: /config/pilotsuite/gdrive_credentials.json
```

### SCP Backup

```yaml
pilotsuite:
  backup:
    remote:
      enabled: true
      type: scp
      host: backup.example.com
      port: 22
      user: pilotsuite
      path: /backups/pilotsuite
      key_file: /config/pilotsuite/ssh_key
```

---

## Recovery Procedures

### Full Recovery

1. **Stop PilotSuite:**
   ```bash
   # In Home Assistant
   Settings → System → Restart
   ```

2. **Restore Backup:**
   ```bash
   # Extract backup
   cd /config/pilotsuite
   tar -xzf /path/to/backup.tar.gz
   
   # Set permissions
   chown -R homeassistant:homeassistant /config/pilotsuite
   ```

3. **Restart PilotSuite:**
   ```bash
   # In Home Assistant
   Settings → System → Restart
   ```

### Recovery via API

```bash
curl -X POST http://localhost:8080/api/v1/backup/restore \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "backup_file": "/config/pilotsuite/backups/pilotsuite_backup_20260407_020000.tar.gz",
    "include_patterns": true,
    "include_vectors": true,
    "include_graph": true
  }'
```

### Recovery via Service

```yaml
- alias: "PilotSuite Restore Backup"
  trigger:
    platform: event
    event_type: pilotsuite_restore_requested
  action:
    - service: pilotsuite.restore_backup
      data:
        backup_file: "/config/pilotsuite/backups/pilotsuite_backup_20260407_020000.tar.gz"
```

---

## Disaster Recovery Plan

### RTO/RPO Targets

| Scenario | RTO (Recovery Time) | RPO (Recovery Point) |
|----------|---------------------|----------------------|
| Single file corruption | 5 minutes | 0 (no data loss) |
| Full system failure | 1 hour | 24 hours (daily backup) |
| Datacenter loss | 4 hours | 24 hours (remote backup) |

### DR Steps

1. **Assess Damage:**
   - Identify affected components
   - Check backup availability
   - Estimate recovery time

2. **Notify Stakeholders:**
   - Send status update
   - Provide ETA for recovery

3. **Execute Recovery:**
   - Follow recovery procedure
   - Verify data integrity
   - Test functionality

4. **Post-Recovery:**
   - Monitor for issues
   - Update documentation
   - Review and improve

---

## Backup Verification

### Verify Backup Integrity

```bash
# List backup contents
tar -tzf pilotsuite_backup_20260407_020000.tar.gz

# Verify checksum
sha256sum pilotsuite_backup_20260407_020000.tar.gz

# Test restore (dry run)
tar -xzf pilotsuite_backup_20260407_020000.tar.gz --to-command="echo Would extract:"
```

### Automated Verification

```yaml
# configuration.yaml
pilotsuite:
  backup:
    verify:
      enabled: true
      schedule: "0 3 * * *"  # Daily at 3 AM (after backup)
      test_restore: true
      notify_on_failure: true
```

---

## Backup Monitoring

### Prometheus Metrics

```
pilotsuite_backup_last_success_timestamp
pilotsuite_backup_last_failure_timestamp
pilotsuite_backup_total_count
pilotsuite_backup_total_size_bytes
pilotsuite_backup_duration_seconds
pilotsuite_backup_remote_sync_status
```

### Alerting Rules

```yaml
# prometheus_alerts.yml
groups:
  - name: pilotsuite_backup
    rules:
      - alert: BackupFailed
        expr: pilotsuite_backup_last_failure_timestamp > pilotsuite_backup_last_success_timestamp
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "PilotSuite backup failed"
          description: "Last backup failed at {{ $value }}"

      - alert: BackupOld
        expr: time() - pilotsuite_backup_last_success_timestamp > 86400
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "PilotSuite backup is old"
          description: "Last backup was {{ $value | humanizeDuration }} ago"
```

---

## Encryption

### Enable Encryption

```yaml
pilotsuite:
  backup:
    encryption:
      enabled: true
      algorithm: aes-256-gcm
      key_file: /config/pilotsuite/backup_key
      key_rotation: true
      rotation_days: 90
```

### Key Management

```bash
# Generate encryption key
openssl rand -base64 32 > /config/pilotsuite/backup_key

# Set permissions
chmod 600 /config/pilotsuite/backup_key

# Backup key securely
cp /config/pilotsuite/backup_key /secure/location/backup_key_backup
```

---

*Last updated: 2026-04-07*
*Version: 1.0.0*
