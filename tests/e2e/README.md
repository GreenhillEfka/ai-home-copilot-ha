# PilotSuite Styx - E2E Screenshot Tests

Playwright-based end-to-end tests with visual regression testing for the Dashboard UI.

## Features

✅ **Screenshot every dashboard tab** (10 zones)  
✅ **Visual comparison with baseline** (pixel-diff <2%)  
✅ **Multiple viewports** (Mobile, Tablet, Desktop)  
✅ **Dark mode + Light mode** screenshots  
✅ **CI integration** (screenshots as artifacts)  

## Test Suite Coverage

- ✅ Tab-Navigation funktioniert
- ✅ Zone-Cards laden korrekt
- ✅ Widgets zeigen echte Daten
- ✅ Alerts werden angezeigt
- ✅ Theme-Toggle funktioniert

## Installation

```bash
cd tests/e2e
npm install
npx playwright install
```

## Running Tests

### Run all tests
```bash
npm test
```

### Run with UI mode
```bash
npm run test:ui
```

### Run in headed mode (see browser)
```bash
npm run test:headed
```

### Debug tests
```bash
npm run test:debug
```

### Run specific test file
```bash
npx playwright test dashboard_screenshots.spec.ts
```

### Run specific test by name
```bash
npx playwright test -g "Tab Navigation"
```

### Run on specific browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

## Generating Baselines

First run will automatically generate baselines. To regenerate:

```bash
# Delete existing baselines
rm -rf screenshots/baseline/*

# Run tests to create new baselines
npm test
```

Or manually save screenshots as baselines:

```bash
node visual-compare.js path/to/screenshot.png baseline-name
```

## Visual Comparison

The `visual-compare.js` utility compares screenshots with baselines:

```bash
# Compare two images
node visual-compare.js baseline/image.png current/image.png 2

# Compare screenshot with baseline (2% tolerance)
node visual-compare.js dashboard-desktop-light
```

## Directory Structure

```
tests/e2e/
├── fixtures.ts              # Test fixtures (Page Object, helpers)
├── dashboard_screenshots.spec.ts  # Main test suite
├── visual-compare.js        # Pixel-diff comparison utility
├── playwright.config.ts     # Playwright configuration
├── package.json             # Dependencies
├── README.md                # This file
└── screenshots/
    ├── baseline/            # Baseline images (commit to git)
    ├── current/             # Current test run images
    └── diff/                # Generated diff images
```

## CI Integration

### GitHub Actions Example

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: |
          cd tests/e2e
          npm install
          npx playwright install --with-deps
      
      - name: Start Dashboard
        run: |
          cd dashboard
          python app.py &
          sleep 5
      
      - name: Run E2E Tests
        run: |
          cd tests/e2e
          npm run ci
      
      - name: Upload Test Results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: tests/e2e/playwright-report/
      
      - name: Upload Screenshots
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: screenshots
          path: tests/e2e/screenshots/
```

### Jenkins Example

```groovy
pipeline {
    agent any
    
    stages {
        stage('E2E Tests') {
            steps {
                sh 'cd tests/e2e && npm install'
                sh 'cd tests/e2e && npx playwright install --with-deps'
                sh 'cd dashboard && python app.py &'
                sleep 5
                sh 'cd tests/e2e && npm run ci'
            }
            post {
                always {
                    junit 'tests/e2e/junit-results.xml'
                    archiveArtifacts artifacts: 'tests/e2e/screenshots/**/*', fingerprint: true
                    archiveArtifacts artifacts: 'tests/e2e/playwright-report/**/*', fingerprint: true
                }
            }
        }
    }
}
```

## Configuration

### Environment Variables

- `DASHBOARD_URL` - Dashboard URL (default: `http://localhost:8766`)
- `CI` - Set to `true` for CI mode (retries, single worker)

### Tolerance Settings

Default visual regression tolerance: **2%**

Adjust in tests:
```typescript
const result = await compareScreenshot('image-name', 1.5); // 1.5% tolerance
```

## Troubleshooting

### Tests fail on first run
This is expected - baselines need to be generated. Run tests once to create baselines.

### Dimension mismatch errors
Ensure viewport size is consistent between baseline and current screenshots.

### Too many false positives
Increase tolerance percentage or update baselines after intentional UI changes.

### Connection refused
Make sure the dashboard is running on the configured URL before tests.

## Best Practices

1. **Commit baselines** - Add `screenshots/baseline/` to version control
2. **Update baselines on UI changes** - When intentionally changing UI, regenerate baselines
3. **Run locally first** - Test changes locally before CI
4. **Use descriptive names** - Screenshot names should indicate viewport, theme, and zone
5. **Review diff images** - When tests fail, check diff images in `screenshots/diff/`

## License

Part of PilotSuite Styx Core
