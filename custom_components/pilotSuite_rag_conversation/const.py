"""Constants for the PilotSuite RAG Conversation component."""

DOMAIN = "pilotSuite_rag_conversation"

# Configuration keys
CONF_RAG_API_URL = "rag_api_url"
CONF_MODEL = "model"
CONF_USE_WEB_SEARCH = "use_web_search"
CONF_OPENAI_API_KEY = "openai_api_key"
CONF_HA_TOKEN = "ha_token"

# Defaults
DEFAULT_RAG_API_URL = "http://localhost:8765"
DEFAULT_MODEL = "gpt-4"
DEFAULT_USE_WEB_SEARCH = False

# Supported models
SUPPORTED_MODELS = [
    "gpt-4",
    "gpt-4-turbo",
    "gpt-4o",
    "gpt-3.5-turbo",
]
