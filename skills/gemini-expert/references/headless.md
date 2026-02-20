# Gemini CLI Headless Mode

## Basic Usage

### Direct Prompt
```bash
gemini -p "What is machine learning?"
```

### From Stdin
```bash
echo "Explain this code" | gemini
cat file.py | gemini -p "Review for bugs"
```

### With Options
```bash
gemini -m gemini-2.5-pro -p "Complex analysis" --output-format json
gemini --include-directories src,docs -p "Analyze project"
```

## Output Formats

### Text (Default)
```bash
gemini -p "Query"
# Returns plain text response
```

### JSON
```bash
gemini -p "Query" --output-format json
```

Response structure:
```json
{
  "response": "The answer",
  "stats": {
    "models": { "gemini-2.5-flash": { "tokens": {...}, "api": {...} } },
    "tools": { "totalCalls": 0, "byName": {} }
  }
}
```

### Stream JSON (JSONL)
```bash
gemini -p "Query" --output-format stream-json
```

Event types: `init`, `message`, `tool_use`, `tool_result`, `error`, `result`

## Command-Line Options

| Flag | Description |
|------|-------------|
| `-p, --prompt` | Run in headless mode |
| `-m, --model` | Specify model |
| `-o, --output-format` | `text`, `json`, `stream-json` |
| `-i, --include-directories` | Additional directories |
| `-y, --yolo` | Auto-approve all actions |
| `--approval-mode` | `default`, `auto_edit`, `yolo`, `plan` |
| `-d, --debug` | Enable debug mode |
| `-s, --sandbox` | Run in sandbox |
| `--raw-output` | Allow ANSI sequences |

## Automation Examples

### Commit Messages
```bash
git diff --cached | gemini -p "Write a commit message"
```

### Code Review
```bash
git diff origin/main...HEAD | gemini -p "Review for issues" --output-format json | jq -r '.response'
```

### Log Analysis
```bash
grep ERROR /var/log/app.log | tail -20 | gemini -p "Analyze errors and suggest fixes"
```

### Batch Analysis
```bash
for file in src/*.py; do
    cat "$file" | gemini -p "Find bugs" > "reports/$(basename $file).analysis"
done
```

### Token Tracking
```bash
result=$(gemini -p "Query" --output-format json)
tokens=$(echo "$result" | jq -r '.stats.models | to_entries | map(.value.tokens.total) | add')
echo "Tokens used: $tokens"
```