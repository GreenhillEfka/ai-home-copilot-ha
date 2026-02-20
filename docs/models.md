# OpenClaw - Model & Service Setup

## Overview

This setup provides multiple AI model access points for the OpenClaw agent:

```
┌─────────────────────────────────────────────────────┐
│                    OpenClaw Agent                    │
├─────────────────────────────────────────────────────┤
│  Model Selection (auto-fallback):                   │
│  1. glm-5:cloud     → Primary (Cloud API)           │
│  2. deepseek-r1:14b → Fallback (Local RAM)          │
├─────────────────────────────────────────────────────┤
│  Coding Agents:                                     │
│  • Codex CLI → OpenAI API (gpt-4o)                 │
│  • Claude Code → Anthropic API (needs credits)       │
└─────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Check status
./bin/openclaw-cli status

# Test all models
./bin/openclaw-cli test

# View configuration
./bin/openclaw-cli models
```

## Available Models

| Model | Size | Type | Use Case |
|-------|------|------|----------|
| **deepseek-r1:14b** | 9.0 GB | Local (RAM) | Primary fallback, coding, reasoning |
| **glm-5:cloud** | - | Cloud API | Best quality, research |
| **qwen3:4b** | 2.5 GB | Local (RAM) | Lightweight tasks |

## Usage

### Direct Ollama Usage

```bash
# List models
ollama list

# Run a model
ollama run deepseek-r1:14b "Hello!"

# API call
curl http://localhost:11434/api/generate \
  -d '{"model": "deepseek-r1:14b", "prompt": "Hi"}'
```

### Programmatic Usage

```bash
# Source the model config
source config/models.sh

# Get model based on API availability
MODEL=$(get_model $(check_api_available))
echo "Using: $MODEL"

# Or set manually
export DEFAULT_MODEL="deepseek-r1:14b"
```

### Coding Agents

```bash
# Codex CLI (OpenAI API)
codex exec "Write a Python function"

# Claude Code (needs Anthropic credits)
claude "Analyze this code"
```

## Service Management

### Ollama Auto-Start

Ollama is configured to start automatically via s6-overlay:

```bash
# Service location
/etc/s6-overlay/s6-rc.d/ollama/

# Check status
./bin/openclaw-cli ollama-status
```

### Manual Control

```bash
# Start
/usr/local/bin/ollama serve &

# Stop
pkill -f "ollama serve"

# Restart
pkill -f "ollama serve" && sleep 1 && /usr/local/bin/ollama serve &
```

## Model Priority Logic

```
if (glm-5:cloud API available) {
    use glm-5:cloud  // Best quality
} else {
    use deepseek-r1:14b  // Local, no cost
}
```

## Adding New Models

```bash
# Pull a new model
ollama pull <model-name>

# It will automatically appear in:
# - ollama list
# - ./bin/openclaw-cli status
```

## Troubleshooting

### Model won't load
```bash
# Check RAM availability
free -h

# Kill background processes
pkill -f ollama

# Restart Ollama
/usr/local/bin/ollama serve &
```

### API not responding
```bash
# Check internet connectivity
curl -s https://ollama.com >/dev/null && echo "Online"

# Check rate limits
# glm-5:cloud has usage limits - wait or upgrade
```

### Codex/Claude CLI not working
```bash
# Codex - needs OpenAI API key
printenv OPENAI_API_KEY | codex login --with-api-key

# Claude - needs Anthropic credits
# Visit https://console.anthropic.com/
```

## Files

```
openclaw/
├── bin/
│   └── openclaw-cli          # CLI tool for management
├── config/
│   └── models.sh              # Model configuration & functions
├── scripts/
│   └── ollama-health.sh       # Health check script
└── README.md                  # This file
```
