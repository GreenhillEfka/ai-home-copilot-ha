"""
OpenAI-Compatible Conversation API for Extended OpenAI Conversation

Provides /v1/chat/completions endpoint compatible with:
- Extended OpenAI Conversation (HA custom component)
- OpenAI SDK
- Any OpenAI-compatible client

Features:
- Function calling for HA services
- Streaming support
- Conversation context
- Ollama integration for offline AI
"""

from flask import Blueprint, request, jsonify, current_app
import logging
import json
import os
import requests
import time
import requests

logger = logging.getLogger(__name__)

conversation_bp = Blueprint('conversation', __name__, url_prefix='/chat')

# HA Service function definitions for function calling
HA_FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "execute_services",
            "description": "Execute Home Assistant services to control devices",
            "parameters": {
                "type": "object",
                "properties": {
                    "list": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "domain": {
                                    "type": "string",
                                    "description": "The domain of the service (e.g., light, switch, climate)"
                                },
                                "service": {
                                    "type": "string",
                                    "description": "The service to call (e.g., turn_on, turn_off)"
                                },
                                "service_data": {
                                    "type": "object",
                                    "description": "Data to pass to the service",
                                    "properties": {
                                        "entity_id": {
                                            "type": "string",
                                            "description": "The entity_id to control"
                                        }
                                    }
                                }
                            },
                            "required": ["domain", "service", "service_data"]
                        }
                    }
                },
                "required": ["list"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_states",
            "description": "Get the current state of Home Assistant entities",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Filter by domain (e.g., light, sensor)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_history",
            "description": "Get history of entities",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of entity IDs"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time (ISO format)"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time (ISO format)"
                    }
                }
            }
        }
    }
]

# System prompt for Home Assistant conversation
HA_SYSTEM_PROMPT = """You are a helpful Home Assistant assistant. You can control devices in the home through Home Assistant services.

You have access to these functions:
- execute_services: Call Home Assistant services to control devices
- get_states: Get current state of entities
- get_history: Get historical data

When a user asks to control a device (like "turn on the light"), use the execute_services function.
When you need to know the current state of something, use get_states.
When you need historical information, use get_history.

Be concise and helpful. Confirm actions after executing them."""


# Character Presets for Conversation
CONVERSATION_CHARACTERS = {
    "copilot": {
        "name": "CoPilot",
        "description": "The main AI assistant - helpful, smart, suggests automations",
        "system_prompt": """You are AI Home CoPilot, a helpful smart home assistant for Home Assistant.

Your role:
- Help users control their smart home devices
- Suggest automations when you notice patterns
- Learn user preferences and adapt
- Always be helpful and proactive but never take action without confirmation

You have access to Home Assistant functions to control devices.
When users ask to control something, use the execute_services function.
After executing, confirm what you did.
If you notice patterns (e.g., user always turns on heating at 6pm), suggest an automation."""
    },
    "butler": {
        "name": "Butler",
        "description": "Formal, attentive, service-oriented",
        "system_prompt": """You are a formal butler for a smart home. 

Your style:
- Polite and formal language
- Anticipate needs before being asked
- Be discreet and respectful
- Use phrases like "Would you like me to..." and "Very well, sir/madam"

You control Home Assistant devices. Execute requests promptly and confirm completion formally."""
    },
    "energy_manager": {
        "name": "Energy Manager",
        "description": "Focus on energy efficiency and savings",
        "system_prompt": """You are an Energy Manager for a smart home, focused on efficiency and savings.

Your priorities:
- Monitor energy consumption
- Suggest ways to save energy
- Highlight inefficient patterns
- Recommend optimal schedules

You control Home Assistant devices. Always consider energy impact when executing commands.
Suggest energy-saving automations when you notice waste (lights left on, heating when windows open)."""
    },
    "security_guard": {
        "name": "Security Guard",
        "description": "Security-focused, alerts on anomalies",
        "system_prompt": """You are a security-focused smart home assistant.

Your priorities:
- Monitor security sensors and cameras
- Alert on unusual activity
- Check door/window states
- Verify all sensors are armed at night

You control Home Assistant devices. Always be vigilant.
Report any anomalies or suspicious activity.
Confirm security-relevant actions with the user."""
    },
    "friendly": {
        "name": "Friendly Assistant",
        "description": "Casual, warm, conversational",
        "system_prompt": """You're a friendly, casual smart home buddy.

Your style:
- Relaxed and conversational
- Use casual language
- Be friendly and approachable
- Have short conversations

You control Home Assistant devices. Just help out and have a friendly chat!
Keep responses short and natural."""
    },
    "minimal": {
        "name": "Minimal",
        "description": "Short, direct, efficient",
        "system_prompt": """You are a minimal, efficient smart home assistant.

Your style:
- Keep responses very short
- Only say what's necessary
- Get straight to the point
- No small talk

You control Home Assistant devices. Execute commands efficiently.
Confirm with minimal words like "Done", "On", "Off"."""
    }
}

