# OpenClaw Konfiguration - Dokumentation

## Übersicht

Die `openclaw.json` ist die Hauptkonfigurationsdatei. Hier ist die Struktur erklärt:

---

## 🔧 AGENTS - Agent-Einstellungen

```json
{
  "agents": {
    "defaults": {
      // Maximale History-Teilen beim Compacting
      "compaction": {
        "maxHistoryShare": 0.35,
        "mode": "safeguard",
        "reserveTokensFloor": 16000
      },
      
      // Context-Management: Wie viel Kontext behalten?
      "contextPruning": {
        "mode": "cache-ttl",
        "ttl": "4h",
        "hardClearRatio": 0.9,
        "softTrimRatio": 0.75,
        "softTrim": {
          "maxChars": 18000,
          "headChars": 2500,
          "tailChars": 3500
        },
        "keepLastAssistants": 4,
        "hardClear": {
          "enabled": true,
          "placeholder": "[… Kontext gekürzt …]"
        }
      },
      
      // Context-Limit und Heartbeat
      "contextTokens": 16000,
      "heartbeat": { "every": "1h" },
      "maxConcurrent": 4,
      
      // Model-Priorität: Primary → Fallbacks
      "model": {
        "primary": "minimax-portal/MiniMax-M2.1",
        "fallbacks": [
          // Priority 1: API-basiert (beste Qualität)
          "openai/gpt-5.1-codex",
          "anthropic/claude-haiku-4-5",
          
          // Priority 2: Lokal (kostenlos)
          "ollama/deepseek-r1",
          "ollama/qwen3-14b"
        ]
      },
      
      // Subagent-Einstellungen
      "subagents": { "maxConcurrent": 8 },
      "thinkingDefault": "off",
      "workspace": "/config/.openclaw/workspace"
    }
  }
}
```

---

## 🔐 AUTH - Authentifizierung

```json
{
  "auth": {
    // Cooldowns bei Billing-Problemen
    "cooldowns": {
      "billingBackoffHours": 1,
      "failureWindowHours": 6,
      "billingBackoffHoursByProvider": {
        "anthropic": 2,    // Claude braucht länger
        "openai": 2,
        "openrouter": 0.5, // OpenRouter ist schneller
        "perplexity": 0.5
      }
    },
    
    // Auth-Profile pro Provider
    "profiles": {
      "anthropic:default": { "mode": "token", "provider": "anthropic" },
      "minimax-portal:default": { "mode": "oauth", "provider": "minimax-portal" },
      "openai-codex:default": { "mode": "oauth", "provider": "openai-codex" },
      "openai:default": { "mode": "api_key", "provider": "openai" },
      "openrouter:default": { "mode": "api_key", "provider": "openrouter" },
      "opencode:default": { "mode": "api_key", "provider": "opencode" }
    }
  }
}
```

---

