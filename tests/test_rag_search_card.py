"""Tests for RAG Search Card documentation."""

import pytest
import sys
import os
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestRAGSearchCardDocumentation:
    """Test RAG Search Card documentation."""

    def test_card_readme_exists(self):
        """Test that card README exists."""
        readme_path = PROJECT_ROOT / "dashboard" / "RAG_SEARCH_CARD.md"
        assert readme_path.exists(), "RAG_SEARCH_CARD.md should exist"

    def test_card_readme_has_basic_config(self):
        """Test that README includes basic configuration."""
        readme_path = PROJECT_ROOT / "dashboard" / "RAG_SEARCH_CARD.md"
        content = readme_path.read_text()

        assert "type: custom:ha-copilot-rag-search-card" in content, \
            "README should show basic card type"
        assert "title:" in content, \
            "README should document title option"
        assert "placeholder:" in content, \
            "README should document placeholder option"

    def test_card_readme_has_full_options(self):
        """Test that README documents all configuration options."""
        readme_path = PROJECT_ROOT / "dashboard" / "RAG_SEARCH_CARD.md"
        content = readme_path.read_text()

        required_options = [
            "max_results",
            "show_filters",
            "api_endpoint",
            "zones",
            "categories",
            "default_zone",
            "default_category"
        ]

        for option in required_options:
            assert option in content, \
                f"README should document {option} option"

    def test_card_readme_has_api_example(self):
        """Test that README includes API integration example."""
        readme_path = PROJECT_ROOT / "dashboard" / "RAG_SEARCH_CARD.md"
        content = readme_path.read_text()

        assert "results" in content.lower(), \
            "README should show API response format"
        assert "metadata" in content, \
            "README should document metadata fields"
