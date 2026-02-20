#!/bin/bash
# Ollama Health Check
# Usage: ./ollama-health.sh [--fix]

set -e

OLLAMA_URL="http://localhost:11434"
MODEL="glm-5:cloud"

check_ollama_running() {
    if curl -s --max-time 5 "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
        echo "✅ Ollama läuft"
        return 0
    else
        echo "❌ Ollama läuft nicht"
        return 1
    fi
}

check_model_available() {
    if ollama list 2>/dev/null | grep -q "$MODEL"; then
        echo "✅ Modell $MODEL verfügbar"
        return 0
    else
        echo "⚠️  Modell $MODEL nicht gefunden, wird gepullt..."
        ollama pull "$MODEL" 2>&1
        return $?
    fi
}

test_model() {
    echo "Teste $MODEL..."
    result=$(curl -s --max-time 30 "$OLLAMA_URL/api/generate" \
        -d "{\"model\": \"$MODEL\", \"prompt\": \"Say: OK\", \"stream\": false}" 2>&1)
    
    if echo "$result" | grep -q '"done":true'; then
        echo "✅ $Model funktioniert"
        return 0
    else
        echo "❌ $MODEL Test fehlgeschlagen: $result"
        return 1
    fi
}

start_ollama() {
    echo "Starte Ollama..."
    # Check if running as root
    if [ "$(id -u)" = "0" ]; then
        su - ollama -c "/usr/local/bin/ollama serve" &
    else
        ollama serve &
    fi
    sleep 3
    check_ollama_running
}

# Main
echo "=== Ollama Health Check ==="
echo ""

if ! check_ollama_running; then
    if [ "$1" = "--fix" ]; then
        start_ollama
    else
        echo "💡 Tipp: --fix um Ollama zu starten"
        exit 1
    fi
fi

check_model_available
test_model

echo ""
echo "=== Alles OK ==="