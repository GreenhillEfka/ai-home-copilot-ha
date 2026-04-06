"""Intent Router for HA Voice Commands — Slice 163.

Routes voice commands intelligently between:
1. Direct HA service calls (known intents)
2. Local LLM (Ollama) for simple queries
3. Cloud LLM for complex reasoning
4. RAG-enhanced responses with home context

Intent Categories:
- home_control: lights, climate, covers → HA service call
- query: weather, facts, how-to → RAG + LLM
- complex_task: planning, reasoning → Cloud LLM
- fallback: unknown → Local LLM

Architecture:
User Voice → Intent Detection → Router → Response → TTS (optional)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

_LOGGER = logging.getLogger(__name__)


class IntentCategory(str, Enum):
    """Intent categories for routing."""
    HOME_CONTROL = "home_control"
    QUERY = "query"
    COMPLEX_TASK = "complex_task"
    FALLBACK = "fallback"


@dataclass
class RouteDecision:
    """Routing decision for a command."""
    category: IntentCategory
    confidence: float
    handler: str  # "ha_service", "local_llm", "cloud_llm", "rag_llm"
    parameters: Dict[str, Any]
    reason: str


# ─── Intent Patterns ────────────────────────────────────────────────────────

HOME_CONTROL_PATTERNS = {
    "light_on": [
        r"licht\s+(an|ein|einschalten)",
        r"mach\s+das\s+licht\s+(an|ein)",
        r"schalte\s+das\s+licht\s+ein",
        r"light\s+on",
        r"turn\s+on\s+(the\s+)?light",
    ],
    "light_off": [
        r"licht\s+aus",
        r"mach\s+das\s+licht\s+aus",
        r"schalte\s+das\s+licht\s+aus",
        r"light\s+off",
        r"turn\s+off\s+(the\s+)?light",
    ],
    "light_dim": [
        r"licht\s+(dimmen|dunkler)",
        r"mach\s+das\s+licht\s+(dunkler|weniger)",
        r"dim\s+(the\s+)?light",
        r"lower\s+(the\s+)?light",
    ],
    "light_brighten": [
        r"licht\s+(heller|mehr)",
        r"mach\s+das\s+licht\s+heller",
        r"brighten\s+(the\s+)?light",
        r"more\s+light",
    ],
    "climate_set": [
        r"(heizung|temperatur)\s+auf\s+(\d+)",
        r"stell\s+(die\s+)?(heizung|temperatur)\s+auf\s+(\d+)",
        r"set\s+(the\s+)?(heat|temperature)\s+to\s+(\d+)",
        r"make\s+it\s+(\d+)\s+degrees",
    ],
    "cover_open": [
        r"(rollladen|vorhang|jalousie)\s+(auf|öffnen|hoch)",
        r"mach\s+(die\s+)?(rollladen|vorhänge|jalousien)\s+auf",
        r"open\s+(the\s+)?(blinds|curtains|shutters)",
        r"raise\s+(the\s+)?blinds",
    ],
    "cover_close": [
        r"(rollladen|vorhang|jalousie)\s+(zu|schließen|runter)",
        r"mach\s+(die\s+)?(rollladen|vorhänge|jalousien)\s+zu",
        r"close\s+(the\s+)?(blinds|curtains|shutters)",
        r"lower\s+(the\s+)?blinds",
    ],
    "media_play": [
        r"(musik|radio|spotify)\s+(start|abspielen|play)",
        r"spiel\s+(musik|radio)",
        r"play\s+(music|radio)",
        r"start\s+music",
    ],
    "media_stop": [
        r"(musik|radio)\s+(stop|aus|anhalten)",
        r"stop\s+(music|radio)",
        r"turn\s+off\s+(music|radio)",
    ],
}

QUERY_PATTERNS = {
    "weather": [
        r"wetter",
        r"wird\s+es\s+(regen|sonnig|kalt|warm)",
        r"wie\s+ist\s+das\s+wetter",
        r"weather",
        r"is\s+it\s+(raining|sunny|cold)",
    ],
    "time_date": [
        r"(wie\s+viel\s+)?uhr(zeit)?",
        r"welcher\s+tag",
        r"wie\s+spät",
        r"what\s+time",
        r"what\s+day",
        r"date",
    ],
    "how_to": [
        r"wie\s+kann\s+ich",
        r"wie\s+funktioniert",
        r"wie\s+mache\s+ich",
        r"how\s+to",
        r"how\s+can\s+i",
        r"how\s+does",
    ],
    "what_is": [
        r"was\s+ist",
        r"was\s+sind",
        r"what\s+is",
        r"what\s+are",
        r"explain",
    ],
}

COMPLEX_TASK_PATTERNS = {
    "planning": [
        r"plan(e)?\s+",
        r"organisiere(n)?\s+",
        r"plan\s+",
        r"organize\s+",
        r"schedule\s+",
        r"arrange\s+",
    ],
    "reasoning": [
        r"warum\s+",
        r"weshalb\s+",
        r"wieso\s+",
        r"why\s+",
        r"should\s+i",
        r"what\s+should",
        r"recommend",
    ],
    "comparison": [
        r"vergleich(e)?\s+",
        r"unterschied\s+zwischen",
        r"compare\s+",
        r"difference\s+between",
        r"which\s+is\s+better",
    ],
}


class IntentRouter:
    """Route voice commands to appropriate handlers.
    
    Usage:
        router = IntentRouter(hass, core_client)
        decision = router.route("mach das licht an")
        if decision.handler == "ha_service":
            await hass.services.async_call(...)
    """
    
    def __init__(
        self,
        hass: Any,
        core_client: Optional[Any] = None,
        rag_client: Optional[Any] = None,
    ) -> None:
        self._hass = hass
        self._core_client = core_client
        self._rag_client = rag_client
    
    def route(self, command: str, context: Optional[Dict[str, Any]] = None) -> RouteDecision:
        """Route a voice command to the appropriate handler.
        
        Args:
            command: User's voice command text
            context: Optional context (zone, time, user, etc.)
        
        Returns:
            RouteDecision with category, confidence, handler, and parameters
        """
        command_lower = command.lower().strip()
        
        # Check home control patterns
        for intent_type, patterns in HOME_CONTROL_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, command_lower)
                if match:
                    params = self._extract_home_control_params(intent_type, match, command)
                    return RouteDecision(
                        category=IntentCategory.HOME_CONTROL,
                        confidence=0.95,
                        handler="ha_service",
                        parameters=params,
                        reason=f"Matched home control intent: {intent_type}",
                    )
        
        # Check query patterns
        for intent_type, patterns in QUERY_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, command_lower)
                if match:
                    return RouteDecision(
                        category=IntentCategory.QUERY,
                        confidence=0.85,
                        handler="rag_llm" if intent_type == "how_to" else "local_llm",
                        parameters={"query_type": intent_type, "command": command},
                        reason=f"Matched query intent: {intent_type}",
                    )
        
        # Check complex task patterns
        for intent_type, patterns in COMPLEX_TASK_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, command_lower)
                if match:
                    return RouteDecision(
                        category=IntentCategory.COMPLEX_TASK,
                        confidence=0.80,
                        handler="cloud_llm",
                        parameters={"task_type": intent_type, "command": command},
                        reason=f"Matched complex task: {task_type}",
                    )
        
        # Fallback to local LLM
        return RouteDecision(
            category=IntentCategory.FALLBACK,
            confidence=0.50,
            handler="local_llm",
            parameters={"command": command},
            reason="No specific pattern matched, using fallback",
        )
    
    def _extract_home_control_params(
        self,
        intent_type: str,
        match: re.Match,
        command: str,
    ) -> Dict[str, Any]:
        """Extract parameters from home control command."""
        params: Dict[str, Any] = {"intent_type": intent_type}
        
        # Extract temperature for climate commands
        if "climate" in intent_type:
            temp_match = re.search(r"(\d+)", command)
            if temp_match:
                params["temperature"] = int(temp_match.group(1))
        
        # Extract brightness for light commands
        if "dim" in intent_type or "brighten" in intent_type:
            # Could extract percentage if specified
            params["brightness"] = 30 if "dim" in intent_type else 80
        
        # Extract zone if mentioned
        zone_match = re.search(r"(wohnzimmer|schlafzimmer|küche|bad|flur|büro)", command.lower())
        if zone_match:
            params["zone"] = zone_match.group(1)
        
        return params
    
    async def execute(self, decision: RouteDecision) -> Dict[str, Any]:
        """Execute a routing decision.
        
        Args:
            decision: RouteDecision from route()
        
        Returns:
            Result dict with success status and response text
        """
        if decision.handler == "ha_service":
            return await self._execute_ha_service(decision)
        elif decision.handler == "local_llm":
            return await self._execute_local_llm(decision)
        elif decision.handler == "cloud_llm":
            return await self._execute_cloud_llm(decision)
        elif decision.handler == "rag_llm":
            return await self._execute_rag_llm(decision)
        else:
            return {"success": False, "error": f"Unknown handler: {decision.handler}"}
    
    async def _execute_ha_service(self, decision: RouteDecision) -> Dict[str, Any]:
        """Execute HA service call for home control."""
        params = decision.parameters
        intent_type = params.get("intent_type", "")
        
        service_domain = "homeassistant"
        service_name = ""
        service_data: Dict[str, Any] = {}
        
        # Map intent to HA service
        if "light_on" in intent_type:
            service_domain = "light"
            service_name = "turn_on"
        elif "light_off" in intent_type:
            service_domain = "light"
            service_name = "turn_off"
        elif "light_dim" in intent_type:
            service_domain = "light"
            service_name = "turn_on"
            service_data["brightness_pct"] = params.get("brightness", 30)
        elif "light_brighten" in intent_type:
            service_domain = "light"
            service_name = "turn_on"
            service_data["brightness_pct"] = params.get("brightness", 80)
        elif "climate_set" in intent_type:
            service_domain = "climate"
            service_name = "set_temperature"
            service_data["temperature"] = params.get("temperature", 21)
        elif "cover_open" in intent_type:
            service_domain = "cover"
            service_name = "open_cover"
        elif "cover_close" in intent_type:
            service_domain = "cover"
            service_name = "close_cover"
        elif "media_play" in intent_type:
            service_domain = "media_player"
            service_name = "media_play"
        elif "media_stop" in intent_type:
            service_domain = "media_player"
            service_name = "media_stop"
        
        if not service_name:
            return {"success": False, "error": f"Unknown intent: {intent_type}"}
        
        # Add zone/entity targeting if specified
        zone = params.get("zone")
        if zone:
            # Find entities in zone
            # This would need zone entity mapping
            pass
        
        try:
            await self._hass.services.async_call(
                service_domain,
                service_name,
                service_data,
                blocking=True,
            )
            
            return {
                "success": True,
                "response": f"✓ {intent_type.replace('_', ' ').title()} executed",
                "service": f"{service_domain}.{service_name}",
            }
        except Exception as exc:
            _LOGGER.error("HA service call failed: %s", exc)
            return {"success": False, "error": str(exc)}
    
    async def _execute_local_llm(self, decision: RouteDecision) -> Dict[str, Any]:
        """Execute local LLM (Ollama) for simple queries."""
        if not self._core_client:
            return {"success": False, "error": "Core client not available"}
        
        try:
            result = await self._core_client.search(
                query=decision.parameters.get("command", ""),
                namespace="default",
                top_k=3,
            )
            
            return {
                "success": True,
                "response": result.get("results", [{}])[0].get("text", "No answer found"),
                "handler": "local_llm",
            }
        except Exception as exc:
            _LOGGER.error("Local LLM failed: %s", exc)
            return {"success": False, "error": str(exc)}
    
    async def _execute_cloud_llm(self, decision: RouteDecision) -> Dict[str, Any]:
        """Execute cloud LLM for complex reasoning."""
        if not self._core_client:
            return {"success": False, "error": "Core client not available"}
        
        # Use cloud model for complex tasks
        try:
            # This would call the cloud LLM endpoint
            # For now, fall back to local
            return await self._execute_local_llm(decision)
        except Exception as exc:
            _LOGGER.error("Cloud LLM failed: %s", exc)
            return {"success": False, "error": str(exc)}
    
    async def _execute_rag_llm(self, decision: RouteDecision) -> Dict[str, Any]:
        """Execute RAG-enhanced LLM for how-to queries."""
        if not self._core_client:
            return await self._execute_local_llm(decision)
        
        try:
            result = await self._core_client.search(
                query=decision.parameters.get("command", ""),
                namespace="ha_docs",
                top_k=5,
            )
            
            # Synthesize answer from RAG results
            results = result.get("results", [])
            if results:
                answer = "\n\n".join(r.get("text", "") for r in results[:3])
                return {
                    "success": True,
                    "response": answer,
                    "handler": "rag_llm",
                    "sources": len(results),
                }
            
            return {"success": True, "response": "I couldn't find specific information about that."}
        except Exception as exc:
            _LOGGER.error("RAG LLM failed: %s", exc)
            return {"success": False, "error": str(exc)}


# ─── Global Instance ────────────────────────────────────────────────────────

_router: Optional[IntentRouter] = None


def get_intent_router(
    hass: Any,
    core_client: Optional[Any] = None,
    rag_client: Optional[Any] = None,
) -> IntentRouter:
    """Get or create the global intent router instance."""
    global _router
    if _router is None:
        _router = IntentRouter(hass, core_client, rag_client)
    return _router
