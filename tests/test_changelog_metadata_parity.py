"""Contract test: CHANGELOG top heading matches manifest.json and README."""
import re
import pathlib
import json
import pytest


def test_changelog_top_heading_matches_manifest_and_readme():
    """CL1: CHANGELOG top heading must match manifest.json version and README version."""
    ha_dir = pathlib.Path("custom_components/pilotsuite")
    manifest_ver = json.loads((ha_dir / "manifest.json").read_text(encoding="utf-8"))["version"]

    changelog_content = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    top_match = re.search(r"^## \[([^\]]+)\]", changelog_content, re.MULTILINE)
    changelog_ver = top_match.group(1) if top_match else "NONE"

    readme_content = pathlib.Path("README.md").read_text(encoding="utf-8")
    readme_match = re.search(r"^\*\*Version:\*\*\s+([\d.]+)", readme_content, re.MULTILINE)
    readme_ver = readme_match.group(1) if readme_match else "NONE"

    assert manifest_ver == changelog_ver == readme_ver, (
        f"Metadata drift: manifest={manifest_ver}, changelog={changelog_ver}, readme={readme_ver}"
    )