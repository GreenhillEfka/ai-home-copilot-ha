"""
Contract test: pilotsuite_dashboard_v13*.yaml button entity reference parity (HA-449).
Source-Guard for canonical pilotsuite button entity references and www paths in v13 dashboards.
Verifies button.copilot_ha_* stale refs → button.pilotsuite_* canonical.
"""
import re

V13_PATH = "custom_components/pilotsuite/dashboard/pilotsuite_dashboard_v13.yaml"
V13_3TAB_PATH = "custom_components/pilotsuite/dashboard/pilotsuite_dashboard_v13_3tab.yaml"


# ─── pilotsuite_dashboard_v13.yaml ────────────────────────────────────────────

def test_v13_validate_habitus_button_is_pilotsuite():
    """DV13B-1: validate_habitus_zones button → pilotsuite_validate_habitus_zones_v2."""
    content = open(V13_PATH, encoding="utf-8").read()
    refs = re.findall(r"entity:\s*button\.(copilot_ha_validate_habitus_zones|pilotsuite_validate_habitus_zones_v2)", content)
    assert refs, "Must have validate_habitus button reference"
    for r in refs:
        assert r == "pilotsuite_validate_habitus_zones_v2", \
            f"validate_habitus button must be pilotsuite_validate_habitus_zones_v2, got {r}"


def test_v13_ping_core_button_is_pilotsuite():
    """DV13B-2: ping_core button → pilotsuite_ping_core."""
    content = open(V13_PATH, encoding="utf-8").read()
    refs = re.findall(r"entity:\s*button\.(copilot_ha_ping_core|pilotsuite_ping_core)", content)
    assert refs, "Must have ping_core button reference"
    for r in refs:
        assert r == "pilotsuite_ping_core", \
            f"ping_core button must be pilotsuite_ping_core, got {r}"


def test_v13_fetch_core_graph_button_is_pilotsuite():
    """DV13B-3: fetch_core_graph_state button → pilotsuite_fetch_core_graph_state."""
    content = open(V13_PATH, encoding="utf-8").read()
    refs = re.findall(r"entity:\s*button\.(copilot_ha_fetch_core_graph_state|pilotsuite_fetch_core_graph_state)", content)
    assert refs, "Must have fetch_core_graph_state button reference"
    for r in refs:
        assert r == "pilotsuite_fetch_core_graph_state", \
            f"fetch_core_graph_state button must be pilotsuite_fetch_core_graph_state, got {r}"


def test_v13_brain_graph_url_is_pilotsuite():
    """DV13B-4: brain_graph_panel.html URL → /local/pilotsuite/."""
    content = open(V13_PATH, encoding="utf-8").read()
    urls = re.findall(r"url:\s*(/local/copilot_ha/brain_graph_panel\.html|/local/pilotsuite/brain_graph_panel\.html)", content)
    assert urls, "Must have brain_graph_panel URL"
    for u in urls:
        assert u == "/local/pilotsuite/brain_graph_panel.html", \
            f"brain_graph_panel URL must be /local/pilotsuite/, got {u}"


def test_v13_no_stale_copilot_ha_buttons():
    """DV13B-5: No stale button.copilot_ha_* entity references in v13."""
    content = open(V13_PATH, encoding="utf-8").read()
    stale = re.findall(r"entity:\s*button\.copilot_ha_\w+", content)
    assert not stale, f"Must not contain stale button.copilot_ha_* refs: {stale}"


def test_v13_no_stale_copilot_ha_url():
    """DV13B-6: No stale /local/copilot_ha/ URLs in v13 brain_graph."""
    content = open(V13_PATH, encoding="utf-8").read()
    stale = re.search(r"url:\s*/local/copilot_ha/brain_graph_panel\.html", content)
    assert not stale, "Must not contain stale /local/copilot_ha/ URL"


# ─── pilotsuite_dashboard_v13_3tab.yaml ───────────────────────────────────────

