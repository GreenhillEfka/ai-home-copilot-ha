---
name: gemini-expert
description: |
  Expert Gemini CLI agent for advanced operations. Use when the user wants to:
  - Run Gemini CLI queries with advanced options
  - Update/manage Gemini CLI installation
  - Use Gemini for code analysis, generation, or complex tasks
  - Coordinate multi-step Gemini workflows
  - Access Gemini models with Google Search grounding
  - Process files, codebases, or long documents with Gemini's 1M context
metadata:
  openclaw:
    emoji: "♊"
    requires:
      bins: ["gemini"]
---

# Gemini CLI Expert

Expert interface for Google's Gemini CLI with full documentation knowledge, best practices, and update management.

## Quick Reference

```bash
# Basic query
gemini -p "Your question here"

# With specific model
gemini -m gemini-2.5-flash -p "Quick question"

# JSON output (for parsing)
gemini -p "Query" --output-format json

# Process files
cat file.py | gemini -p "Explain this code"

# Multiple directories
gemini --include-directories src,docs -p "Analyze project"
```

## Key Models

| Model | Best For | Speed |
|-------|----------|-------|
| `gemini-2.5-pro` | Complex reasoning, analysis | Slower |
| `gemini-2.5-flash` | Quick tasks, high volume | Fast |
| Default | Auto-selected | Varies |

## Output Formats

- `text` (default) - Human-readable
- `json` - Structured with stats
- `stream-json` - Real-time events (JSONL)

## Common Workflows

### Code Review
```bash
git diff origin/main...HEAD | gemini -p "Review for bugs and security issues"
```

### Document Analysis
```bash
cat README.md | gemini -p "Summarize and extract key points" --include-directories docs/
```

### Generate Code
```bash
gemini -p "Create a Python function that validates email addresses"
```

### JSON Output for Automation
```bash
result=$(gemini -p "Query" --output-format json)
echo "$result" | jq -r '.response'
```

## Update Management

Run `gemini-update` script to update to latest stable version:
```bash
npm install -g @google/gemini-cli@latest
```

For preview/nightly:
```bash
npm install -g @google/gemini-cli@preview  # Weekly preview
npm install -g @google/gemini-cli@nightly  # Daily build
```

## Authentication

Gemini CLI uses OAuth by default. Already configured in `~/.gemini/`.

To re-authenticate:
```bash
gemini
# Follow browser flow
```

## Advanced Options

| Flag | Description |
|------|-------------|
| `--yolo` | Auto-approve all actions (use with caution) |
| `--approval-mode` | `default`, `auto_edit`, `yolo`, `plan` |
| `--sandbox` | Run in sandboxed environment |
| `--debug` | Enable debug mode |

## Context Files (GEMINI.md)

Place `GEMINI.md` in project root for persistent context:
```markdown
# Project Context
This is a TypeScript project using...
```

## MCP Integration

Gemini CLI supports MCP servers. Configure in `~/.gemini/settings.json`.

## Version Check

```bash
gemini --version
npm show @google/gemini-cli version  # Latest available
```

## Error Handling

- Exit code 0: Success
- Non-zero: Error occurred
- Check JSON output `error` field for details