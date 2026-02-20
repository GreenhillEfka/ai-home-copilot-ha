---
name: claude-code-expert
description: |
  Expert Claude Code CLI agent for advanced code analysis, generation, and management.
  Provides access to Claude models for detailed coding tasks.
metadata:
  openclaw:
    emoji: "🟣"
    requires:
      bins: ["claude"]
---

# Claude Code Expert

Expert interface for Anthropic's Claude Code CLI (v2.1.41). Full headless &
interactive support. Authenticated via `claude auth login`.

## Quick Reference

```bash
# One-shot query (headless)
claude -p "Explain this function" --model sonnet

# With specific model
claude --model opus -p "Complex analysis"
claude --model sonnet -p "Quick task"

# JSON output
claude -p "Query" --output-format json

# Stream JSON (real-time)
claude -p "Query" --output-format stream-json

# Process files via stdin
cat file.py | claude -p "Review for bugs"

# Budget limit
claude -p "Analyze codebase" --max-budget-usd 0.50

# Effort level
claude --effort high -p "Deep analysis"
claude --effort low -p "Quick question"
```

## Models

| Alias    | Model                 | Best For                    |
|----------|-----------------------|-----------------------------|
| `opus`   | claude-opus-4-20240229 | Complex reasoning, deep analysis |
| `sonnet` | claude-sonnet-4-20250617 | Balanced performance        |
| `haiku`  | claude-haiku-4-20240307 | Fast, cheap tasks           |

_Note: Ensure you are logged in via `claude auth login`._

## Key Flags

| Flag               | Description                                   |
|--------------------|-----------------------------------------------|
| `-p, --print`      | Headless mode (required for scripting)        |
| `--model <alias>`  | Select model (`opus`, `sonnet`, `haiku`)      |
| `--output-format`  | `text`, `json`, `stream-json`                 |
| `--effort <level>` | `low`, `medium`, `high`                       |
| `--max-budget-usd` | Cost limit per session                        |
| `-c, --continue`   | Continue last conversation                    |
| `-r, --resume`     | Resume by session ID                          |
| `--add-dir <dirs>` | Add workspace directories                     |
| `--permission-mode`| `default`, `plan`, `acceptEdits`, `bypassPermissions` |
| `--fallback-model` | Auto-fallback when overloaded                 |
| `--json-schema`    | Structured output validation                |

## Permission Modes

- `default` - Ask for permission
- `plan` - Read-only mode
- `acceptEdits` - Auto-approve edits
- `bypassPermissions` - Skip all checks (sandbox only!)

## Commands

```bash
claude auth status          # Check authentication status
claude auth login           # Trigger login flow
claude auth logout          # Log out
claude doctor               # Check health of auto-updater
claude install [target]     # Install/update Claude Code (stable, latest, version)
claude mcp                  # Manage MCP servers
setup-token                 # Set up long-lived auth token (requires subscription)
```

## Automation Examples

### Code Generation (Palindrome Check)
```bash
claude -p "Schreibe eine Python Funktion, die prüft, ob ein Wort ein Palindrom ist. Verwende --output-format json." --model haiku
```

### Code Analysis
```bash
git diff HEAD~1 | claude --model sonnet -p "Review these changes for bugs and issues" --output-format text
```

### Structured Output Example
```bash
claude -p "List 3 bugs in this code" --model opus --output-format json --json-schema '{"inputSchema": {"type": "string"}, "outputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "line": {"type": "number"}, "issue": {"type": "string"}}}}' < code.py
```

## Update

```bash
claude update          # Check for and install updates
claude doctor          # Check health of auto-updater
```

## Authentication

- Use `claude auth login` to authenticate.
- The CLI stores tokens locally after successful login.
- `claude auth status` shows login status.
- `claude auth logout` to log out.
