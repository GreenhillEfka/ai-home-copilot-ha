#!/bin/bash
# pplx.sh - Perplexity Search CLI
# Usage: pplx "query" | pplx-deep "query" | pplx-reasoning "query"

set -e

API_KEY="${PERPLEXITY_API_KEY:-$(printenv PERPLEXITY_API_KEY 2>/dev/null)}"
API_URL="https://api.perplexity.ai/chat/completions"

# Model selection
case "$(basename "$0")" in
    pplx-deep|pplx.sh)
        MODEL="${PERPLEXITY_MODEL:-sonar-pro}"
        ;;
    pplx-reasoning)
        MODEL="sonar-reasoning-pro"
        ;;
    pplx|*)
        MODEL="sonar"
        ;;
esac

# Allow override via first arg
if [[ "$1" == "--model" ]]; then
    MODEL="$2"
    shift 2
fi

if [[ -z "$API_KEY" ]]; then
    echo "Error: PERPLEXITY_API_KEY not set" >&2
    exit 1
fi

if [[ -z "$1" ]]; then
    echo "Usage: pplx \"query\" [--lang de|en]" >&2
    echo "       pplx-deep \"query\" (sonar-pro)" >&2
    echo "       pplx-reasoning \"query\" (deep reasoning)" >&2
    exit 1
fi

QUERY="$1"
LANG="${2:-de}"

# Build prompt with language
if [[ "$LANG" == "de" ]]; then
    SYSTEM="Antworte auf Deutsch. Sei prägnant und faktisch."
else
    SYSTEM="Be concise and factual."
fi

# Call Perplexity API
RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"$MODEL\",
        \"messages\": [
            {\"role\": \"system\", \"content\": \"$SYSTEM\"},
            {\"role\": \"user\", \"content\": $(echo "$QUERY" | jq -Rs .)}
        ]
    }" 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [[ "$HTTP_CODE" != "200" ]]; then
    echo "Perplexity API error (HTTP $HTTP_CODE): $BODY" >&2
    # Fallback hint
    echo "Tip: Use 'web_search' tool as fallback" >&2
    exit 1
fi

# Extract and output content
echo "$BODY" | jq -r '.choices[0].message.content // empty'

# Show citations if available
CITATIONS=$(echo "$BODY" | jq -r '.citations // empty')
if [[ -n "$CITATIONS" && "$CITATIONS" != "null" ]]; then
    echo ""
    echo "---"
    echo "Quellen:"
    echo "$CITATIONS" | jq -r '.[] | "- \(.)"' 2>/dev/null || true
fi