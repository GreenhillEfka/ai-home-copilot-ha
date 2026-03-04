"""Tests for RAG Search Card (rag_search_card.ts)"""

import pytest
import sys
import os
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestRAGSearchCardConfig:
    """Test RAG Search Dashboard Card configuration and structure."""

    def test_card_ts_exists(self):
        """Test that rag_search_card.ts exists."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        assert card_path.exists(), "rag_search_card.ts should exist"

    def test_card_ts_is_valid_typescript(self):
        """Test that card TS file is valid TypeScript."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        # Check for basic TypeScript/LitElement structure
        assert "import { LitElement, html, css, nothing } from 'lit'" in content, \
            "Card should import LitElement"
        assert "import { customElement, property, state } from 'lit/decorators.js'" in content, \
            "Card should import decorators"
        assert "@customElement('ha-copilot-rag-search-card')" in content, \
            "Card should define custom element"

    def test_card_has_required_interfaces(self):
        """Test that card has required TypeScript interfaces."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        # Check for interfaces
        assert "export interface RAGSearchResult" in content, \
            "Card should export RAGSearchResult interface"
        assert "export interface RAGSearchConfig" in content, \
            "Card should export RAGSearchConfig interface"

    def test_card_has_required_properties(self):
        """Test that card has required properties."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        required_properties = [
            "hass",
            "config",
            "query",
            "results",
            "loading",
            "error"
        ]

        for prop in required_properties:
            assert f"private {prop}" in content or f"public {prop}" in content, \
                f"Card should have {prop} property"

    def test_card_has_required_methods(self):
        """Test that card has required methods."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        required_methods = [
            "setConfig",
            "getStubConfig",
            "_handleInput",
            "_performSearch",
            "_handleZoneChange",
            "_handleCategoryChange",
            "_highlightMatch",
            "_getSourceIcon"
        ]

        for method in required_methods:
            # Check for method (can be private, public, or public static)
            assert method in content, \
                f"Card should have {method} method"

    def test_card_has_autocomplete_functionality(self):
        """Test that card includes autocomplete/suggestions."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        assert "suggestions" in content.lower(), \
            "Card should have suggestions functionality"
        assert "_updateSuggestions" in content, \
            "Card should have _updateSuggestions method"
        assert "suggestions-dropdown" in content, \
            "Card should render suggestions dropdown"

    def test_card_has_filter_functionality(self):
        """Test that card includes zone/category filters."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        assert "_handleZoneChange" in content, \
            "Card should have zone filter handler"
        assert "_handleCategoryChange" in content, \
            "Card should have category filter handler"
        assert "selectedZone" in content, \
            "Card should track selected zone"
        assert "selectedCategory" in content, \
            "Card should track selected category"

    def test_card_has_search_history(self):
        """Test that card includes search history."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        assert "searchHistory" in content, \
            "Card should track search history"
        assert "_loadHistory" in content, \
            "Card should have history loading method"
        assert "_saveHistory" in content, \
            "Card should have history saving method"
        assert "localStorage" in content, \
            "Card should use localStorage for history"

    def test_card_has_results_display(self):
        """Test that card includes results display."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        assert "results-container" in content, \
            "Card should have results container"
        assert "result-item" in content, \
            "Card should render result items"
        assert "result-score" in content, \
            "Card should display relevance scores"
        assert "result-rank" in content, \
            "Card should display result rank"

    def test_card_has_api_integration(self):
        """Test that card integrates with RAG API."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        assert "fetch(" in content, \
            "Card should use fetch for API calls"
        assert "/api/rag/search" in content or "api_endpoint" in content, \
            "Card should reference RAG search endpoint"
        assert "POST" in content, \
            "Card should use POST method for search"

    def test_card_has_error_handling(self):
        """Test that card includes error handling."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        assert "error-message" in content, \
            "Card should display error messages"
        assert "try" in content and "catch" in content, \
            "Card should have try-catch blocks"
        assert "_performSearch" in content, \
            "Card should handle search errors"

    def test_card_has_keyboard_navigation(self):
        """Test that card supports keyboard navigation."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        assert "_handleKeyDown" in content, \
            "Card should handle keyboard events"
        assert "Enter" in content, \
            "Card should handle Enter key"
        assert "Escape" in content, \
            "Card should handle Escape key"

    def test_card_has_text_highlighting(self):
        """Test that card includes text highlighting for matches."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        assert "_highlightMatch" in content, \
            "Card should highlight search matches"
        assert "<mark>" in content or "mark" in content.lower(), \
            "Card should use mark element for highlighting"

    def test_card_exports_element(self):
        """Test that card properly exports custom element."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        assert "declare global" in content, \
            "Card should declare global element"
        assert "HTMLElementTagNameMap" in content, \
            "Card should use HTMLElementTagNameMap"
        assert "ha-copilot-rag-search-card" in content, \
            "Card should register correct element name"

    def test_card_has_stub_config(self):
        """Test that card provides stub config for HA."""
        card_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "rag_search_card.ts"
        content = card_path.read_text()

        assert "getStubConfig" in content, \
            "Card should have getStubConfig method"
        assert "HomeAssistant" in content, \
            "Card should use HomeAssistant type"


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


class TestRAGSearchCardIndex:
    """Test that card is properly exported in index."""

    def test_card_exported_from_index(self):
        """Test that card is exported from index.ts."""
        index_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "index.ts"
        content = index_path.read_text()

        assert "rag_search_card" in content.lower(), \
            "index.ts should reference rag_search_card"
        assert "HaCopilotRAGSearchCard" in content, \
            "index.ts should export HaCopilotRAGSearchCard"

    def test_card_registered_in_global_map(self):
        """Test that card is registered in global HTMLElementTagNameMap."""
        index_path = PROJECT_ROOT / "src" / "visualizations" / "lovelace_cards" / "index.ts"
        content = index_path.read_text()

        assert "ha-copilot-rag-search-card" in content, \
            "Card should be registered in global map"
