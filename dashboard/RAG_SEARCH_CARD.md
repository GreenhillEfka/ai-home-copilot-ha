# RAG Search Card Configuration

## Overview

The RAG Search Card provides a full-text search interface for your knowledge base, integrating with the RAG (Retrieval-Augmented Generation) API endpoints.

## Features

- 🔍 **Search Input** with autocomplete suggestions
- 📋 **Search History** - remembers recent searches
- 🏷️ **Filters** - filter by Zone and Category
- 📊 **Results Display** - snippets with relevance scores
- 📄 **Source Documents** - shows source, timestamp, metadata

## Basic Configuration

```yaml
type: custom:ha-copilot-rag-search-card
title: Knowledge Search
placeholder: "Search documentation, runbooks, FAQs..."
```

## Full Configuration

```yaml
type: custom:ha-copilot-rag-search-card
title: Knowledge Search
placeholder: "Search documentation, runbooks, FAQs..."
max_results: 10
show_filters: true
api_endpoint: /api/rag/search

# Filter options
zones:
  - home
  - work
  - automation
  - kitchen
  - bedroom

categories:
  - documentation
  - runbook
  - faq
  - troubleshooting

# Default filters
default_zone: home
default_category: documentation
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | string | "Knowledge Search" | Card header title |
| `placeholder` | string | "Search knowledge base..." | Input placeholder text |
| `max_results` | number | 10 | Maximum number of results to display |
| `show_filters` | boolean | true | Show zone/category filters |
| `api_endpoint` | string | "/api/rag/search" | RAG API search endpoint |
| `zones` | string[] | [] | Available zones for filtering |
| `categories` | string[] | [] | Available categories for filtering |
| `default_zone` | string | - | Pre-selected zone filter |
| `default_category` | string | - | Pre-selected category filter |

## Example: Dashboard Layout

```yaml
views:
  - title: Knowledge Base
    cards:
      - type: custom:ha-copilot-rag-search-card
        title: Search Documentation
        placeholder: "Search docs, runbooks, FAQs..."
        show_filters: true
        zones:
          - home
          - work
          - automation
        categories:
          - documentation
          - runbook
          - faq
          - troubleshooting
        max_results: 15
```

## API Integration

The card expects the RAG API to return results in this format:

```json
{
  "results": [
    {
      "id": "doc_123",
      "text": "The automation triggers when motion is detected...",
      "score": 0.95,
      "rank": 1,
      "metadata": {
        "source": "documentation",
        "zone": "home",
        "title": "Motion Automation Setup",
        "timestamp": "2026-01-15T10:30:00Z"
      }
    }
  ],
  "result_count": 1,
  "took_ms": 45
}
```

## Keyboard Shortcuts

- **Enter** - Execute search
- **Escape** - Close suggestions dropdown
- **Arrow Keys** - Navigate suggestions (when shown)

## Styling

The card uses Home Assistant's built-in CSS variables:
- `--primary-color` - Main accent color
- `--secondary-color` - Secondary accent
- `--card-background-color` - Card background
- `--divider-color` - Borders and dividers
- `--primary-text-color` - Main text
- `--secondary-text-color` - Secondary text
- `--error-color` - Error states
- `--success-color` - Success indicators
