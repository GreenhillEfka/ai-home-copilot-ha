# PilotSuite Core — Configuration Examples

## Production Configuration

```yaml
# configuration.yaml
pilotsuite:
  # Core settings
  debug: false
  data_dir: /config/pilotsuite
  llm_model: ollama/qwen3.5:397b-cloud
  
  # RAG Configuration
  rag:
    vector_store: faiss
    embedding_model: sentence-transformers/all-MiniLM-L6-v2
    dimension: 384
    max_cache_size: 10000
    use_approximate: true
  
  # ML Configuration
  ml:
    pattern_min_confidence: 0.6
    habit_learning_enabled: true
    max_patterns: 5000
    persistence:
      enabled: true
      path: /config/pilotsuite/patterns
      interval: 300
  
  # Presence Configuration
  presence:
    wilson_confidence: 0.95
    sensors:
      - binary_sensor.living_room_motion
      - binary_sensor.bedroom_motion
      - sensor.wifi_presence
      - binary_sensor.radar_hallway
    history_limit: 10000
  
  # Energy Configuration
  energy:
    forecasting_enabled: true
    scheduler_enabled: true
    optimizer: ortools
    horizon_hours: 24
    devices:
      - entity_id: sensor.wallbox_power
        type: ev_charger
        max_power_kw: 11.0
      - entity_id: climate.heat_pump
        type: heat_pump
        max_power_kw: 8.0
      - entity_id: sensor.battery_soc
        type: battery
        capacity_kwh: 10.0
  
  # API Configuration
  api:
    enabled: true
    host: 0.0.0.0
    port: 8080
    jwt_expiry_hours: 24
    rate_limit_requests: 100
    rate_limit_window_seconds: 60
    cors_origins:
      - https://my-home-assistant.local
  
  # Voice Configuration
  voice:
    stt:
      enabled: true
      model: whisper
      language: en
    tts:
      enabled: true
      model: piper
      voice: en_US-amy-low
    emotion_detection: true
  
  # Brain/Knowledge Graph
  brain:
    backend: networkx  # or neo4j
    neo4j_url: bolt://localhost:7687
    neo4j_user: neo4j
    neo4j_password: ${NEO4J_PASSWORD}
    persistence:
      enabled: true
      path: /config/pilotsuite/brain
```

---

## Development Configuration

```yaml
# configuration.yaml
pilotsuite:
  debug: true
  data_dir: /tmp/pilotsuite_dev
  llm_model: ollama/qwen3.5:397b-cloud
  
  # Enable all debug features
  rag:
    max_cache_size: 1000
    log_queries: true
  
  ml:
    pattern_min_confidence: 0.3  # Lower for testing
    max_patterns: 100
  
  presence:
    wilson_confidence: 0.8  # Lower threshold
    sensors:
      - binary_sensor.test_motion
  
  api:
    enabled: true
    port: 8081  # Different port
    jwt_expiry_hours: 1  # Short for testing
    rate_limit_requests: 1000  # Higher for testing
```

---

## Minimal Configuration

```yaml
# configuration.yaml
pilotsuite:
  debug: false
  data_dir: /config/pilotsuite
```

---

## High-Performance Configuration

```yaml
# configuration.yaml
pilotsuite:
  debug: false
  data_dir: /config/pilotsuite
  
  # Optimized for performance
  rag:
    vector_store: faiss
    use_approximate: true
    max_cache_size: 50000
    indexing_batch_size: 1000
  
  ml:
    pattern_detection_interval: 300  # 5 minutes
    max_patterns: 10000
  
  presence:
    history_limit: 50000
    fusion_interval: 10  # 10 seconds
  
  api:
    enabled: true
    rate_limit_requests: 500
    rate_limit_window_seconds: 60
  
  # Enable caching
  cache:
    enabled: true
    ttl_seconds: 300
    max_size: 10000
```

---

## Neo4j Production Configuration

```yaml
# configuration.yaml
pilotsuite:
  brain:
    backend: neo4j
    neo4j_url: bolt://neo4j.local:7687
    neo4j_user: neo4j
    neo4j_password: ${NEO4J_PASSWORD}
    neo4j_database: pilotsuite
    connection_pool_size: 20
    max_retry: 3
    timeout: 30
    
    persistence:
      enabled: true
      path: /config/pilotsuite/brain
      backup_enabled: true
      backup_path: /config/pilotsuite/backups/brain
      backup_interval: 86400  # Daily
```

---

## Multi-Home Configuration

```yaml
# configuration.yaml
pilotsuite:
  multi_home:
    enabled: true
    homes:
      - id: home_main
        name: Main House
        data_dir: /config/pilotsuite/main
      - id: home_vacation
        name: Vacation Home
        data_dir: /config/pilotsuite/vacation
  
  # Sync between homes
  sync:
    enabled: true
    interval: 300  # 5 minutes
    sync_patterns: true
    sync_preferences: true
```

---

## Environment Variables

Create `/config/pilotsuite.env`:

```bash
# API Keys
PILOTSUITE_API_KEY=sk_your_secure_api_key_here

# Neo4j
NEO4J_PASSWORD=secure_password

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# Encryption
PILOTSUITE_ENCRYPTION_KEY=your_32_byte_encryption_key

# Feature Flags
PILOTSUITE_FEATURE_ML=true
PILOTSUITE_FEATURE_ENERGY=true
PILOTSUITE_FEATURE_VOICE=true
```

Load in `configuration.yaml`:

```yaml
pilotsuite:
  env_file: /config/pilotsuite.env
```

---

## Docker Compose (External Services)

```yaml
# docker-compose.yml
version: '3.8'

services:
  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/secure_password
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data
    networks:
      - pilotsuite

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - pilotsuite
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - pilotsuite

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    networks:
      - pilotsuite

volumes:
  neo4j_data:
  ollama_data:
  prometheus_data:
  grafana_data:

networks:
  pilotsuite:
    driver: bridge
```

---

## Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'pilotsuite'
    static_configs:
      - targets: ['host.docker.internal:8080']
    metrics_path: '/metrics'
```

---

## Backup Configuration

```yaml
# /config/pilotsuite/backup_config.yaml
backup:
  enabled: true
  destination: /config/pilotsuite/backups
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention:
    daily: 7
    weekly: 4
    monthly: 12
  
  include:
    - patterns
    - preferences
    - vector_store
    - graph_store
    - configurations
  
  exclude:
    - cache
    - temp
    - logs
  
  compression: true
  encryption: true
  encryption_key: ${BACKUP_ENCRYPTION_KEY}
  
  remote:
    enabled: false
    type: s3
    bucket: pilotsuite-backups
    region: us-east-1
    access_key: ${AWS_ACCESS_KEY}
    secret_key: ${AWS_SECRET_KEY}
```

---

*Last updated: 2026-04-07*
*Version: 1.0.0*
