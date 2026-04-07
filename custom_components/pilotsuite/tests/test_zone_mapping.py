"""Tests for PS-178 Area-to-Zone Mapping Registry."""
from __future__ import annotations

import json
from pathlib import Path
from custom_components.copilot_ha.area_zone_registry import (
    load_area_zone_map,
    get_zone_for_area,
    get_aggregated_areas,
    get_zone_type,
    get_unmatched_fallback,
    validate_mapping,
)


def test_load_area_zone_map() -> None:
    """Test loading area zone map from config."""
    config = load_area_zone_map()
    
    assert "version" in config
    assert "unmatched_fallback" in config
    assert "mappings" in config
    assert "zone_types" in config
    assert config["unmatched_fallback"] == "ungeordnet"
    assert len(config["mappings"]) > 0


def test_get_zone_for_area() -> None:
    """Test getting zone ID for area ID."""
    config = load_area_zone_map()
    
    # Test known mapping
    zone_id = get_zone_for_area("wohnzimmer", config)
    assert zone_id == "wohnbereich"
    
    # Test unknown area
    zone_id = get_zone_for_area("unknown_area", config)
    assert zone_id is None


def test_get_aggregated_areas() -> None:
    """Test getting aggregated areas for a zone."""
    config = load_area_zone_map()
    
    areas = get_aggregated_areas("wohnbereich", config)
    assert "wohnzimmer" in areas
    assert "esszimmer" in areas


def test_get_zone_type() -> None:
    """Test getting zone type."""
    config = load_area_zone_map()
    
    zone_type = get_zone_type("wohnbereich", config)
    assert zone_type == "area"
    
    zone_type = get_zone_type("zimmer_mira", config)
    assert zone_type == "room"
    
    zone_type = get_zone_type("ungeordnet", config)
    assert zone_type == "fallback"


def test_get_unmatched_fallback() -> None:
    """Test getting unmatched fallback zone."""
    config = load_area_zone_map()
    
    fallback = get_unmatched_fallback(config)
    assert fallback == "ungeordnet"


def test_validate_mapping_valid() -> None:
    """Test validation with valid config."""
    config = load_area_zone_map()
    
    valid, errors = validate_mapping(config)
    assert valid is True
    assert len(errors) == 0


def test_validate_mapping_missing_fields() -> None:
    """Test validation with missing required fields."""
    config = {"version": 1}  # Missing required fields
    
    valid, errors = validate_mapping(config)
    assert valid is False
    assert any("unmatched_fallback" in e for e in errors)
    assert any("mappings" in e for e in errors)


def test_validate_mapping_invalid_confidence() -> None:
    """Test validation with out-of-range confidence."""
    config = {
        "version": 1,
        "unmatched_fallback": "ungeordnet",
        "mappings": [{"area_id": "test", "zone_id": "test", "confidence": 1.5}],
        "zone_types": {"test": "area"},
    }
    
    valid, errors = validate_mapping(config)
    assert valid is False
    assert any("confidence" in e for e in errors)


def test_validate_mapping_invalid_zone_type() -> None:
    """Test validation with invalid zone type."""
    config = {
        "version": 1,
        "unmatched_fallback": "ungeordnet",
        "mappings": [],
        "zone_types": {"test": "invalid_type"},
    }
    
    valid, errors = validate_mapping(config)
    assert valid is False
    assert any("invalid type" in e for e in errors)
