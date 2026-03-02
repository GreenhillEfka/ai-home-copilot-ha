# Accessibility Testing Guide

This directory contains automated and manual accessibility tests for the PilotSuite Styx Dashboard.

## Overview

The tests verify WCAG 2.1 AA compliance through:
- **Automated tests** (`test_wcag.py`) - Programmatic checks
- **Manual testing checklists** - Human verification
- **Tool integration** - axe-core, pa11y, Lighthouse

## Quick Start

### Run Automated Tests

```bash
# Navigate to project root
cd /config/.openclaw/workspace/pilotsuite-styx-core

# Run all accessibility tests
pytest tests/accessibility/test_wcag.py -v

# Run specific test class
pytest tests/accessibility/test_wcag.py::TestWCAGCompliance -v

# Run only automated tests (skip manual checklists)
pytest tests/accessibility/ -v -m "not manual"
```

### Install Testing Tools

```bash
# Install axe-core for browser testing
npm install --save-dev axe-core @axe-core/playwright

# Install pa11y for CLI testing
npm install --save-dev pa11y pa11y-ci

# Install Lighthouse for performance + accessibility
npm install -g lighthouse @lhci/cli
```

## Test Structure

```
tests/accessibility/
├── test_wcag.py           # Main test suite
├── README.md              # This file
└── (future: axe scans, reports, etc.)
```

## Test Categories

### 1. WCAG Compliance Tests (`TestWCAGCompliance`)

Automated checks for specific WCAG success criteria:

| Test ID | WCAG Criterion | Level | Description |
|---------|----------------|-------|-------------|
| `test_1_1_1` | 1.1.1 Non-text Content | A | Alt text, icon labels |
| `test_1_1_2` | 1.1.2 Audio-only/Video-only | A | No standalone media |
| `test_1_3_1` | 1.3.1 Info and Relationships | A | Semantic structure |
| `test_1_4_1` | 1.4.1 Use of Color | A | Non-color indicators |
| `test_1_4_3` | 1.4.3 Contrast (Minimum) | AA | 4.5:1 contrast ratio |
| `test_1_4_4` | 1.4.4 Resize Text | AA | 200% zoom support |
| `test_2_1_1` | 2.1.1 Keyboard | A | Keyboard accessibility |
| `test_2_1_2` | 2.1.2 No Keyboard Trap | A | No focus traps |
| `test_2_4_1` | 2.4.1 Bypass Blocks | A | Skip link |
| `test_2_4_2` | 2.4.2 Page Titled | A | Descriptive title |
| `test_2_4_3` | 2.4.3 Focus Order | A | Logical focus |
| `test_2_4_7` | 2.4.7 Focus Visible | AA | Visible focus indicator |
| `test_3_1_1` | 3.1.1 Language of Page | A | Language declaration |
| `test_3_3_2` | 3.3.2 Labels or Instructions | A | Form labels |
| `test_4_1_1` | 4.1.1 Parsing | A | Valid HTML |
| `test_4_1_2` | 4.1.2 Name, Role, Value | A | ARIA roles |
| `test_4_1_3` | 4.1.3 Status Messages | AA | Live regions |

### 2. Automated Tools Integration (`TestAutomatedTools`)

Integration with industry-standard tools:

- **axe-core**: Browser-based accessibility engine
- **pa11y**: Command-line accessibility tester
- **Lighthouse**: Performance + accessibility audits

### 3. File Structure Checks (`TestFileStructure`)

Verify required files exist:

- `docs/ACCESSIBILITY_AUDIT.md` - Full audit report
- `dashboard/static/css/accessibility.css` - A11Y styles
- `dashboard/static/js/accessibility.js` - A11Y scripts

### 4. Manual Testing Checklist (`TestManualChecklist`)

Documented manual tests for:

- Screen reader compatibility
- Keyboard-only navigation
- Zoom and reflow
- Color and contrast

## Manual Testing Procedures

### Screen Reader Testing

**Tools:**
- NVDA (Windows, free): https://www.nvaccess.org/
- VoiceOver (macOS/iOS, built-in): Enable with Cmd+F5
- Orca (Linux, free): `sudo apt install orca`

**Test Scenarios:**

1. **Page Load**
   - Open dashboard
   - Verify page title is announced
   - Verify skip link is announced

2. **Navigation**
   - Press Tab to reach tab navigation
   - Use Arrow Left/Right to switch tabs
   - Verify each tab switch is announced

