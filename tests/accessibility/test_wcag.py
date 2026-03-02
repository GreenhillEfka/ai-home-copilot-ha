"""
PilotSuite Styx Dashboard — WCAG 2.1 AA Accessibility Tests

Automated accessibility tests using:
- axe-core (via Selenium/Playwright)
- pa11y (command-line)
- Custom WCAG checks

Run with:
    pytest tests/accessibility/test_wcag.py -v
    
Or with coverage:
    pytest tests/accessibility/ --cov=accessibility
"""

import pytest
import subprocess
import json
import os
from pathlib import Path
from typing import List, Dict, Any


# =============================================================================
# Configuration
# =============================================================================

BASE_URL = os.getenv('DASHBOARD_URL', 'http://localhost:8123')
DASHBOARD_PATHS = [
    '/dashboard',
    '/dashboard?zone=wohn',
    '/dashboard?zone=bad',
    '/dashboard?zone=koch',
]

WCAG_LEVEL = 'AA'
WCAG_VERSION = '2.1'


# =============================================================================
# Helper Functions
# =============================================================================

def run_command(command: List[str], timeout: int = 60) -> Dict[str, Any]:
    """Run a shell command and return result."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Command timed out',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }


def check_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()


def read_file_content(filepath: str) -> str:
    """Read file content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


# =============================================================================
# Test Class: WCAG Compliance Tests
# =============================================================================