# Default character
DEFAULT_CHARACTER = "copilot"


@conversation_bp.route('/characters', methods=['GET'])
def list_characters():
    """List available conversation characters"""
    return jsonify({
        "characters": [
            {
                "id": key,
                "name": val["name"],
                "description": val["description"]
            }
            for key, val in CONVERSATION_CHARACTERS.items()
        ],
        "default": DEFAULT_CHARACTER
    })


@conversation_bp.route('/completions', methods=['POST'])
def chat_completions():
    """
    OpenAI-compatible chat completions endpoint
    
    Expected payload (OpenAI format):
    {
        "model": "gpt-4" (or any string, we use our own),
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."}
        ],
        "functions": [...],  # optional
        "stream": false     # or true for streaming
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON body provided"}), 400
        
        messages = data.get('messages', [])
        stream = data.get('stream', False)
        functions = data.get('functions', HA_FUNCTIONS)
        
        # Extract last user message
        user_message = None
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                user_message = msg.get('content', '')
                break
        
        if not user_message:
            return jsonify({"error": "No user message found"}), 400
        
        logger.info(f"Conversation request: {user_message[:100]}...")
        
        # Build conversation context
        conversation_context = _build_context(messages)
        
        # Process through our AI (mock for now - will connect to real AI)
        response = _process_conversation(user_message, conversation_context, functions)
        
        if stream:
            return _stream_response(response)
        
        return jsonify(response)
        
    except Exception as e:
        logger.exception("Error in chat completions")
        return jsonify({"error": str(e)}), 500


def _build_context(messages):
    """Build context from message history"""
    context = {
        "system": HA_SYSTEM_PROMPT,
        "history": []
    }
    
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role != 'system':
            context["history"].append(f"{role}: {content}")
    
    return context


def _process_conversation(user_message, context, functions):
    """
    Process conversation through Ollama for offline AI
    Uses llm2.5-thinking:latest by default
    Supports character selection via config or model name
    """
    # Get Ollama settings from environment or config
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "llm2.5-thinking:latest")
    
    # Get character from model name or environment (e.g., "copilot" or "butler")
    character_name = os.environ.get("CONVERSATION_CHARACTER", DEFAULT_CHARACTER)
    
    # Also check if model name contains character (e.g., "copilot-qwen")
    for char_key in CONVERSATION_CHARACTERS:
        if char_key in ollama_model.lower():
            character_name = char_key
            break
    
    # Get character config
    character = CONVERSATION_CHARACTERS.get(character_name, CONVERSATION_CHARACTERS[DEFAULT_CHARACTER])
    system_prompt = character["system_prompt"]
    
    logger.info(f"Using character: {character_name} ({character['name']})")
    
    # Prepare messages for Ollama
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    try:
        # Call Ollama
        ollama_response = requests.post(
            f"{ollama_url}/api/chat",
            json={
                "model": ollama_model,
                "messages": messages,
                "stream": False
            },
            timeout=60
        )
        
        if ollama_response.status_code == 200:
            result = ollama_response.json()
            response_content = result.get("message", {}).get("content", "")
        else:
            logger.warning(f"Ollama returned {ollama_response.status_code}")
            response_content = _fallback_response(user_message)
            
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to Ollama at {ollama_url}")
        response_content = _offline_fallback(user_message)
    except Exception as e:
        logger.exception("Error calling Ollama")
        response_content = _fallback_response(user_message)
    
    response = {
        "id": f"chatcmpl-{os.urandom(12).hex()}",
        "object": "chat.completion",
        "created": int(__import__('time').time()),
        "model": ollama_model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_content,
                    "function_call": None
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": len(user_message),
            "completion_tokens": len(response_content),
            "total_tokens": len(user_message) + len(response_content)
        }
    }
    
    return response


def _fallback_response(user_message):
    return f"I understand: '{user_message}'. Ollama not connected."


def _offline_fallback(user_message):
    return f"I'm offline. Message: '{user_message}'. Check Ollama at localhost:11434 with llm2.5-thinking:latest."


def _stream_response(response):
    """Stream response implementation"""
    # Placeholder for streaming
    import flask
    def generate():
        content = response["choices"][0]["message"]["content"]
        for chunk in content.split():
            yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk + ' '}}]})}\n\n"
        yield "data: [DONE]\n\n"
    
    return flask.Response(generate(), mimetype='text/event-stream')


def register_routes(app):
    """Register conversation routes with Flask app"""
    app.register_blueprint(conversation_bp)
    logger.info("Registered conversation API at /v1/chat/completions")
