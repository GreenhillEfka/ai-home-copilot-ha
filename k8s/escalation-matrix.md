# Escalation Matrix — PilotSuite
# Version: 1.0.0
# Last Updated: 2026-04-06
# Owner: PilotSuite Operations Team

## Übersicht

Diese Eskalationsmatrix definiert die Verantwortlichkeiten und Eskalationspfade für Incidents basierend auf der Schweregrad-Klassifizierung der Prometheus-Alerts.

## Prioritätsstufen

| Priorität | Schweregrad | Beschreibung | Reaktionszeit | Lösungszeit |
|-----------|-------------|--------------|---------------|-------------|
| P1 | Critical | Service-Ausfall oder schwere Beeinträchtigung | 5 Minuten | 1 Stunde |
| P2 | Warning | Beeinträchtigung der Service-Qualität | 15 Minuten | 4 Stunden |
| P3 | Info | Potenzielle Probleme oder Warnungen | 1 Stunde | 24 Stunden |

## Eskalationsstufen

### Stufe 1: On-Call Engineer (0-15 Minuten)

**Verantwortlich:** Primary On-Call
**Kontakt:** 
- Telegram: @pilotsuite-oncall
- Phone: +49-XXX-XXX-XXX (P1 nur)

**Aufgaben:**
- Alert bestätigen und triagieren
- Erste Diagnose durchführen
- Bei P1: Sofortige Maßnahmen zur Service-Wiederherstellung
- Bei P2: Monitoring verstärken, Trends analysieren
- Bei P3: In Ticket-System dokumentieren

**Eskalationskriterien:**
- Service kann nicht innerhalb von 15 Minuten wiederhergestellt werden
- Root Cause ist unklar und erfordert Expertenwissen
- Multiple Alerts gleichzeitig (möglicher Kaskadeneffekt)

### Stufe 2: Senior Engineer (15-60 Minuten)

**Verantwortlich:** Secondary On-Call / Senior Platform Engineer
**Kontakt:**
- Telegram: @pilotsuite-senior-oncall
- Phone: +49-XXX-XXX-XXX

**Aufgaben:**
- Deep-Dive Diagnose
- Koordinierung von Gegenmaßnahmen
- Entscheidung über Change-Freeze bei Error-Budget-Risiko
- Kommunikation mit Stakeholdern bei P1

**Eskalationskriterien:**
- Incident dauert länger als 60 Minuten
- Multiple Services betroffen
- Externe Abhängigkeiten (Ollama, Telegram API) betroffen
- Datenverlust oder Korruption festgestellt

### Stufe 3: Team Lead / Architecture (60+ Minuten)

**Verantwortlich:** Platform Team Lead / System Architect
**Kontakt:**
- Telegram: @pilotsuite-lead
- Phone: +49-XXX-XXX-XXX

**Aufgaben:**
- Strategische Entscheidungen (Rollback, Failover, etc.)
- Eskalation an externe Vendor (bei Upstream-Problemen)
- Kommunikation an Management bei schweren Incidents
- Anordnung von Post-Mortem-Prozessen

### Stufe 4: Management (bei schweren P1 Incidents > 2 Stunden)

**Verantwortlich:** CTO / VP Engineering
**Kontakt:**
- Email: cto@pilotsuite.io
- Phone: +49-XXX-XXX-XXX

**Aufgaben:**
- Business-Impact Assessment
- Kommunikation an Kunden/Stakeholder
- Ressourcen-Freigabe für Incident-Response

## Alert-spezifische Eskalationspfade

### P1 Alerts (Critical)

| Alert | Primary | Secondary | Spezialisten |
|-------|---------|-----------|--------------|
| PilotSuiteServiceDown | On-Call | Senior Engineer | Platform Architect |
| PilotSuiteHighErrorRate | On-Call | Senior Engineer | Backend Lead |
| PilotSuiteHighLatency | On-Call | Senior Engineer | Performance Engineer |
| PilotSuiteSessionSpawnFailures | On-Call | Senior Engineer | Runtime Specialist |
| PilotSuiteMemoryWriteFailures | On-Call | Senior Engineer | Data Engineer |
| PilotSuiteWebSocketConnectionFailures | On-Call | Senior Engineer | Network Engineer |
| PilotSuiteOllamaAPIFailures | On-Call | Senior Engineer | AI Platform Lead |

### P2 Alerts (Warning)

| Alert | Primary | Secondary | Escalation after |
|-------|---------|-----------|------------------|
| PilotSuiteElevatedErrorRate | On-Call | Senior Engineer | 2 hours |
| PilotSuiteElevatedLatency | On-Call | Senior Engineer | 2 hours |
| PilotSuiteHighMemoryUsage | On-Call | - | 4 hours |
| PilotSuiteHighCPUUsage | On-Call | - | 4 hours |
| PilotSuitePodRestartLoop | On-Call | Senior Engineer | 1 hour |
| PilotSuiteToolExecutionTimeouts | On-Call | Senior Engineer | 2 hours |
| PilotSuiteTelegramDeliveryFailures | On-Call | Integration Specialist | 2 hours |
| PilotSuiteErrorBudgetCritical | On-Call | Team Lead | 30 minutes |

### P3 Alerts (Info)

| Alert | Primary | Escalation after | Notes |
|-------|---------|------------------|-------|
| PilotSuiteErrorBudgetWarning | On-Call | Next business day | In weekly review besprechen |
| PilotSuiteLowReplicaCount | On-Call | 4 hours | Auto-healing prüfen |
| PilotSuiteCertExpiryWarning | On-Call | Next business day | In Ticket-System eintragen |

