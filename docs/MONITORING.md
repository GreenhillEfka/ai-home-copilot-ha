# Monitoring & Observability Guide

## Prometheus Metrics

PilotSuite Core exposes the following metrics at `/metrics`:

### System Metrics

```
pilotsuite_info{version="1.0.0"}
pilotsuite_uptime_seconds
pilotsuite_memory_usage_bytes
pilotsuite_cpu_usage_percent
```

### RAG Metrics

```
pilotsuite_rag_vector_count
pilotsuite_rag_query_duration_seconds
pilotsuite_rag_query_total
pilotsuite_rag_cache_hits_total
pilotsuite_rag_cache_misses_total
```

### ML Metrics

```
pilotsuite_ml_patterns_detected
pilotsuite_ml_habits_learned
pilotsuite_ml_anomalies_detected
pilotsuite_ml_inference_duration_seconds
```

### Presence Metrics

```
pilotsuite_presence_state{state="home|away"}
pilotsuite_presence_confidence
pilotsuite_presence_sensor_count
pilotsuite_presence_sensor_value{sensor_type="pir|radar|wifi|ble"}
```

### Energy Metrics

```
pilotsuite_energy_forecast_kwh
pilotsuite_energy_optimization_savings_ct
pilotsuite_energy_solar_self_consumption_kwh
pilotsuite_energy_grid_consumption_kwh
pilotsuite_energy_scheduler_runtime_seconds
```

### API Metrics

```
pilotsuite_api_requests_total{endpoint="/api/v1/*", method="GET|POST"}
pilotsuite_api_request_duration_seconds{endpoint="/api/v1/*"}
pilotsuite_api_errors_total{endpoint="/api/v1/*"}
pilotsuite_api_rate_limit_hits_total
```

### Graph Metrics

```
pilotsuite_graph_node_count
pilotsuite_graph_edge_count
pilotsuite_graph_query_duration_seconds
pilotsuite_graph_traversal_depth
```

---

## Grafana Dashboards

### Dashboard 1: System Overview

**JSON Import ID:** (coming soon)

**Panels:**
- System uptime
- Memory usage
- CPU usage
- Request rate
- Error rate
- Response time (p50, p95, p99)

### Dashboard 2: RAG Performance

**Panels:**
- Vector count over time
- Query latency
- Cache hit rate
- Embedding generation rate
- Similarity search performance

### Dashboard 3: ML & Automation

**Panels:**
- Patterns detected per hour
- Habits learned per day
- Anomaly detection rate
- Inference latency
- Model accuracy (if labeled data available)

### Dashboard 4: Presence Detection

**Panels:**
- Presence state timeline
- Confidence over time
- Sensor contributions
- Wilson score interval
- False positive/negative rate

### Dashboard 5: Energy Optimization

**Panels:**
- Forecast vs actual consumption
- Solar self-consumption rate
- Cost savings over time
- Scheduler runtime
- Device schedules visualization

---

## Alerting Rules

### Critical Alerts

```yaml
# prometheus_alerts.yml
groups:
  - name: pilotsuite_critical
    rules:
      - alert: PilotSuiteDown
        expr: up{job="pilotsuite"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PilotSuite Core is down"
          description: "PilotSuite Core instance {{ $labels.instance }} has been down for more than 1 minute."

      - alert: HighErrorRate
        expr: rate(pilotsuite_api_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High API error rate"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: HighMemoryUsage
        expr: pilotsuite_memory_usage_bytes / 1024 / 1024 > 1500
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }} MB"
```

### Warning Alerts

```yaml
  - name: pilotsuite_warnings
    rules:
      - alert: SlowQueries
        expr: histogram_quantile(0.95, rate(pilotsuite_rag_query_duration_seconds_bucket[5m])) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow RAG queries"
          description: "95th percentile query time is {{ $value }}s"

      - alert: LowCacheHitRate
        expr: rate(pilotsuite_rag_cache_hits_total[1h]) / (rate(pilotsuite_rag_cache_hits_total[1h]) + rate(pilotsuite_rag_cache_misses_total[1h])) < 0.5
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }}"

      - alert: PresenceConfidenceLow
        expr: pilotsuite_presence_confidence < 0.5
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Low presence detection confidence"
          description: "Confidence is {{ $value }}"
```

---

## Logging Configuration

### Structured Logging

```yaml
# configuration.yaml
pilotsuite:
  logging:
    level: info  # debug, info, warning, error
    format: json  # json or text
    output: file  # file, stdout, or both
    path: /config/pilotsuite/logs
    rotation:
      max_size_mb: 100
      max_files: 10
      compress: true
```

### Log Aggregation

**Loki Configuration:**

```yaml
# loki_config.yml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093
```

### Log Queries (LogQL)

```logql
# All error logs
{app="pilotsuite"} |= "error"

# API errors
{app="pilotsuite"} |= "api" |= "error"

# Slow queries
{app="pilotsuite"} | json | query_duration_ms > 1000

# Authentication failures
{app="pilotsuite"} |= "auth" |= "failure"
```

---

## Distributed Tracing

### Jaeger Integration

```yaml
# configuration.yaml
pilotsuite:
  tracing:
    enabled: true
    type: jaeger
    endpoint: http://jaeger:14268/api/traces
    service_name: pilotsuite-core
    sampling_rate: 0.1  # 10% of requests
```

### OpenTelemetry

```yaml
pilotsuite:
  tracing:
    enabled: true
    type: otlp
    endpoint: http://otel-collector:4317
    service_name: pilotsuite-core
```

---

## Health Checks

### Liveness Probe

```yaml
pilotsuite:
  health:
    liveness:
      enabled: true
      path: /health
      interval: 30s
      timeout: 10s
      failure_threshold: 3
```

### Readiness Probe

```yaml
pilotsuite:
  health:
    readiness:
      enabled: true
      path: /health/ready
      interval: 10s
      timeout: 5s
      failure_threshold: 3
```

### Startup Probe

```yaml
pilotsuite:
  health:
    startup:
      enabled: true
      path: /health/startup
      interval: 10s
      timeout: 5s
      failure_threshold: 30  # 5 minutes max
```

---

## Performance Tuning

### Prometheus Scrape Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'pilotsuite'
    static_configs:
      - targets: ['pilotsuite:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
```

### Grafana Alerting

Configure alerts in Grafana:
1. Go to **Alerting** → **Contact points**
2. Add Slack/Email/PagerDuty
3. Create notification policy
4. Link to dashboards

---

## Disaster Recovery

### Backup Monitoring Data

```bash
# Backup Prometheus data
docker exec prometheus tar czf - /prometheus > prometheus-backup.tar.gz

# Backup Grafana dashboards
docker exec grafana tar czf - /var/lib/grafana > grafana-backup.tar.gz
```

### Restore Monitoring

```bash
# Restore Prometheus
docker exec -i prometheus tar xzf - /prometheus < prometheus-backup.tar.gz

# Restore Grafana
docker exec -i grafana tar xzf - /var/lib/grafana < grafana-backup.tar.gz
```

---

*Last updated: 2026-04-07*
*Version: 1.0.0*