3. **Content**
   - Navigate through zone cards
   - Verify card titles are announced
   - Verify status updates are announced

4. **Chat Widget**
   - Navigate to chat input
   - Verify label is announced
   - Send a message
   - Verify new message is announced

### Keyboard Testing

**Procedure:**

1. Unplug mouse (or disable trackpad)
2. Open dashboard
3. Press Tab to navigate forward
4. Press Shift+Tab to navigate backward
5. Verify:
   - All interactive elements are reachable
   - Focus is always visible
   - No keyboard traps
   - Enter/Space activate buttons
   - Arrow keys work in tab navigation

### Zoom Testing

**Procedure:**

1. Open dashboard in Chrome/Firefox
2. Press Ctrl++ (or Cmd++) to zoom in
3. Test at 200%, 300%, 400%
4. Verify:
   - All content is visible
   - No horizontal scrollbar
   - Text remains readable
   - No content overlap

### Color Contrast Testing

**Tools:**
- Chrome DevTools → Rendering → Emulate vision deficiencies
- Colour Contrast Analyser: https://www.tpgi.com/color-contrast-checker/

**Procedure:**

1. Open Chrome DevTools (F12)
2. Go to Rendering tab
3. Enable "Emulate vision deficiencies"
4. Test each type (protanopia, deuteranopia, tritanopia)
5. Verify all information is still accessible

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Accessibility Tests

on: [push, pull_request]

jobs:
  a11y:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install pytest
        npm install axe-core
    
    - name: Run accessibility tests
      run: |
        pytest tests/accessibility/test_wcag.py -v --tb=short
    
    - name: Run pa11y CI
      run: |
        npx pa11y-ci
```

### GitLab CI Example

```yaml
accessibility:
  image: python:3.11
  stage: test
  
  before_script:
    - pip install pytest
    - npm install axe-core pa11y-ci
  
  script:
    - pytest tests/accessibility/test_wcag.py -v
    - npx pa11y-ci
```

## Fixing Common Issues

### Missing Focus Indicators

**Problem:** Focus outline not visible

**Solution:** Add to `accessibility.css`:
```css
*:focus {
  outline: 3px solid #2563eb;
  outline-offset: 2px;
}
```

### Missing Alt Text

**Problem:** Images without alt attributes

**Solution:** Add alt text to images:
```html
<img src="logo.png" alt="PilotSuite Styx Logo">
```

### Missing ARIA Labels

**Problem:** Icon buttons without accessible names

**Solution:** Add aria-label:
```html
<button aria-label="Einstellungen öffnen">
  <i class="mdi mdi-cog"></i>
</button>
```

### Low Contrast

**Problem:** Text hard to read

**Solution:** Update colors in CSS:
```css
/* Before */
--text-muted: #94a3b8;  /* 3.2:1 */

/* After */
--text-muted: #71717a;  /* 4.6:1 */
```

## Resources

### Guidelines
- [WCAG 2.1 AA Checklist](https://www.w3.org/WAI/WCAG21/quickref/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)

### Tools
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [WAVE](https://wave.webaim.org/)
- [Lighthouse](https://developer.chrome.com/docs/lighthouse/overview/)
- [Colour Contrast Analyser](https://www.tpgi.com/color-contrast-checker/)

### Testing
- [Screen Reader Testing Guide](https://www.w3.org/WAI/test-evaluate/tools/screen-readers/)
- [Keyboard Testing](https://www.w3.org/WAI/test-evaluate/preliminary/#keyboard)

## Reporting Issues

When reporting accessibility issues, include:

1. **WCAG Criterion** (e.g., 1.4.3 Contrast)
2. **Severity** (Critical, Serious, Moderate, Minor)
3. **Steps to Reproduce**
4. **Expected Behavior**
5. **Actual Behavior**
6. **Screen Reader/Browser** (if applicable)
7. **Screenshot** (if helpful)

## Maintenance

- **Monthly**: Run full accessibility audit
- **Per PR**: Run automated tests on dashboard changes
- **Quarterly**: Manual screen reader testing
- **Annually**: Full WCAG 2.1 AA recertification

## Contact

For accessibility questions or issues, contact the development team.

---

**Last Updated:** 2026-03-02  
**WCAG Version:** 2.1 AA  
**Next Review:** 2026-04-02
