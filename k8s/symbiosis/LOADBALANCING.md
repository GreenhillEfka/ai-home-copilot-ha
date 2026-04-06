# Load Balancing für Symbiosis

## Übersicht

Diese Konfiguration implementiert Load Balancing für die Symbiosis-Anwendung mit:
- Nginx Ingress Controller
- Traffic Splitting (Canary Deployments)
- Session Affinity (Cookie-basiert)

## Komponenten

### 1. Haupt-Ingress (`ingress.yaml`)

- **Host:** `symbiosis.pilotsuite.local`
- **Backend Service:** `symbiosis` (Production)
- **Session Affinity:** Cookie-basiert (`SYMBIOSIS_SESSION`)
- **Session Duration:** 48 Stunden (172800 Sekunden)
- **Load Balancing:** Hash-basiert auf Client-IP (`$binary_remote_addr`)

### 2. Canary-Ingress (`canary-ingress.yaml`)

- **Traffic Weight:** 20% (konfigurierbar via `canary-weight`)
- **Header-basiertes Routing:** `X-Canary-Test: true`
- **Cookie-basiertes Routing:** `canary_test` Cookie
- **Backend Service:** `symbiosis-canary`

### 3. Session Affinity

Session Affinity wird auf zwei Ebenen sichergestellt:

1. **Ingress-Level:** Cookie-basierte Affinität
   - `nginx.ingress.kubernetes.io/affinity: "cookie"`
   - `nginx.ingress.kubernetes.io/session-cookie-name: "SYMBIOSIS_SESSION"`

2. **Service-Level:** Source-IP-Hashing
   - `nginx.ingress.kubernetes.io/upstream-hash-by: "$binary_remote_addr"`

## Traffic Splitting Strategien

### Gewicht-basiert (Weight-based)
```yaml
nginx.ingress.kubernetes.io/canary-weight: "20"  # 20% Traffic
```

### Header-basiert
```yaml
nginx.ingress.kubernetes.io/canary-by-header: "X-Canary-Test"
nginx.ingress.kubernetes.io/canary-by-header-value: "true"
```

### Cookie-basiert
```yaml
nginx.ingress.kubernetes.io/canary-by-cookie: "canary_test"
```

## Deployment

### Production Deployment
```bash
kubectl apply -k /config/clawd/k8s/symbiosis/
```

### Canary Deployment aktivieren
1. Canary-Resources sind bereits in Kustomization enthalten
2. Traffic-Anteil über `canary-weight` Annotation steuern
3. Canary-Deployment mit neuer Version deployen

### Rollback
```bash
# Canary-Weight auf 0 setzen
kubectl annotate ingress symbiosis-canary nginx.ingress.kubernetes.io/canary-weight="0"

# Oder Canary-Deployment entfernen
kubectl delete -k /config/clawd/k8s/symbiosis/canary-deployment.yaml
```

## Monitoring

- **Prometheus Metrics:** Verfügbar unter `/metrics` (Port 8080)
- **ServiceMonitor:** Konfiguriert für automatische Discovery
- **Health Checks:** `/health` (Liveness), `/ready` (Readiness)

## Konfiguration anpassen

### Traffic-Anteil ändern
Editiere `canary-ingress.yaml`:
```yaml
nginx.ingress.kubernetes.io/canary-weight: "10"  # 10% Traffic
```

### Session-Dauer ändern
```yaml
nginx.ingress.kubernetes.io/session-cookie-expires: "86400"  # 24 Stunden
nginx.ingress.kubernetes.io/session-cookie-max-age: "86400"
```

### Host ändern
```yaml
spec:
  rules:
  - host: symbiosis.example.com  # Neuer Host
```

## Sicherheit

- **SSL Redirect:** Aktiviert (`ssl-redirect: "true"`)
- **TLS Secret:** `symbiosis-tls-secret` muss erstellt werden
- **Request Limits:** 50MB Body-Size
- **Timeouts:** 60 Sekunden Read/Send

## Troubleshooting

### Session Affinity funktioniert nicht
- Cookie-Name prüfen: `SYMBIOSIS_SESSION`
- Browser-Cookies löschen und neu testen
- Ingress Controller Logs prüfen: `kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx`

### Canary Traffic wird nicht verteilt
- Canary-Annotationen prüfen
- Ingress Controller Version (≥ 0.21.0 erforderlich)
- `kubectl describe ingress symbiosis-canary` für Status

### TLS Fehler
- Secret erstellen: `kubectl create secret tls symbiosis-tls-secret --cert=path/to/tls.crt --key=path/to/tls.key`
