#!/usr/bin/env python3
"""Test all OpenClaw models and report results."""

import subprocess
import time
import re

MODELS_TO_TEST = [
    ("xai/grok-code-fast-1", "--agent groky"),
    ("ollama/minimax-m2.5:cloud", "--local"),
    ("ollama/qwen3-coder-next:cloud", "--local"),
    ("ollama/glm-5:cloud", "--local"),
    ("ollama/deepseek-r1:latest", "--local"),
    ("minimax-portal/MiniMax-M2.5", "--local"),
    ("minimax-portal/MiniMax-M2.1-lightning", "--local"),
    ("opencode/minimax-m2.5-free", "--local"),
    ("opencode/kimi-k2.5-free", "--local"),
    ("openrouter/openrouter/free", "--local"),
    ("openrouter/openrouter/auto", "--local"),
    ("ollama/kimi-k2.5:cloud", "--local"),
    ("ollama/codellama:latest", "--local"),
    ("anthropic/claude-haiku-4-5", "--local"),
    ("anthropic/claude-opus-4.5", "--local"),
    ("anthropic/claude-opus-4.6", "--local"),
    ("anthropic/claude-sonnet-4-0", "--local"),
    ("anthropic/claude-sonnet-4-5", "--local"),
    ("anthropic/claude-opus-4-1", "--local"),
    ("anthropic/claude-opus-4-0", "--local"),
    ("anthropic/claude-3-5-haiku-latest", "--local"),
    ("anthropic/claude-3-7-sonnet-latest", "--local"),
    ("minimax-portal/MiniMax-M2.1", "--local"),
    ("minimax/MiniMax-M2", "--local"),
    ("minimax/MiniMax-M2.1", "--local"),
    ("minimax-cn/MiniMax-M2", "--local"),
    ("minimax-cn/MiniMax-M2.1", "--local"),
    ("openai/gpt-4", "--local"),
    ("openai/gpt-4-turbo", "--local"),
    ("openai/gpt-4.1-mini", "--local"),
    ("openai/gpt-4.1-nano", "--local"),
    ("openai/gpt-4o", "--local"),
    ("openai/gpt-5", "--local"),
    ("openai/gpt-5-chat-latest", "--local"),
    ("openai/gpt-5-mini", "--local"),
    ("openai/gpt-5-nano", "--local"),
    ("openai/gpt-5-pro", "--local"),
    ("openai/gpt-5-codex", "--local"),
    ("openai/gpt-5.1-chat-latest", "--local"),
]

def test_model(model_name, flags):
    """Test a single model with a simple prompt."""
    prompt = "Say 'ok' only"
    cmd = ["openclaw", "agent", flags, "--session-id", f"test-{model_name.replace('/', '-').replace(':', '-').replace('.', '-')}", "--message", prompt, "--thinking", "minimal", "--timeout", "60"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=65)
        output = result.stdout + result.stderr
        if result.returncode == 0 and re.search(r'\bok\b', output, re.IGNORECASE):
            return "✅ OK"
        else:
            return f"❌ FAIL (exit={result.returncode})"
    except subprocess.TimeoutExpired:
        return "❌ TIMEOUT"
    except Exception as e:
        return f"❌ ERROR: {e}"

def main():
    print("=" * 80)
    print("OPENCLAW MODEL TEST REPORT")
    print("=" * 80)
    print(f"Total models: {len(MODELS_TO_TEST)}")
    print("-" * 80)
    
    results = []
    for i, (model, flags) in enumerate(MODELS_TO_TEST, 1):
        print(f"[{i}/{len(MODELS_TO_TEST)}] Testing {model}...", end=" ")
        status = test_model(model, flags)
        print(status)
        results.append((model, status))
        time.sleep(2)  # Avoid rate limits
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for model, status in results:
        print(f"{model}: {status}")
    
    passed = sum(1 for _, s in results if "✅" in s)
    print(f"\nPassed: {passed}/{len(results)}")

if __name__ == "__main__":
    main()
