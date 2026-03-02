# Quick Start Guide - E2E Screenshot Tests

## 1. Install Dependencies

```bash
cd tests/e2e
npm install
npx playwright install
```

## 2. Start Dashboard

Make sure the dashboard is running:

```bash
cd dashboard
python app.py
```

Dashboard should be available at: http://localhost:8766/dashboard

## 3. Generate Baselines (First Run Only)

```bash
npm run baseline:generate
```

Or manually:

```bash
npm test
```

First run will create baselines automatically.

## 4. Run Tests

```bash
# All tests
npm test

# With browser UI
npm run test:ui

# Specific browser
npx playwright test --project=chromium

# Specific test
npx playwright test -g "Tab Navigation"
```

## 5. View Results

```bash
# HTML report
npm run test:report

# Check screenshots
ls -la screenshots/baseline/
ls -la screenshots/current/
```

## 6. CI Integration

Add to your CI pipeline:

```bash
npm run ci
```

This generates JUnit and JSON reports for CI systems.

---

**That's it!** 🎉

For more details, see [README.md](README.md).
