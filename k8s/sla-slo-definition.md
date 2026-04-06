# SLA/SLO Definition — PilotSuite
# Version: 1.0.0
# Last Updated: 2026-04-06
# Owner: PilotSuite Operations Team

## Overview
Dieses Dokument definiert die Service Level Objectives (SLOs) für alle PilotSuite-Endpoints.
Diese SLOs bilden die Basis für Monitoring-Alerts und Eskalationsprozesse.

## Service Level Indicators (SLIs)

### 1. API Gateway Endpoints

| Endpoint | Method | SLI | Target |
|----------|--------|-----|--------|
| /api/v1/agents | GET, POST | Availability | 99.9% |
| /api/v1/agents | GET, POST | Latency (p95) | < 500ms |
| /api/v1/agents/{id} | GET, PUT, DELETE | Availability | 99.9% |
| /api/v1/agents/{id} | GET, PUT, DELETE | Latency (p95) | < 300ms |
| /api/v1/sessions | GET, POST | Availability | 99.9% |
| /api/v1/sessions | GET, POST | Latency (p95) | < 400ms |
| /api/v1/sessions/{id} | GET, PUT, DELETE | Availability | 99.9% |
| /api/v1/sessions/{id} | GET, PUT, DELETE | Latency (p95) | < 300ms |
| /api/v1/tools | GET | Availability | 99.9% |
| /api/v1/tools | GET | Latency (p95) | < 200ms |
| /api/v1/tools/{id}/call | POST | Availability | 99.5% |
| /api/v1/tools/{id}/call | POST | Latency (p95) | < 5000ms |
| /api/v1/memory/search | POST | Availability | 99.9% |
| /api/v1/memory/search | POST | Latency (p95) | < 1000ms |
| /api/v1/memory/get | GET | Availability | 99.9% |
| /api/v1/memory/get | GET | Latency (p95) | < 200ms |
| /health | GET | Availability | 99.99% |
| /health | GET | Latency (p95) | < 100ms |
| /ready | GET | Availability | 99.99% |
| /ready | GET | Latency (p95) | < 100ms |
| /metrics | GET | Availability | 99.99% |
| /metrics | GET | Latency (p95) | < 200ms |

### 2. WebSocket Endpoints

| Endpoint | SLI | Target |
|----------|-----|--------|
| /ws/agent | Connection Success Rate | 99.5% |
| /ws/agent | Message Delivery Latency (p95) | < 200ms |
| /ws/agent | Reconnection Time (p95) | < 5s |

### 3. Background Processing

| Operation | SLI | Target |
|-----------|-----|--------|
| Session Spawn | Success Rate | 99.5% |
| Session Spawn | Completion Time (p95) | < 30s |
| Tool Execution | Success Rate | 99.0% |
| Tool Execution | Completion Time (p95) | < 60s |
| Memory Write | Success Rate | 99.9% |
| Memory Write | Completion Time (p95) | < 500ms |

### 4. External Integrations

| Integration | SLI | Target |
|-------------|-----|--------|
| Telegram Bot | Message Delivery Rate | 99.5% |
| Telegram Bot | Message Latency (p95) | < 2s |
| Ollama API | Request Success Rate | 99.0% |
| Ollama API | Response Time (p95) | < 30s |
| Web Search | Request Success Rate | 98.0% |
| Web Search | Response Time (p95) | < 10s |

## Service Level Objectives (SLOs)

### Availability SLOs

| Service Tier | Availability Target | Error Budget (Monthly) |
|--------------|--------------------|----------------------|
| Tier 1 (Critical) | 99.99% | 4.32 min |
| Tier 2 (Standard) | 99.9% | 43.2 min |
| Tier 3 (Best Effort) | 99.5% | 3.6 hours |

#### Tier Classification

**Tier 1 (Critical):**
- /health, /ready, /metrics
- Core agent runtime endpoints
- Session management

**Tier 2 (Standard):**
- Memory operations
- Tool execution
- WebSocket connections

**Tier 3 (Best Effort):**
- External integrations (web search, Ollama)
- Background processing
- Analytics endpoints

### Latency SLOs

| Percentile | Target | Use Case |
|------------|--------|----------|
| p50 | < 200ms | Typical user experience |
| p90 | < 500ms | Acceptable upper bound |
| p95 | < 1000ms | SLA threshold |
| p99 | < 3000ms | Extreme tail tolerance |

### Error Rate SLOs

| Error Type | Target | Measurement Window |
|------------|--------|-------------------|
| HTTP 5xx | < 0.1% | 1 hour rolling |
| HTTP 4xx (excluding 404) | < 1% | 1 hour rolling |
| Timeout Errors | < 0.5% | 1 hour rolling |
| Connection Errors | < 0.1% | 1 hour rolling |

## Error Budget Policy

### Budget Consumption

| Burn Rate | Action |
|-----------|--------|
| < 50% | Normal operations |
| 50-75% | Increase monitoring, review trends |
| 75-90% | Freeze non-critical changes, investigate |
| > 90% | Emergency review, change freeze |
| 100% | Incident review, post-mortem required |

### Budget Reset

- Monthly reset on the 1st of each month
- No carry-over of unused budget
- Budget violations trigger mandatory review

## Measurement Methodology

### Data Sources

1. **Prometheus Metrics**: Primary source for availability and latency
2. **Application Logs**: Error classification and root cause
3. **Synthetic Monitoring**: External perspective on availability
4. **Real User Monitoring**: Client-side latency measurements

### Calculation Formulas

**Availability:**
```
availability = (total_requests - error_requests) / total_requests * 100
```

**Latency (p95):**
```
p95_latency = histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Error Rate:**
```
error_rate = rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100
```

## Review Cycle

- **Weekly**: SLO compliance review in operations meeting
- **Monthly**: Error budget consumption analysis
- **Quarterly**: SLO target adjustment based on business needs
- **Annually**: Comprehensive SLA review and contract updates

## Exceptions

Temporary SLO suspensions may be granted for:
- Planned maintenance (48h notice required)
- Force majeure events
- Upstream provider outages (documented)

All exceptions must be documented in the incident management system.
