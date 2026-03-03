# Canvas Dashboard - Test Suite

## Test Environment
- **HA Version:** 2024.3+
- **Browser:** Chrome/Firefox latest
- **Canvas Files:** pilotsuite_canvas_dashboard.html, pilotsuite_functions.html

## Tests

### 1. File Deployment Tests
```bash
# Test 1.1: HTML files exist
test -f /config/www/canvas/pilotsuite_canvas_dashboard.html && echo "✅ Main dashboard exists" || echo "❌ Missing main dashboard"
test -f /config/www/canvas/pilotsuite_functions.html && echo "✅ Functions file exists" || echo "❌ Missing functions file"

# Test 1.2: File permissions
ls -la /config/www/canvas/

# Test 1.3: File sizes (verify integrity)
wc -c /config/www/canvas/pilotsuite_canvas_dashboard.html
wc -c /config/www/canvas/pilotsuite_functions.html
```

### 2. Home Assistant Integration Tests
```yaml
# Test 2.1: Resource configuration
# Expected: Dashboard loads without errors
# Steps:
# 1. Add resource: /local/canvas/pilotsuite_canvas_dashboard.html
# 2. Add iframe card with url: /local/canvas/pilotsuite_canvas_dashboard.html
# 3. Reload page
# 4. Verify dashboard renders

# Test 2.2: Lovelace YAML validation
# Expected: No syntax errors
# Check HA logs for errors after reload
```

### 3. Visual Tests
- [ ] Dashboard header displays correctly
- [ ] Mood gauges animate smoothly
- [ ] Zone cards render with proper styling
- [ ] Neuron graph displays with D3.js
- [ ] Canvas zone editor responsive
- [ ] Glass-morphism effects visible
- [ ] Dark mode colors applied correctly

### 4. Interactive Tests
- [ ] Zone editor drag & drop works
- [ ] Mood gauge updates animate smoothly
- [ ] Zone selection highlights correctly
- [ ] Export layout function works

### 5. Responsive Tests
- [ ] Mobile (375px): Dashboard adapts
- [ ] Tablet (768px): Dashboard adapts
- [ ] Desktop (1920px): Dashboard optimal

### 6. Browser Compatibility Tests
- [ ] Chrome latest
- [ ] Firefox latest
- [ ] Safari latest
- [ ] Edge latest

### 7. Performance Tests
```bash
# Test 7.1: Load time
curl -o /dev/null -s -w "Time: %{time_total}s\n" http://localhost:8123/local/canvas/pilotsuite_canvas_dashboard.html

# Test 7.2: Memory usage
# Monitor browser memory while dashboard is open
# Expected: < 500MB for full dashboard
```

### 8. WebSocket Tests
```javascript
// Test 8.1: Connection established
const ws = new WebSocket('ws://localhost:8123/api/websocket');
ws.onopen = () => console.log('WebSocket connected');
ws.onclose = () => console.log('WebSocket disconnected');

// Test 8.2: Real-time updates received
// Subscribe to state changes and verify data flows
```

## Test Results Template

| Test ID | Description | Status | Notes |
|---------|-------------|--------|-------|
| 1.1 | HTML files exist | ✅ | Pass |
| 1.2 | File permissions | ✅ | 644 for HTML files |
| 1.3 | File integrity | ✅ | Sizes match original |
| 2.1 | HA integration | ⏳ | Manual test required |
| 3.1 | Visual rendering | ⏳ | Manual test required |
| 4.1 | Interactive features | ⏳ | Manual test required |
| 5.1 | Responsive design | ⏳ | Manual test required |

## Run Tests

```bash
# Quick file test
bash <(curl -s https://raw.githubusercontent.com/.../test.sh)

# Or local
cd /config/www/canvas
bash test.sh
```

## Automation

### CI/CD Integration
```yaml
# .github/workflows/canvas-tests.yml
name: Canvas Dashboard Tests
on: [push, pull_request]
jobs:
  deploy-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test deployment
        run: |
          cp pilotsuite_canvas_dashboard.html /tmp/canvas/
          bash test.sh
```

---

**Last Updated:** 2026-03-03 21:10 GMT+1  
**Version:** 1.0.0  
**Author:** Viewona
