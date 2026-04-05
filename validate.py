#!/usr/bin/env python3
"""Validation script for HACS integration."""

import json
from pathlib import Path

def validate_manifest():
    """Validate manifest.json."""
    manifest_path = Path("custom_components/pilotsuite/manifest.json")
    if not manifest_path.exists():
        print("❌ manifest.json missing")
        return False
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    required = ["domain", "name", "version"]
    for key in required:
        if key not in manifest:
            print(f"❌ manifest.json missing '{key}'")
            return False
    
    print("✅ manifest.json valid")
    return True

def validate_structure():
    """Validate file structure."""
    required_files = [
        "custom_components/pilotsuite/__init__.py",
        "custom_components/pilotsuite/sensor.py",
        "custom_components/pilotsuite/config_flow.py",
        "custom_components/pilotsuite/manifest.json",
        "hacs.json",
        "README.md",
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Missing: {file}")
            return False
    
    print("✅ All required files present")
    return True

def main():
    print("🔍 Validating HACS integration...\n")
    
    success = True
    success &= validate_manifest()
    success &= validate_structure()
    
    print()
    if success:
        print("🚀 All validations passed!")
        return 0
    else:
        print("⚠️ Some validations failed")
        return 1

if __name__ == "__main__":
    exit(main())