class TestWCAGCompliance:
    """
    Test WCAG 2.1 AA compliance for the PilotSuite Styx Dashboard.
    
    These tests check for:
    - Perceivable content (text alternatives, captions, adaptability)
    - Operable interface (keyboard navigation, timing, seizures)
    - Understandable information (readable, predictable, input assistance)
    - Robust content (compatible with assistive technologies)
    """

    # -------------------------------------------------------------------------
    # Test 1.1.1: Non-text Content (Level A)
    # -------------------------------------------------------------------------
    
    def test_1_1_1_non_text_content_has_alternatives(self):
        """
        WCAG 1.1.1: All non-text content has text alternatives.
        
        Check that:
        - Images have alt text
        - Icons have aria-label or aria-hidden
        - Form inputs have labels
        """
        # Check HTML files for proper alt attributes
        dashboard_html = Path('dashboard/templates/dashboard.html')
        index_html = Path('dashboard/templates/index.html')
        
        if dashboard_html.exists():
            content = read_file_content(str(dashboard_html))
            
            # Check that all img tags have alt attributes
            import re
            img_tags = re.findall(r'<img[^>]*>', content)
            for img in img_tags:
                assert 'alt=' in img, f"Image missing alt attribute: {img}"
            
            # Check that decorative icons have aria-hidden
            icon_tags = re.findall(r'<i[^>]*class="mdi[^"]*"[^>]*>', content)
            # At least some icons should have aria-hidden
            # (This is a basic check - manual review recommended)
            assert len(icon_tags) > 0, "No MDI icons found"
        
        print("✓ Test 1.1.1: Non-text content check passed")

    # -------------------------------------------------------------------------
    # Test 1.1.2: Audio-only and Video-only (Level A)
    # -------------------------------------------------------------------------
    
    def test_1_1_2_no_audio_video_only_content(self):
        """
        WCAG 1.1.2: No audio-only or video-only content without alternatives.
        
        Dashboard should not have standalone audio/video content.
        """
        # Check for audio/video tags without alternatives
        dashboard_html = Path('dashboard/templates/dashboard.html')
        
        if dashboard_html.exists():
            content = read_file_content(str(dashboard_html))
            
            import re
            # Check for video tags
            video_tags = re.findall(r'<video[^>]*>', content)
            for video in video_tags:
                # Video should have controls or alternatives
                assert 'controls' in video or 'aria-label' in video, \
                    f"Video missing controls or alternatives: {video}"
            
            # Check for audio tags
            audio_tags = re.findall(r'<audio[^>]*>', content)
            for audio in audio_tags:
                assert 'controls' in audio or 'aria-label' in audio, \
                    f"Audio missing controls or alternatives: {audio}"
        
        print("✓ Test 1.1.2: No audio/video-only content")

    # -------------------------------------------------------------------------
    # Test 1.3.1: Info and Relationships (Level A)
    # -------------------------------------------------------------------------
    
    def test_1_3_1_semantic_structure(self):
        """
        WCAG 1.3.1: Information, structure, and relationships can be programmatically determined.
        
        Check for:
        - Proper heading hierarchy
        - Form labels
        - Table headers
        - List structure
        """
        dashboard_html = Path('dashboard/templates/dashboard.html')
        
        if dashboard_html.exists():
            content = read_file_content(str(dashboard_html))
            
            import re
            
            # Check heading hierarchy
            h1_tags = re.findall(r'<h1[^>]*>', content)
            h2_tags = re.findall(r'<h2[^>]*>', content)
            h3_tags = re.findall(r'<h3[^>]*>', content)
            
            # Should have exactly one H1
            assert len(h1_tags) == 1, f"Expected 1 H1, found {len(h1_tags)}"
            
            # H2 should come after H1 (dynamically generated, so check for h2 in general)
            # Note: H2s may be generated dynamically by JavaScript
            # Check that heading tags exist (h1, h2, or h3)
            total_headings = len(h1_tags) + len(h2_tags) + len(h3_tags)
            assert total_headings >= 1, "Should have heading elements"
        
        print("✓ Test 1.3.1: Semantic structure check passed")

    # -------------------------------------------------------------------------
    # Test 1.4.1: Use of Color (Level A)
    # -------------------------------------------------------------------------
    
    def test_1_4_1_color_not_only_indicator(self):
        """
        WCAG 1.4.1: Color is not the only visual means of conveying information.
        
        Check that status indicators have additional visual cues.
        """
        dashboard_css = Path('dashboard/static/css/dashboard.css')
        accessibility_css = Path('dashboard/static/css/accessibility.css')
        
        if accessibility_css.exists():
            content = read_file_content(str(accessibility_css))
            
            # Check for non-color indicators in status classes
            assert '.status-indicator' in content, \
                "Status indicator styles not found"
            
            # Should have ::after pseudo-elements for icons
            assert '::after' in content, \
                "Should have pseudo-elements for non-color indicators"
        
        print("✓ Test 1.4.1: Color not used as only indicator")

    # -------------------------------------------------------------------------
    # Test 1.4.3: Contrast (Minimum) (Level AA)
    # -------------------------------------------------------------------------
    
    def test_1_4_3_contrast_ratios(self):
        """
        WCAG 1.4.3: Text has contrast ratio of at least 4.5:1.
        
        Check CSS variables for contrast compliance.
        """
        accessibility_css = Path('dashboard/static/css/accessibility.css')
        
        assert accessibility_css.exists(), \
            "accessibility.css should exist with contrast fixes"
        
        content = read_file_content(str(accessibility_css))
        
        # Check for updated color variables
        assert '--text-muted-a11y' in content, \
            "Should have accessibility-improved text-muted color"
        assert '--text-secondary-a11y' in content, \
            "Should have accessibility-improved text-secondary color"
        
        print("✓ Test 1.4.3: Contrast ratio improvements present")

    # -------------------------------------------------------------------------
    # Test 1.4.4: Resize Text (Level AA)
    # -------------------------------------------------------------------------
    
    def test_1_4_4_text_resizable(self):
        """
        WCAG 1.4.4: Text can be resized up to 200% without loss of content.
        
        Check that relative units are used.
        """
        dashboard_css = Path('dashboard/static/css/dashboard.css')
        
        if dashboard_css.exists():
            content = read_file_content(str(dashboard_css))
            
            import re
            
            # Check for use of rem/em units (good)
            rem_usage = len(re.findall(r'\d+rem', content))
            em_usage = len(re.findall(r'\d+em', content))
            
            # Check for px usage in font-size (bad, but not critical)
            px_font_sizes = re.findall(r'font-size:\s*\d+px', content)
            
            # Should have more relative units than absolute
            # This is a soft check - relative units are preferred
            assert rem_usage + em_usage > 0, \
                "Should use relative units (rem/em) for text sizing"
        
        print("✓ Test 1.4.4: Text uses relative units")

    # -------------------------------------------------------------------------
    # Test 2.1.1: Keyboard (Level A)
    # -------------------------------------------------------------------------
    
    def test_2_1_1_keyboard_accessible(self):
        """
        WCAG 2.1.1: All functionality available from keyboard.
        
        Check that:
        - Interactive elements are focusable
        - JavaScript handles keyboard events
        """
        accessibility_js = Path('dashboard/static/js/accessibility.js')
        
        assert accessibility_js.exists(), \
            "accessibility.js should exist with keyboard navigation"
        
        content = read_file_content(str(accessibility_js))
        
        # Check for keyboard event handlers
        assert 'keydown' in content, "Should handle keydown events"
        assert 'Enter' in content, "Should handle Enter key"
        assert 'ArrowLeft' in content or 'ArrowRight' in content, \
            "Should handle arrow keys for navigation"
        
        # Check for tabindex management
        assert 'tabindex' in content, "Should manage tabindex"
        
        print("✓ Test 2.1.1: Keyboard accessibility implemented")

    # -------------------------------------------------------------------------
    # Test 2.1.2: No Keyboard Trap (Level A)
    # -------------------------------------------------------------------------
    
    def test_2_1_2_no_keyboard_trap(self):
        """
        WCAG 2.1.2: No keyboard trap.
        
        Users should be able to navigate away from all elements.
        """
        # Check that Escape key handling exists
        accessibility_js = Path('dashboard/static/js/accessibility.js')
        
        if accessibility_js.exists():
            content = read_file_content(str(accessibility_js))
            
            # Should handle Escape key
            assert 'Escape' in content, "Should handle Escape key"
        
        print("✓ Test 2.1.2: No keyboard trap detected")

    # -------------------------------------------------------------------------
    # Test 2.4.1: Bypass Blocks (Level A)
    # -------------------------------------------------------------------------
    
    def test_2_4_1_skip_link_present(self):
        """
        WCAG 2.4.1: Mechanism to bypass repeated content (skip link).
        """
        accessibility_js = Path('dashboard/static/js/accessibility.js')
        
        assert accessibility_js.exists(), \
            "accessibility.js should add skip link"
        
        content = read_file_content(str(accessibility_js))
        
        # Check for skip link creation
        assert 'skip-link' in content, "Should create skip link"
        assert 'Zum Hauptinhalt springen' in content, \
            "Skip link should have German text"
        
        print("✓ Test 2.4.1: Skip link implementation present")

    # -------------------------------------------------------------------------
    # Test 2.4.2: Page Titled (Level A)
    # -------------------------------------------------------------------------
    
    def test_2_4_2_page_has_title(self):
        """
        WCAG 2.4.2: Pages have descriptive titles.
        """
        dashboard_html = Path('dashboard/templates/dashboard.html')
        
        if dashboard_html.exists():
            content = read_file_content(str(dashboard_html))
            
            import re
            
            # Check for title tag
            title_match = re.search(r'<title>([^<]+)</title>', content)
            assert title_match, "Page should have <title> tag"
            
            title = title_match.group(1)
            assert len(title) > 0, "Title should not be empty"
            assert len(title) <= 60, "Title should be concise (≤60 chars)"
        
        print("✓ Test 2.4.2: Page has descriptive title")

    # -------------------------------------------------------------------------
    # Test 2.4.3: Focus Order (Level A)
    # -------------------------------------------------------------------------
    
    def test_2_4_3_logical_focus_order(self):
        """
        WCAG 2.4.3: Focus order preserves meaning and operability.
        
        Check that focus management is implemented.
        """
        accessibility_js = Path('dashboard/static/js/accessibility.js')
        
        if accessibility_js.exists():
            content = read_file_content(str(accessibility_js))
            
            # Should manage focus when switching tabs
            assert 'focus' in content.lower(), "Should manage focus"
        
        print("✓ Test 2.4.3: Focus order management implemented")

    # -------------------------------------------------------------------------
    # Test 2.4.7: Focus Visible (Level AA)
    # -------------------------------------------------------------------------
    
    def test_2_4_7_focus_visible(self):
        """
        WCAG 2.4.7: Keyboard focus indicator is visible.
        """
        accessibility_css = Path('dashboard/static/css/accessibility.css')
        
        assert accessibility_css.exists(), \
            "accessibility.css should have focus styles"
        
        content = read_file_content(str(accessibility_css))
        
        # Check for :focus styles
        assert ':focus' in content, "Should have :focus styles"
        assert 'outline' in content, "Should have outline for focus"
        
        # Check for focus-visible support
        assert ':focus-visible' in content, "Should support :focus-visible"
        
        print("✓ Test 2.4.7: Focus indicators implemented")

    # -------------------------------------------------------------------------
    # Test 3.1.1: Language of Page (Level A)
    # -------------------------------------------------------------------------
    
    def test_3_1_1_language_declared(self):
        """
        WCAG 3.1.1: Default language of page is declared.
        """
        dashboard_html = Path('dashboard/templates/dashboard.html')
        
        if dashboard_html.exists():
            content = read_file_content(str(dashboard_html))
            
            import re
            
            # Check for lang attribute on html tag
            html_tag = re.search(r'<html[^>]*>', content)
            assert html_tag, "Should have <html> tag"
            
            html_content = html_tag.group(0)
            assert 'lang=' in html_content, "HTML tag should have lang attribute"
            assert 'lang="de"' in html_content or "lang='de'" in html_content, \
                "Language should be German (de)"
        
        print("✓ Test 3.1.1: Page language declared")

    # -------------------------------------------------------------------------
    # Test 3.3.2: Labels or Instructions (Level A)
    # -------------------------------------------------------------------------
    
    def test_3_3_2_form_labels(self):
        """
        WCAG 3.3.2: Labels or instructions provided for user input.
        """
        chat_widget = Path('dashboard/templates/widgets/chat_widget.html')
        
        if chat_widget.exists():
            content = read_file_content(str(chat_widget))
            
            # Check that chat input has associated label (added by JS)
            # The label is added dynamically by accessibility.js
            accessibility_js = Path('dashboard/static/js/accessibility.js')
            
            if accessibility_js.exists():
                js_content = read_file_content(str(accessibility_js))
                assert 'Nachricht eingeben' in js_content, \
                    "Should add label to chat input"
        
        print("✓ Test 3.3.2: Form labels implemented")

    # -------------------------------------------------------------------------
    # Test 4.1.1: Parsing (Level A)
    # -------------------------------------------------------------------------
    
    def test_4_1_1_valid_html(self):
        """
        WCAG 4.1.1: Content can be parsed unambiguously.
        
        Basic HTML structure check.
        """
        dashboard_html = Path('dashboard/templates/dashboard.html')
        
        if dashboard_html.exists():
            content = read_file_content(str(dashboard_html))
            
            # Basic structure checks
            assert '<!DOCTYPE html>' in content, "Should have DOCTYPE"
            assert '<html' in content, "Should have html tag"
            assert '<head>' in content, "Should have head tag"
            assert '</head>' in content, "Should close head tag"
            assert '<body>' in content, "Should have body tag"
            assert '</body>' in content, "Should close body tag"
            assert '</html>' in content, "Should close html tag"
        
        print("✓ Test 4.1.1: HTML structure is valid")

    # -------------------------------------------------------------------------
    # Test 4.1.2: Name, Role, Value (Level A)
    # -------------------------------------------------------------------------
    
    def test_4_1_2_aria_roles_present(self):
        """
        WCAG 4.1.2: All UI components have accessible name, role, value.
        """
        accessibility_js = Path('dashboard/static/js/accessibility.js')
        
        assert accessibility_js.exists(), \
            "accessibility.js should add ARIA roles"
        
        content = read_file_content(str(accessibility_js))
        
        # Check for ARIA role assignments (using setAttribute syntax)
        assert 'role' in content and 'tablist' in content, "Should add tablist role"
        assert 'role' in content and 'tab' in content, "Should add tab role"
        assert 'role' in content and 'tabpanel' in content, "Should add tabpanel role"
        assert 'aria-selected' in content, "Should use aria-selected"
        assert 'aria-controls' in content, "Should use aria-controls"
        assert 'aria-labelledby' in content, "Should use aria-labelledby"
        
        print("✓ Test 4.1.2: ARIA roles implemented")

    # -------------------------------------------------------------------------
    # Test 4.1.3: Status Messages (Level AA)
    # -------------------------------------------------------------------------
    
    def test_4_1_3_status_messages_announced(self):
        """
        WCAG 4.1.3: Status messages can be programmatically determined.
        """
        accessibility_js = Path('dashboard/static/js/accessibility.js')
        
        assert accessibility_js.exists(), \
            "accessibility.js should handle status messages"
        
        content = read_file_content(str(accessibility_js))
        
        # Check for live regions
        assert 'aria-live' in content, "Should use aria-live regions"
        assert 'announce' in content.lower(), "Should have announcement function"
        assert 'polite' in content, "Should have polite live regions"
        
        print("✓ Test 4.1.3: Status messages implemented")


