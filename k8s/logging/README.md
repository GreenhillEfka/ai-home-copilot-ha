# PilotSuite Log Aggregation Stack

Komplette Log-Aggregation-Lösung für Kubernetes basierend auf Fluentd, Elasticsearch und Kibana (EFK-Stack).

## Komponenten

### 1. Fluentd (Log Collection)
- **DaemonSet**: Sammelt Logs von allen Nodes
- **ConfigMap**: Fluentd-Konfiguration für Container- und System-Logs
- **Features**:
  - Automatische Kubernetes-Metadata-Anreicherung
  - Filterung von Fluentd-eigenen Logs
  - Buffer für zuverlässige Zustellung
  - Unterstützung für alle Pod-Logs

### 2. Elasticsearch (Log Storage)
- **StatefulSet**: 3-Node-Cluster für Hochverfügbarkeit
- **Index Templates**: Automatische Index-Erstellung mit optimierten Mappings
- **ILM Policy**: Lifecycle-Management (Hot → Warm → Cold → Delete)
  - Hot: 7 Tage, Rollover bei 50GB
  - Warm: 30 Tage, Shrink auf 1 Shard
  - Cold: 90 Tage, Frozen
  - Delete: Nach 90 Tagen

### 3. Kibana (Log Visualization)
- **Deployment**: Web-UI für Log-Analyse
- **Dashboards**:
  - Pod Log Volume (Timeseries)
  - Namespace Log Distribution (Pie Chart)
  - Error Rate Timeseries mit Threshold
  - Log Level Breakdown
  - Top Error Containers
  - Volltextsuche-Tabelle

## Installation

```bash
# Namespace erstellen
kubectl create namespace logging

# Logging-Stack deployen
kubectl apply -k /config/clawd/k8s/logging

# Setup-Script ausführen (importiert Dashboards)
kubectl run kibana-setup --rm -it --image=curlimages/curl \
  --namespace=logging \
  -- bash /usr/share/kibana/config/dashboards/setup-script.sh
```

## Zugriff

```bash
# Port-Forward für Kibana
kubectl port-forward svc/kibana 5601:5601 -n logging

# Kibana im Browser öffnen
# http://localhost:5601
```

## Konfiguration anpassen

### Fluentd Config
Datei: `fluentd-configmap.yaml`
- Log-Pfade anpassen
- Elasticsearch-Host ändern
- Buffer-Einstellungen optimieren

### Elasticsearch Ressourcen
Datei: `elasticsearch-statefulset.yaml`
- Replica-Anzahl (empfohlen: 3)
- JVM-Heap-Größe (ES_JAVA_OPTS)
- Storage-Größe in volumeClaimTemplates

### ILM Policy
Datei: `elasticsearch-index-templates.yaml`
- Aufbewahrungsdauer anpassen
- Rollover-Bedingungen ändern

## Monitoring

```bash
# Fluentd Status
kubectl get daemonset fluentd -n logging

# Elasticsearch Cluster Health
kubectl port-forward svc/elasticsearch 9200:9200 -n logging
curl http://localhost:9200/_cluster/health

# Kibana Status
kubectl get deployment kibana -n logging
```

## Troubleshooting

### Fluentd sammelt keine Logs
```bash
kubectl logs daemonset/fluentd -n logging
kubectl describe daemonset fluentd -n logging
```

### Elasticsearch Cluster ist rot/gelb
```bash
curl http://localhost:9200/_cluster/health?pretty
curl http://localhost:9200/_cat/shards?v
```

### Dashboards nicht sichtbar
Setup-Script erneut ausführen oder manuell über Kibana UI importieren.

## Sicherheitshinweise

- Aktuell ohne Authentication (für Entwicklung/Test)
- Für Production: X-Pack Security aktivieren
- Network Policies für logging-Namespace erwägen
- TLS für Elasticsearch-Kommunikation konfigurieren
