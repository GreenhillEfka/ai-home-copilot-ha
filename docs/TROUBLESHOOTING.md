# Troubleshooting Guide

## Common Issues and Solutions

---

## Installation Issues

### HACS Installation Fails

**Symptom:** Download fails or hangs

**Causes:**
- Network connectivity issues
- GitHub rate limiting
- Insufficient disk space

**Solutions:**

1. **Check disk space:**
```bash
df -h /config
```

2. **Retry installation:**
```bash
# In HACS, click "Retry" button
```

3. **Manual installation as fallback:**
```bash
cd /config/custom_components
git clone https://github.com/GreenhillEfka/pilotsuite-styx-ha.git pilotsuite
```

---

### Integration Not Appearing

**Symptom:** PilotSuite Core not in integrations list after install

**Solutions:**

1. **Clear browser cache:**
   - Chrome: Ctrl+Shift+Delete
   - Firefox: Ctrl+Shift+Delete
   - Hard refresh: Ctrl+Shift+R

2. **Check if integration loaded:**
```bash
# SSH into Home Assistant
grep -r "pilotsuite" /config/custom_components/
```

3. **Restart Home Assistant:**
   - Settings → System → Restart

4. **Check logs:**
   - Settings → System → Logs
   - Search for "pilotsuite"

---

## Runtime Issues

### High Memory Usage

**Symptom:** Memory usage >2GB

**Causes:**
- Large vector store cache
- Too many patterns tracked
- RAG embedding cache unbounded

**Solutions:**

```yaml
pilotsuite:
  rag:
    max_cache_size: 5000  # Limit embeddings
  ml:
    max_patterns: 1000    # Limit patterns
  presence:
    history_limit: 1000   # Limit history
```

---

### Slow Response Times

**Symptom:** API responses >5 seconds

**Causes:**
- Vector similarity search on large dataset
- Complex graph queries
- LLM inference latency

**Solutions:**

1. **Optimize vector search:**
```yaml
pilotsuite:
  rag:
    max_results: 10       # Limit search results
    use_approximate: true # Use approximate nearest neighbor
```

2. **Use faster LLM:**
```yaml
pilotsuite:
  llm:
    model: qwen3.5:397b-cloud  # Faster than larger models
```

3. **Enable caching:**
```yaml
pilotsuite:
  cache:
    enabled: true
    ttl_seconds: 300
```

---

### API Server Won't Start

**Symptom:** Port 8080 errors

**Causes:**
- Port already in use
- Permission issues
- Firewall blocking

**Solutions:**

1. **Check port usage:**
```bash
netstat -tlnp | grep 8080
```

2. **Change port:**
```yaml
pilotsuite:
  api:
    port: 8081
    host: 0.0.0.0
```

3. **Check firewall:**
```bash
# Allow port
sudo ufw allow 8081/tcp
```

---

## Feature-Specific Issues

### Presence Detection Not Working

**Symptom:** Presence always shows "away"

**Causes:**
- Sensors not configured
- Sensor data not flowing
- Wilson score threshold too high

**Solutions:**

1. **Verify sensors:**
```yaml
pilotsuite:
  presence:
    sensors:
      - binary_sensor.living_room_motion
      - binary_sensor.bedroom_motion
```

2. **Check sensor states:**
   - Developer Tools → States
   - Search for sensor entities

3. **Adjust Wilson threshold:**
```yaml
pilotsuite:
  presence:
    wilson_confidence: 0.8  # Lower from 0.95
```

---

### Energy Optimization Not Running

**Symptom:** No optimization schedules created

**Causes:**
- OR-Tools not installed
- Device configuration missing
- Forecast data unavailable

**Solutions:**

1. **Install OR-Tools:**
```bash
pip install ortools>=9.8.0
```

2. **Configure devices:**
```yaml
pilotsuite:
  energy:
    devices:
      - entity_id: sensor.wallbox_power
        type: ev_charger
```

3. **Check forecast:**
   - Ensure weather/price data available

---

### Voice Pipeline Fails

**Symptom:** STT/TTS not working

**Causes:**
- Whisper/Piper not installed
- Audio device not configured
- Model files missing

**Solutions:**

1. **Install Whisper:**
```bash
pip install openai-whisper
```

2. **Install Piper:**
```bash
pip install piper-tts
```