## 📱 CHANNELS - Messenger-Integration

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "8217978632:...",  // Bot-Token
      "dmPolicy": "pairing",          // DM-Paarung erlaubt
      "groupPolicy": "open",           // Gruppen offen
      "linkPreview": true,
      "streamMode": "partial",
      "retry": { "attempts": 2 },
      "configWrites": true
    }
  }
}
```

---

## 🌐 GATEWAY - Gateway-Einstellungen

```json
{
  "gateway": {
    "mode": "local",           // Lokal oder Cloud
    "port": 18789,             // Port
    "bind": "lan",             // Bind-Interface
    "auth": {
      "mode": "token",
      "token": "..."
    },
    "http": {
      "endpoints": {
        "chatCompletions": { "enabled": true }
      }
    },
    "remote": {
      "url": "ws://127.0.0.1:18789",
      "token": "..."
    },
    "tailscale": { "mode": "off" },
    "controlUi": { "allowInsecureAuth": true }
  }
}
```

---

## 🔑 ENV - Environment-Variablen

**WICHTIG:** Diese Keys sind sensibel!

```json
{
  "env": {
    "vars": {
      "OPENAI_API_KEY": "sk-proj-...",           // OpenAI API
      "ANTHROPIC_API_KEY": "sk-ant-...",        // Anthropic API  
      "OPENROUTER_API_KEY": "sk-or-v1-...",     // OpenRouter
      "PERPLEXITY_API_KEY": "pplx-...",        // Perplexity
      "BRAVE_API_KEY": "BSAe...",              // Brave Search
      "HOMEASSISTANT_URL": "https://...",      // Home Assistant
      "HOMEASSISTANT_TOKEN": "eyJ..."          // HA Token
    }
  }
}
```

---

## 🧠 MODELS - Model-Provider

```json
{
  "models": {
    "providers": {
      // === LOCAL MODELS (Kostenlos) ===
      "ollama": {
        "api": "openai-completions",
        "apiKey": "ollama-local",
        "baseUrl": "http://127.0.0.1:11434/v1",
        "models": [
          {
            "id": "glm-5:cloud",
            "name": "GLM-5 Cloud",
            "contextWindow": 131072,
            "maxTokens": 16384,
            "reasoning": false
          },
          {
            "id": "deepseek-r1:14b",
            "name": "DeepSeek R1 14B",
            "contextWindow": 131072,
            "maxTokens": 16384,
            "reasoning": true,
            "local": true
          }
        ]
      },
      
      // === CLOUD APIs (Kostenpflichtig) ===
      "minimax-portal": {
        "api": "anthropic-messages",
        "apiKey": "minimax-oauth",
        "baseUrl": "https://api.minimax.io/anthropic",
        "models": [
          {
            "id": "MiniMax-M2.1",
            "name": "MiniMax M2.1",
            "contextWindow": 200000,
            "maxTokens": 8192,
            "reasoning": false,
            "cost": { "input": 0, "output": 0 }
          },
          {
            "id": "MiniMax-M2.1-lightning",
            "name": "MiniMax M2.1 Lightning",
            "contextWindow": 200000,
            "maxTokens": 8192,
            "reasoning": false,
            "cost": { "input": 0, "output": 0 }
          }
        ]
      },
      
      "openrouter": {
        "api": "openai-completions", 
        "apiKey": "env:OPENROUTER_API_KEY",
        "baseUrl": "https://openrouter.ai/api/v1",
        "models": [
          {
            "id": "openrouter/auto",
            "name": "OpenRouter Auto",
            "description": "Wählt automatisch das beste Modell",
            "contextWindow": 131072,
            "reasoning": false
          },
          {
            "id": "anthropic/claude-sonnet-4",
            "name": "Claude Sonnet 4",
            "contextWindow": 200000,
            "reasoning": true
          },
          {
            "id": "google/gemini-2.0-flash",
            "name": "Gemini 2.0 Flash",
            "contextWindow": 1048576,
            "reasoning": false
          }
        ]
      }
    }
  }
}
```

---

## 🛠️ TOOLS - Tool-Konfiguration

```json
{
  "tools": {
    "agentToAgent": { "enabled": true },
    "links": { "enabled": true },
    
    // === WEB SEARCH ===
    "web": {
      "search": {
        "enabled": true,
        "provider": "perplexity",
        "apiKey": "env:PERPLEXITY_API_KEY",
        "maxResults": 5,
        "timeoutSeconds": 30,
        "perplexity": {
          "baseUrl": "https://openrouter.ai/api/v1",
          "model": "perplexity/sonar-pro"
        }
      }
    },
    
    // === AUDIO / TRANSCRIPTION ===
    "media": {
      "audio": {
        "enabled": true,
        "scope": { "default": "allow" },
        "deepgram": {
          "detectLanguage": true,
          "punctuate": true,
          "smartFormat": true
        },
        "models": [
          {
            "model": "gpt-4o-mini-transcribe",
            "provider": "openai",
            "profile": "openai:default",
            "capabilities": ["audio"]
          }
        ]
      }
    },
    
    // === MESSAGING ===
    "message": {
      "allowCrossContextSend": true,
      "broadcast": { "enabled": true },
      "crossContext": { "allowWithinProvider": true }
    },
    
    "subagents": { "tools": { "allow": [] } }
  }
}
```

---

## 🔌 PLUGINS & SKILLS

```json
{
  "plugins": {
    "enabled": true,
    "entries": {
      "minimax-portal-auth": { "enabled": true },
      "telegram": { "enabled": true }
    }
  },
  
  "skills": {
    "install": { "nodeManager": "npm" },
    "entries": {
      "openai-image-gen": {
        "apiKey": "sk-proj-..."
      },
      "openai-whisper-api": {
        "apiKey": "sk-proj-...",
        "enabled": false
      }
    }
  }
}
```

---

## 📊 HOOKS & DIAGNOSTICS

```json
{
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "boot-md": { "enabled": true },       // Markdown beim Boot
        "command-logger": { "enabled": true }, // Command-Logging
        "session-memory": { "enabled": true }  // Session-Speicher
      }
    }
  },
  
  "diagnostics": {
    "enabled": true,
    "flags": ["media.*", "telegram.*"]
  },
  
  "messages": {
    "ackReactionScope": "group-mentions"
  },
  
  "update": { "checkOnStart": true }
}
```

---

## 📁 Weitere Dateien

| Datei | Zweck |
|-------|-------|
| `config/models.sh` | Model-Prioritäten & Funktionen |
| `bin/openclaw-cli` | Management CLI |
| `MEMORY.md` | Langzeit-Gedächtnis |
| `TOOLS.md` | Lokale Tools/Credentials |

---

## ✅ Model-Prioritäten (Empfohlen)

```
1. glm-5:cloud        → Beste Qualität (API)
2. deepseek-r1:14b     → Lokal, kostenlos
3. MiniMax-M2.1        → Backup Cloud
4. OpenRouter Auto     → Flexibel
5. Claude/GPT Models   → Premium Fallback
```