## Kommunikationskanäle

### Telegram Channels

| Channel | Zweck | Mitglieder |
|---------|-------|------------|
| @pilotsuite-alerts | Automatischer Alert-Feed | Entire team |
| @pilotsuite-oncall | Primary On-Call | Rotation |
| @pilotsuite-senior-oncall | Secondary On-Call | Senior engineers |
| @pilotsuite-incident | Active incident coordination | All responders |
| @pilotsuite-status | Status updates for stakeholders | Management, PM |

### Telefon-Eskalation

**P1 Incidents:**
1. Primary On-Call (0-5 min)
2. Secondary On-Call (5-10 min, wenn Primary nicht erreichbar)
3. Team Lead (10-15 min, wenn Secondary nicht erreichbar)

**P2 Incidents:**
1. Primary On-Call (Telegram)
2. Secondary On-Call (nach 30 min ohne Response)

## Incident-Status-Updates

### P1 Incidents

| Zeitpunkt | Update an | Inhalt |
|-----------|-----------|--------|
| T+5 min | @pilotsuite-incident | Alert bestätigt, Diagnose läuft |
| T+15 min | @pilotsuite-incident | Erste Erkenntnisse, Gegenmaßnahmen |
| T+30 min | @pilotsuite-status | Status-Update für Stakeholder |
| T+60 min | @pilotsuite-status | Fortschritts-Update |
| Jede Stunde | @pilotsuite-status | Bis Incident resolved |

### P2 Incidents

| Zeitpunkt | Update an | Inhalt |
|-----------|-----------|--------|
| T+15 min | @pilotsuite-incident | Alert bestätigt, Diagnose läuft |
| T+60 min | @pilotsuite-incident | Fortschritts-Update |

## Post-Incident Prozesse

### P1 Incidents

**Verpflichtend:**
- Post-Mortem innerhalb von 5 Werktagen
- Root Cause Analysis (RCA) Dokument
- Action Items mit Besitzern und Deadlines
- Review im Team-Meeting

**Dokumentation:**
- Incident-Timeline (5-Minuten-Granularität)
- Betroffene Services und SLOs
- Error-Budget-Impact
- Kunden-Impact (falls zutreffend)

### P2 Incidents

**Empfohlen:**
- Kurze Analyse im Team-Channel
- Bei wiederkehrenden Alerts: Deep-Dive
- Action Items im Task-Board

### P3 Alerts

**Optional:**
- Dokumentation im Incident-Log
- Trend-Analyse im monatlichen Review

## On-Call Rotation

### Schedule

- **Rotation:** Wöchentlich (Montag 09:00 bis Montag 09:00)
- **Primary:** 1 Engineer pro Woche
- **Secondary:** 1 Senior Engineer pro Woche (Backup)

### Übergabe

- **Zeitpunkt:** Montag 09:00-09:30
- **Inhalt:**
  - Offene Alerts der letzten Woche
  - Bekannte Probleme / technische Schulden
  - Anstehende Changes (Risk Assessment)
  - Error-Budget-Status

### Kompensation

- On-Call Zulage gemäß Betriebsvereinbarung
- Zeitkompensation bei nächtlichen Incidents
- Maximal 2 On-Call-Wochen pro Monat pro Engineer

## Change Freeze bei Error-Budget-Risiko

### Automatische Trigger

| Error Budget | Maßnahme | Genehmigung |
|--------------|----------|-------------|
| > 50% | Erhöhtes Monitoring | Team Lead |
| > 75% | Change Freeze (nicht-kritisch) | Team Lead |
| > 90% | Strikter Change Freeze | CTO |
| 100% | Incident Review + Post-Mortem | CTO + Team |

### Ausnahmen vom Change Freeze

**Kritische Changes (trotz Freeze erlaubt):**
- Security-Patches
- Bugfixes für P1 Incidents
- Data-Loss-Prevention

**Genehmigung:** Team Lead + Dokumentation im Incident-Log

## Kontaktliste

| Rolle | Name | Telegram | Phone | Email |
|-------|------|----------|-------|-------|
| Primary On-Call | Rotation | @pilotsuite-oncall | +49-XXX-XXX-XXX | oncall@pilotsuite.io |
| Secondary On-Call | Rotation | @pilotsuite-senior-oncall | +49-XXX-XXX-XXX | senior-oncall@pilotsuite.io |
| Team Lead | [Name] | @pilotsuite-lead | +49-XXX-XXX-XXX | lead@pilotsuite.io |
| Platform Architect | [Name] | @pilotsuite-architect | +49-XXX-XXX-XXX | architect@pilotsuite.io |
| CTO | [Name] | @pilotsuite-cto | +49-XXX-XXX-XXX | cto@pilotsuite.io |

**Hinweis:** Diese Liste muss aktuell im Team-Wiki gepflegt werden.

## Runbook-Verzeichnis

Alle Runbooks sind unter https://runbooks.pilotsuite.io/alerts/ verfügbar:

- service-down.md
- high-error-rate.md
- high-latency.md
- session-spawn-failures.md
- memory-write-failures.md
- websocket-failures.md
- ollama-api-failures.md
- elevated-error-rate.md
- elevated-latency.md
- high-memory.md
- high-cpu.md
- pod-restart-loop.md
- tool-timeouts.md
- telegram-failures.md
- error-budget-warning.md
- error-budget-critical.md
- low-replicas.md
- cert-expiry.md

## Revision History

| Version | Datum | Autor | Änderungen |
|---------|-------|-------|------------|
| 1.0.0 | 2026-04-06 | PilotSuite Ops | Initial release |