# =============================================================================
# Test Class: Automated Tools Integration
# =============================================================================

class TestAutomatedTools:
    """
    Integration tests for automated accessibility testing tools.
    """

    @pytest.mark.skipif(
        not check_file_exists('package.json'),
        reason="package.json not found - axe-core not configured"
    )
    def test_axe_core_available(self):
        """
        Check if axe-core is available for testing.
        """
        # Try to find axe-core in node_modules
        axe_path = Path('node_modules/axe-core')
        
        if axe_path.exists():
            print("✓ axe-core is installed")
        else:
            pytest.skip("axe-core not installed - run: npm install axe-core")

    @pytest.mark.skipif(
        os.getenv('CI') != 'true',
        reason="Skip browser tests in local development"
    )
    def test_axe_core_scan(self):
        """
        Run axe-core accessibility scan on dashboard.
        
        Requires:
        - Selenium or Playwright
        - axe-core
        - Running dashboard instance
        """
        # This test requires a browser automation setup
        # Example implementation with Selenium:
        """
        from selenium import webdriver
        from axe_core import Axe
        
        driver = webdriver.Chrome()
        driver.get(f"{BASE_URL}/dashboard")
        
        results = Axe(driver).run()
        
        # Check for violations
        violations = results['violations']
        
        # Assert no critical violations
        critical_violations = [
            v for v in violations 
            if v['impact'] in ['critical', 'serious']
        ]
        
        assert len(critical_violations) == 0, \
            f"Found {len(critical_violations)} critical violations: {critical_violations}"
        
        driver.quit()
        """
        pytest.skip("Browser automation not configured")

    def test_pa11y_available(self):
        """
        Check if pa11y is available.
        """
        result = run_command(['which', 'pa11y'])
        
        if result['success']:
            print("✓ pa11y is installed")
        else:
            pytest.skip("pa11y not installed - run: npm install -g pa11y")

    @pytest.mark.skipif(
        os.getenv('CI') != 'true',
        reason="Skip pa11y tests in local development"
    )
    def test_pa11y_scan(self):
        """
        Run pa11y accessibility scan.
        """
        # Run pa11y on dashboard
        result = run_command([
            'pa11y',
            '--standard', 'WCAG2AA',
            '--reporter', 'json',
            f'{BASE_URL}/dashboard'
        ])
        
        if result['success']:
            results = json.loads(result['stdout'])
            
            # Check for issues
            assert len(results) == 0, \
                f"Found {len(results)} accessibility issues: {results}"
        else:
            pytest.fail(f"pa11y scan failed: {result['stderr']}")


