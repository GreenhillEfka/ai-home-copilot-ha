#!/bin/bash
# OpenClaw Model Configuration
# Defines model priorities and fallbacks
# Remote Ollama Server (set your LAN IP below)

# Set remote Ollama host (for glm-5:cloud and local models)
export OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

# Priority order for agent usage
# 1. Primary (Remote Ollama)
# 2. Fallback (MiniMax Cloud API)

export PRIMARY_MODEL="glm-5:cloud"           # Remote Ollama
export FALLBACK_MODEL="minimax-portal/MiniMax-M2.1"  # MiniMax Cloud API

# CLI tools (fallbacks when APIs fail)
export CLI_CLAUDE="claude"              # Claude Code CLI (Anthropic)
export CLI_GEMINI="gemini"               # Gemini CLI (Google)
export CLI_CODEX="codex"                 # Codex CLI (OpenAI)

# Coding agent configurations
export CODEX_MODEL="gpt-4o"            # Codex CLI uses OpenAI API
export CLAUDE_MODEL=""                   # Needs Anthropic credits

# Model selection function
get_model() {
    local api_available="$1"  # "true" or "false"
    
    if [ "$api_available" = "true" ] && [ -n "$PRIMARY_MODEL" ]; then
        echo "$PRIMARY_MODEL"
    elif [ -n "$FALLBACK_MODEL" ]; then
        echo "$FALLBACK_MODEL"
    else
        echo "$LOCAL_FALLBACK"
    fi
}

# Check if API is available
check_api_available() {
    # Check glm-5:cloud availability (ping remote server)
    curl -s --max-time 5 "${OLLAMA_HOST}/api/tags" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Display current configuration
show_config() {
    echo "=== OpenClaw Model Configuration ==="
    echo ""
    echo "Server:          $OLLAMA_HOST"
    echo ""
    echo "Model Priority:"
    echo "  1. $PRIMARY_MODEL (Remote Ollama - Primary)"
    echo "  2. $FALLBACK_MODEL (MiniMax API - Fallback)"
    echo ""
    echo "Available Models:"
    curl -s "${OLLAMA_HOST}/api/tags" 2>/dev/null | grep -o '"name":"[^"]*"' | sed 's/"name":"//;s/"//g' | head -10 || echo "  (checking...)"
    echo ""
    echo "API Status:"
    if [ "$(check_api_available)" = "true" ]; then
        echo "  🌐 Remote Ollama: Online"
    else
        echo "  🌐 Remote Ollama: Offline (using MiniMax)"
    fi
    echo ""
    echo "Usage:"
    echo "  source this file: source $0"
    echo "  get model: \$(get_model \$api_status)"
}

# Quick test all models
test_all() {
    echo "Testing available models..."
    echo "Server: $OLLAMA_HOST"
    echo ""
    
    echo "1. glm-5:cloud (Primary - Remote Ollama):"
    curl -s --max-time 30 "${OLLAMA_HOST}/api/generate" \
        -d '{"model": "glm-5:cloud", "prompt": "1+1=", "stream": false}' \
        | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','N/A')[:100])" 2>/dev/null || echo "Failed"
    
    echo ""
    echo "2. MiniMax (Fallback - Cloud API):"
    echo "  (Nutzt default_model aus OpenClaw Runtime)"
    
    echo ""
    echo "3. Remote Server Status:"
    curl -s "${OLLAMA_HOST}/api/tags" 2>/dev/null | grep -o '"name":"[^"]*"' | sed 's/"name":"//;s/"//g' | head -5 || echo "  Cannot connect"
}

# Check if CLI tools are available
check_gemini() {
    if which gemini >/dev/null 2>&1; then
        echo "true"
    else
        echo "false"
    fi
}

# If script is run directly (not sourced)
if [ "$0" = "${BASH_SOURCE[0]}" ]; then
    show_config
    echo ""
    echo "Run 'test_all' to test model availability."
fi
