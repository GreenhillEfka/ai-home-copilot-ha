"""
MCP-style Tool Server for PilotSuite Core

Proof-of-Concept: MCP-compatible function definitions
for Home Assistant services.

This provides structured tool definitions similar to MCP
that can be used by LLM-powered conversations.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# MCP-style Tool Definitions
class MCPTool:
    """Represents an MCP tool"""
    def __init__(self, name: str, description: str, input_schema: Dict):
        self.name = name
        self.description = description
        self.input_schema = input_schema
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


# Home Assistant Tools (MCP-style)
HA_TOOLS = [
    MCPTool(
        name="ha.call_service",
        description="Call a Home Assistant service to control devices",
        input_schema={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "The domain of the service (e.g., light, switch, climate, fan)"
                },
                "service": {
                    "type": "string", 
                    "description": "The service to call (e.g., turn_on, turn_off, set_temperature)"
                },
                "service_data": {
                    "type": "object",
                    "description": "Data to pass to the service",
                    "properties": {
                        "entity_id": {"type": "string", "description": "The entity to control"},
                        "brightness_pct": {"type": "number", "description": "Brightness 0-100"},
                        "temperature": {"type": "number", "description": "Target temperature"},
                        "color": {"type": "string", "description": "Color in hex format"}
                    }
                },
                "target": {
                    "type": "object",
                    "description": "Target area or device",
                    "properties": {
                        "area_id": {"type": "string"},
                        "device_id": {"type": "string"},
                        "entity_id": {"type": "string"}
                    }
                }
            },
            "required": ["domain", "service"]
        }
    ),
    
    MCPTool(
        name="ha.get_states",
        description="Get the current state of Home Assistant entities",
        input_schema={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Filter by domain (e.g., light, sensor, switch)"
                },
                "entity_id": {
                    "type": "string", 
                    "description": "Filter by entity ID (supports wildcards)"
                },
                "area_id": {
                    "type": "string",
                    "description": "Filter by area"
                }
            }
        }
    ),
    
    MCPTool(
        name="ha.get_history",
        description="Get historical data for entities",
        input_schema={
            "type": "object",
            "properties": {
                "entity_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of entity IDs to get history for"
                },
                "start_time": {
                    "type": "string",
                    "description": "Start time (ISO 8601 format)"
                },
                "end_time": {
                    "type": "string",
                    "description": "End time (ISO 8601 format)"
                },
                "significant_changes_only": {
                    "type": "boolean",
                    "default": True,
                    "description": "Only return significant state changes"
                }
            },
            "required": ["entity_ids"]
        }
    ),
    
    MCPTool(
        name="ha.activate_scene",
        description="Activate a Home Assistant scene",
        input_schema={
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The scene entity to activate"
                }
            },
            "required": ["entity_id"]
        }
    ),
    
    MCPTool(
        name="ha.get_config",
        description="Get Home Assistant configuration information",
        input_schema={
            "type": "object",
            "properties": {}
        }
    ),
    
    MCPTool(
        name="ha.get_services",
        description="Get list of available Home Assistant services",
        input_schema={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Filter services by domain"
                }
            }
        }
    ),
    
    MCPTool(
        name="ha.fire_event",
        description="Fire a custom event in Home Assistant",
        input_schema={
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "The type of event to fire"
                },
                "event_data": {
                    "type": "object",
                    "description": "Data to include with the event"
                }
            },
            "required": ["event_type"]
        }
    ),
    
    MCPTool(
        name="calendar.get_events",
        description="Get calendar events from Home Assistant",
        input_schema={
            "type": "object",
            "properties": {
                "start_date_time": {
                    "type": "string",
                    "description": "Start datetime (ISO 8601)"
                },
                "end_date_time": {
                    "type": "string",
                    "description": "End datetime (ISO 8601)"
                },
                "calendar_id": {
                    "type": "string",
                    "description": "Specific calendar entity ID"
                }
            }
        }
    ),
    
    MCPTool(
        name="weather.get_forecast",
        description="Get weather forecast",
        input_schema={
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Weather entity ID"
                },
                "type": {
                    "type": "string",
                    "enum": ["hourly", "daily", "twice_daily"],
                    "description": "Type of forecast"
                }
            },
            "required": ["entity_id"]
        }
    ),
]


def get_tools() -> List[Dict]:
    """Get all available tools in MCP format"""
    return [tool.to_dict() for tool in HA_TOOLS]


def get_tool_by_name(name: str) -> Optional[MCPTool]:
    """Get a specific tool by name"""
    for tool in HA_TOOLS:
        if tool.name == name:
            return tool
    return None


def get_openai_functions() -> List[Dict]:
    """Get tools in OpenAI function calling format"""
    functions = []
    for tool in HA_TOOLS:
        functions.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema
            }
        })
    return functions
