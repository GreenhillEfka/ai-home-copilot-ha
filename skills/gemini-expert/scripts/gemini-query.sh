#!/bin/bash
# Gemini CLI Query Wrapper
# Provides convenient access with common options

set -e

MODEL="${GEMINI_MODEL:-gemini-2.5-flash}"
FORMAT="${GEMINI_FORMAT:-text}"
TIMEOUT="${GEMINI_TIMEOUT:-60}"

usage() {
    echo "Usage: gemini-query [options] <prompt>"
    echo ""
    echo "Options:"
    echo "  -m, --model <model>      Gemini model (default: gemini-2.5-flash)"
    echo "  -f, --format <format>    Output format: text, json, stream-json"
    echo "  -i, --include <dirs>     Include directories (comma-separated)"
    echo "  -y, --yolo              Auto-approve all actions"
    echo "  -h, --help              Show this help"
    echo ""
    echo "Environment Variables:"
    echo "  GEMINI_MODEL          Default model"
    echo "  GEMINI_FORMAT         Default output format"
    echo "  GEMINI_TIMEOUT        Timeout in seconds"
    echo ""
    echo "Examples:"
    echo "  gemini-query 'Explain quantum computing'"
    echo "  gemini-query -m gemini-2.5-pro -f json 'Analyze this code'"
    echo "  cat file.py | gemini-query 'Review for bugs'"
}

INCLUDE_DIRS=""
YOLO=""
PROMPT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        -i|--include)
            INCLUDE_DIRS="--include-directories $2"
            shift 2
            ;;
        -y|--yolo)
            YOLO="--yolo"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            PROMPT="$*"
            break
            ;;
    esac
done

if [ -z "$PROMPT" ] && [ -t 0 ]; then
    usage
    exit 1
fi

# Build command
CMD="timeout $TIMEOUT gemini -m $MODEL -p \"$PROMPT\" --output-format $FORMAT $INCLUDE_DIRS $YOLO"

# Execute
if [ -t 0 ]; then
    eval $CMD
else
    # Reading from stdin
    timeout $TIMEOUT gemini -m "$MODEL" --output-format "$FORMAT" $INCLUDE_DIRS $YOLO
fi