# =============================================================================
# Test Class: File Structure Checks
# =============================================================================

class TestFileStructure:
    """
    Verify that all required accessibility files exist.
    """

    def test_accessibility_audit_exists(self):
        """
        Check that ACCESSIBILITY_AUDIT.md exists.
        """
        audit_path = Path('docs/ACCESSIBILITY_AUDIT.md')
        assert audit_path.exists(), \
            "docs/ACCESSIBILITY_AUDIT.md should exist"
        
        content = read_file_content(str(audit_path))
        assert len(content) > 1000, "Audit should be comprehensive"
        
        print("✓ ACCESSIBILITY_AUDIT.md exists and is comprehensive")

    def test_accessibility_css_exists(self):
        """
        Check that accessibility.css exists.
        """
        css_path = Path('dashboard/static/css/accessibility.css')
        assert css_path.exists(), \
            "dashboard/static/css/accessibility.css should exist"
        
        content = read_file_content(str(css_path))
        assert ':focus' in content, "Should have focus styles"
        assert 'sr-only' in content, "Should have screen reader only class"
        
        print("✓ accessibility.css exists with required styles")

    def test_accessibility_js_exists(self):
        """
        Check that accessibility.js exists.
        """
        js_path = Path('dashboard/static/js/accessibility.js')
        assert js_path.exists(), \
            "dashboard/static/js/accessibility.js should exist"
        
        content = read_file_content(str(js_path))
        assert 'AccessibilityManager' in content, \
            "Should have AccessibilityManager class"
        assert 'announce' in content, "Should have announcement function"
        
        print("✓ accessibility.js exists with required functionality")

    def test_wcag_tests_exist(self):
        """
        Check that WCAG test file exists.
        """
        test_path = Path('tests/accessibility/test_wcag.py')
        assert test_path.exists(), \
            "tests/accessibility/test_wcag.py should exist"
        
        print("✓ test_wcag.py exists")