3. **Configure audio:**
```yaml
pilotsuite:
  voice:
    stt:
      model: whisper
      language: en
    tts:
      model: piper
      voice: en_US-amy-low
```

---

### Knowledge Graph Errors

**Symptom:** Graph queries fail

**Causes:**
- Neo4j not running
- NetworkX fallback too slow
- Graph store corrupted

**Solutions:**

1. **Start Neo4j:**
```bash
docker start neo4j
```

2. **Use NetworkX fallback:**
```yaml
pilotsuite:
  brain:
    backend: networkx  # Instead of neo4j
```

3. **Rebuild graph:**
```yaml
# In configuration.yaml
pilotsuite:
  brain:
    rebuild_on_start: true
```

---

## Performance Issues

### Slow Startup

**Symptom:** Home Assistant takes >60 seconds to start

**Causes:**
- Large vector store loading
- Graph store initialization
- Too many patterns

**Solutions:**

```yaml
pilotsuite:
  lazy_load: true       # Load modules on demand
  preload: false        # Don't preload data
  startup_timeout: 120  # Increase timeout
```

---

### High CPU Usage

**Symptom:** CPU >80% continuously

**Causes:**
- Pattern detection running constantly
- Vector indexing in background
- LLM inference loops

**Solutions:**

```yaml
pilotsuite:
  ml:
    pattern_detection_interval: 300  # Run every 5 min
  rag:
    indexing_batch_size: 100         # Smaller batches
  llm:
    max_concurrent: 1                # Single inference
```

---

## Security Issues

### API Authentication Fails

**Symptom:** 401 Unauthorized errors

**Causes:**
- Invalid API key
- Token expired
- JWT secret mismatch

**Solutions:**

1. **Generate new API key:**
```bash
curl -X POST http://localhost:8080/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "new_key_12345", "scope": "read"}'
```

2. **Check token expiry:**
```yaml
pilotsuite:
  api:
    jwt_expiry_hours: 48  # Increase from 24
```

---

### Rate Limiting Too Aggressive

**Symptom:** 429 Too Many Requests

**Causes:**
- Rate limit too low for workload
- Multiple clients sharing IP

**Solutions:**

```yaml
pilotsuite:
  api:
    rate_limit_requests: 200      # Increase from 100
    rate_limit_window_seconds: 120  # Increase window
```

---

## Data Issues

### Vector Store Corruption

**Symptom:** Similarity search returns wrong results

**Causes:**
- Disk write errors
- Version mismatch
- Index corruption

**Solutions:**

1. **Rebuild index:**
```yaml
pilotsuite:
  rag:
    rebuild_index: true
```

2. **Clear cache:**
```bash
rm -rf /config/pilotsuite/vector_cache/*
```

---

### Pattern Data Loss

**Symptom:** Learned patterns disappear after restart

**Causes:**
- Persistence not enabled
- Storage path incorrect
- Permission issues

**Solutions:**

```yaml
pilotsuite:
  ml:
    persistence:
      enabled: true
      path: /config/pilotsuite/patterns
      interval: 300  # Save every 5 min
```

---

## Getting Help

### Logs

**Location:**
- Home Assistant: Settings → System → Logs
- File: `/config/home-assistant.log`

**Search terms:**
- `pilotsuite`
- `copilot_core`
- `ERROR`
- `WARNING`

### Support Channels

1. **GitHub Issues:** https://github.com/GreenhillEfka/pilotsuite-styx-ha/issues
2. **Discussions:** https://github.com/GreenhillEfka/pilotsuite-styx-ha/discussions
3. **Documentation:** https://github.com/GreenhillEfka/pilotsuite-styx-ha/docs

### Information to Include

When reporting issues:

- Home Assistant version
- PilotSuite Core version
- Configuration (redact secrets)
- Error messages (full text)
- Steps to reproduce
- Expected vs actual behavior

---

## Emergency Recovery

### Complete Reset

If all else fails:

```bash
# Stop Home Assistant
# Remove PilotSuite data
rm -rf /config/pilotsuite
rm -rf /config/custom_components/pilotsuite

# Reinstall
# Follow installation guide from scratch
```

### Rollback to Previous Version

```bash
cd /config/custom_components/pilotsuite
git checkout <previous_version_tag>
```

---

*Last updated: 2026-04-07*
*Version: 1.0.0-rc2*