def test_v13_3tab_validate_habitus_button_is_pilotsuite():
    """DV13B-7: validate_habitus_zones button → pilotsuite_validate_habitus_zones_v2."""
    content = open(V13_3TAB_PATH, encoding="utf-8").read()
    refs = re.findall(r"entity:\s*button\.(copilot_ha_validate_habitus_zones|pilotsuite_validate_habitus_zones_v2)", content)
    assert refs, "Must have validate_habitus button reference"
    for r in refs:
        assert r == "pilotsuite_validate_habitus_zones_v2", \
            f"validate_habitus button must be pilotsuite_validate_habitus_zones_v2, got {r}"


def test_v13_3tab_ping_core_button_is_pilotsuite():
    """DV13B-8: ping_core button → pilotsuite_ping_core."""
    content = open(V13_3TAB_PATH, encoding="utf-8").read()
    refs = re.findall(r"entity:\s*button\.(copilot_ha_ping_core|pilotsuite_ping_core)", content)
    assert refs, "Must have ping_core button reference"
    for r in refs:
        assert r == "pilotsuite_ping_core", \
            f"ping_core button must be pilotsuite_ping_core, got {r}"


def test_v13_3tab_fetch_core_graph_button_is_pilotsuite():
    """DV13B-9: fetch_core_graph_state button → pilotsuite_fetch_core_graph_state."""
    content = open(V13_3TAB_PATH, encoding="utf-8").read()
    refs = re.findall(r"entity:\s*button\.(copilot_ha_fetch_core_graph_state|pilotsuite_fetch_core_graph_state)", content)
    assert refs, "Must have fetch_core_graph_state button reference"
    for r in refs:
        assert r == "pilotsuite_fetch_core_graph_state", \
            f"fetch_core_graph_state button must be pilotsuite_fetch_core_graph_state, got {r}"


def test_v13_3tab_enable_debug_button_is_pilotsuite():
    """DV13B-10: enable_debug_30m button → pilotsuite_enable_debug_30m."""
    content = open(V13_3TAB_PATH, encoding="utf-8").read()
    refs = re.findall(r"entity:\s*button\.(copilot_ha_enable_debug_30m|pilotsuite_enable_debug_30m)", content)
    assert refs, "Must have enable_debug_30m button reference"
    for r in refs:
        assert r == "pilotsuite_enable_debug_30m", \
            f"enable_debug_30m button must be pilotsuite_enable_debug_30m, got {r}"


def test_v13_3tab_brain_graph_url_is_pilotsuite():
    """DV13B-11: brain_graph_panel.html URL → /local/pilotsuite/."""
    content = open(V13_3TAB_PATH, encoding="utf-8").read()
    urls = re.findall(r"url:\s*(/local/copilot_ha/brain_graph_panel\.html|/local/pilotsuite/brain_graph_panel\.html)", content)
    assert urls, "Must have brain_graph_panel URL"
    for u in urls:
        assert u == "/local/pilotsuite/brain_graph_panel.html", \
            f"brain_graph_panel URL must be /local/pilotsuite/, got {u}"


def test_v13_3tab_no_stale_copilot_ha_buttons():
    """DV13B-12: No stale button.copilot_ha_* entity references in 3tab."""
    content = open(V13_3TAB_PATH, encoding="utf-8").read()
    stale = re.findall(r"entity:\s*button\.copilot_ha_\w+", content)
    assert not stale, f"Must not contain stale button.copilot_ha_* refs: {stale}"


def test_v13_3tab_no_stale_copilot_ha_url():
    """DV13B-13: No stale /local/copilot_ha/ URLs in 3tab brain_graph."""
    content = open(V13_3TAB_PATH, encoding="utf-8").read()
    stale = re.search(r"url:\s*/local/copilot_ha/brain_graph_panel\.html", content)
    assert not stale, "Must not contain stale /local/copilot_ha/ URL"