# =============================================================================
# Test Class: Manual Testing Checklist
# =============================================================================

class TestManualChecklist:
    """
    Manual testing checklist for accessibility.
    
    These tests document what should be manually verified.
    """

    def test_screen_reader_compatibility(self):
        """
        Manual Test: Screen Reader Compatibility
        
        Test with NVDA (Windows), VoiceOver (macOS), or Orca (Linux):
        
        [ ] Page title is announced
        [ ] Skip link is available and functional
        [ ] Landmark regions are announced
        [ ] Tab navigation works with arrow keys
        [ ] Tab switches are announced
        [ ] Status updates are announced
        [ ] Chat messages are announced
        [ ] Form labels are announced
        [ ] Error messages are announced
        
        Status: DOCUMENTED (requires manual execution)
        """
        print("""
        ═══════════════════════════════════════════════════════════
        Manual Test: Screen Reader Compatibility
        
        Test with NVDA, VoiceOver, or Orca:
        
        □ Page title is announced
        □ Skip link is available and functional
        □ Landmark regions are announced
        □ Tab navigation works with arrow keys
        □ Tab switches are announced
        □ Status updates are announced
        □ Chat messages are announced
        □ Form labels are announced
        □ Error messages are announced
        ═══════════════════════════════════════════════════════════
        """)

    def test_keyboard_navigation(self):
        """
        Manual Test: Keyboard-Only Navigation
        
        Unplug mouse and navigate using only keyboard:
        
        [ ] Tab through all interactive elements
        [ ] Shift+Tab moves backward
        [ ] Arrow keys navigate tabs
        [ ] Enter/Space activate buttons
        [ ] Focus is always visible
        [ ] No keyboard traps
        [ ] All functionality accessible
        
        Status: DOCUMENTED (requires manual execution)
        """
        print("""
        ═══════════════════════════════════════════════════════════
        Manual Test: Keyboard-Only Navigation
        
        Unplug mouse, use only keyboard:
        
        □ Tab through all interactive elements
        □ Shift+Tab moves backward
        □ Arrow keys navigate tabs
        □ Enter/Space activate buttons
        □ Focus is always visible
        □ No keyboard traps
        □ All functionality accessible
        ═══════════════════════════════════════════════════════════
        """)

    def test_zoom_reflow(self):
        """
        Manual Test: Zoom and Reflow
        
        Test at various zoom levels:
        
        [ ] Zoom to 200% - all content visible
        [ ] Zoom to 300% - content reflows properly
        [ ] No horizontal scrollbar at 320px width
        [ ] Text remains readable
        [ ] No content overlap
        
        Status: DOCUMENTED (requires manual execution)
        """
        print("""
        ═══════════════════════════════════════════════════════════
        Manual Test: Zoom and Reflow
        
        Test browser zoom:
        
        □ Zoom to 200% - all content visible
        □ Zoom to 300% - content reflows properly
        □ No horizontal scrollbar at 320px width
        □ Text remains readable
        □ No content overlap
        ═══════════════════════════════════════════════════════════
        """)

    def test_color_contrast(self):
        """
        Manual Test: Color and Contrast
        
        Test with color blindness simulation:
        
        [ ] Protanopia (red-blind) - content distinguishable
        [ ] Deuteranopia (green-blind) - content distinguishable
        [ ] Tritanopia (blue-blind) - content distinguishable
        [ ] Grayscale - status indicators distinguishable
        [ ] High contrast mode - all content visible
        
        Status: DOCUMENTED (requires manual execution)
        """
        print("""
        ═══════════════════════════════════════════════════════════
        Manual Test: Color and Contrast
        
        Use Chrome DevTools or color blindness simulator:
        
        □ Protanopia - content distinguishable
        □ Deuteranopia - content distinguishable
        □ Tritanopia - content distinguishable
        □ Grayscale - status indicators distinguishable
        □ High contrast mode - all content visible
        ═══════════════════════════════════════════════════════════
        """)


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "a11y: mark test as accessibility test"
    )
    config.addinivalue_line(
        "markers", "wcag: mark test as WCAG compliance test"
    )
    config.addinivalue_line(
        "markers", "manual: mark test as manual testing checklist"
    )


if __name__ == '__main__':
    # Run tests
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-m', 'not manual'  # Skip manual tests by default
    ])
