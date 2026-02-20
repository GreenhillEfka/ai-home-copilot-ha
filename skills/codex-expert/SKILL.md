---
name: codex-expert
description: |
  Expert Codex CLI agent for advanced code analysis, generation, and management.
  Provides access to OpenAI Codex models for detailed coding tasks.
metadata:
  openclaw:
    emoji: "🟢"
    requires:
      bins: ["codex"]
---

# Codex CLI Expert

Expert interface for OpenAI's Codex CLI (v0.101+). Headless code generation and analysis.

## Quick Reference

```bash
# One-shot execution with schema output
codex exec "Schreibe eine Python Funktion für X" --output-schema ./response_schema.json

# Review code
codex review --help
```

## Configuration

Config: `~/.codex/config.toml`
```toml
provider = "openai"
model = "gpt-5.2-codex"
personality = "pragmatic"
model_reasoning_effort = "high"

[providers.openai]
name = "OpenAI"
base_url = "https://api.openai.com/v1"
env_key = "OPENAI_API_KEY"
```

## Key Options

| Option             | Description                                    |
|--------------------|------------------------------------------------|
| `exec`             | Execute a one-shot prompt                      |
| `review`           | Run a code review                              |
| `--model`          | Select model                                   |
| `--provider`       | Select provider                                |
| `--output-schema`  | Path to JSON Schema for structured output      |
| `--sandbox`        | Select sandbox policy (`read-only`, `workspace-write`, `danger-full-access`) |
| `--add-dir`        | Additional directories (writable)              |

## Personalities

- `pragmatic` - Balanced, practical approach
- `creative` - More exploratory solutions
- `precise` - Exact, minimal code

## Authentication

Login:
```bash
printenv OPENAI_API_KEY | codex login --with-api-key
```

Environment: `OPENAI_API_KEY` must be set.

## Trust Levels

In `~/.codex/config.toml`:
```toml
[projects."/"]
trust_level = "trusted"
```

## Update

```bash
npm install -g @openai/codex@latest
```

## Version Check

```bash
codex --version
```