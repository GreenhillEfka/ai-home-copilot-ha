"""PilotSuite Conversation Agent for Home Assistant.

Proxies user utterances to the PilotSuite Core Add-on via the
OpenAI-compatible /v1/chat/completions endpoint and returns the
assistant reply as a ConversationResult.

Enhanced with:
- Home context injection (mood, zones, time) for smarter LLM responses
- Basic intent detection for direct HA service calls
- Conversation memory (last 5 turns per conversation)

Follows the HA 2024.x+ conversation agent pattern.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from homeassistant.components.conversation import (
    AbstractConversationAgent,
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent

from .const import DOMAIN
from .coordinator import CopilotApiError
from .conversation_ids import normalize_conversation_id

_LOGGER = logging.getLogger(__name__)

# ── Intent patterns for basic HA service detection ───────────────────
_INTENT_PATTERNS: dict[str, list[str]] = {
    "turn_on": [r"mach.*an", r"schalte.*ein", r"turn on", r"aktiviere"],
    "turn_off": [r"mach.*aus", r"schalte.*aus", r"turn off", r"deaktiviere"],
    "set_brightness": [r"helligkeit", r"dimme", r"brightness"],
    "set_temperature": [r"temperatur", r"heizung", r"thermostat"],
    "play_music": [r"spiel.*musik", r"play music", r"sonos"],
}

# Maximum conversation history turns (1 turn = user + assistant)
_MAX_HISTORY_TURNS = 5


class StyxConversationAgent(AbstractConversationAgent):
    """Conversation agent that proxies to PilotSuite Core."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        # Conversation history: conversation_id -> list of message dicts
        self._conversation_history: dict[str, list[dict[str, str]]] = {}

    @property
    def supported_languages(self) -> list[str]:
        """Return supported languages."""
        return ["de", "en"]

    # ── Home Context Builder ─────────────────────────────────────────

    async def _build_home_context(self) -> str:
        """Build home context string for LLM system prompt enrichment."""
        context_parts: list[str] = []

        try:
            # Get coordinator data
            entry_data = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {})
            coordinator = entry_data.get("coordinator")
            if coordinator and coordinator.data:
                data = coordinator.data

                # Mood
                mood = data.get("mood", {})
                if mood:
                    state = mood.get("mood", mood.get("state", "unbekannt"))
                    confidence = mood.get("confidence", 0)
                    try:
                        confidence_pct = f"{float(confidence):.0%}"
                    except (TypeError, ValueError):
                        confidence_pct = "?"
                    context_parts.append(
                        f"Aktuelle Stimmung: {state} ({confidence_pct})"
                    )

                # Zone presence
                zone_auto = data.get("zone_automation", {})
                zones_list = zone_auto.get("zones", [])
                if zones_list:
                    active = [
                        z.get("zone_id", z.get("name", "?"))
                        for z in zones_list
                        if z.get("presence_detected")
                        or z.get("config", {}).get("automation_mode", "off") != "off"
                    ]
                    if active:
                        context_parts.append(f"Aktive Zonen: {', '.join(active)}")

                # Neurons summary
                neurons = data.get("neurons", {})
                if neurons:
                    active_neurons = [
                        name for name, info in neurons.items()
                        if isinstance(info, dict)
                        and info.get("state") in ("active", "firing")
                    ]
                    if active_neurons:
                        context_parts.append(
                            f"Aktive Neuronen: {', '.join(active_neurons[:5])}"
                        )

            # Add time context (always, even if coordinator is unavailable)
            now = datetime.now()
            weekday = [
                "Montag", "Dienstag", "Mittwoch", "Donnerstag",
                "Freitag", "Samstag", "Sonntag",
            ][now.weekday()]
            context_parts.append(f"Zeit: {now.strftime('%H:%M')}, {weekday}")

        except Exception:
            _LOGGER.debug("Home context building failed, continuing without", exc_info=True)

        return "\n".join(context_parts) if context_parts else ""

    # ── Intent Detection ─────────────────────────────────────────────

    def _detect_intent(self, text: str) -> tuple[str | None, str | None]:
        """Detect basic intent and extract a rough entity hint from user text.

        Returns (intent_name, entity_hint) or (None, None).
        """
        text_lower = text.lower()
        for intent_name, patterns in _INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Try to extract entity hint: last quoted word or noun-like token
                    entity_hint = self._extract_entity_hint(text_lower, pattern)
                    return intent_name, entity_hint
        return None, None

    @staticmethod
    def _extract_entity_hint(text: str, matched_pattern: str) -> str | None:
        """Try to extract an entity name hint from the user text."""
        # Check for quoted entity names first: "Kuechenlicht", 'Flur'
        quoted = re.findall(r'["\u201e\u201c\u201d\']([\w\s]+)["\u201e\u201c\u201d\']', text)
        if quoted:
            return quoted[0].strip()

        # Remove the matched intent phrase and take remaining words
        cleaned = re.sub(matched_pattern, "", text).strip()
        # Remove common filler words
        for filler in ["bitte", "mal", "das", "die", "der", "den", "dem",
                       "im", "in", "the", "please", "kannst du", "koenntest du"]:
            cleaned = re.sub(rf"\b{filler}\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip(" .,!?")
        return cleaned if cleaned else None

    async def _execute_intent(
        self, intent_name: str, entity_hint: str | None
    ) -> str | None:
        """Try to execute a detected intent via HA services.

        Returns a human-readable result string or None if execution failed.
        """
        if not entity_hint:
            return None

        # Try to find a matching entity
        entity_id = self._resolve_entity(entity_hint)
        if not entity_id:
            _LOGGER.debug(
                "Intent %s detected but no entity found for hint '%s'",
                intent_name, entity_hint,
            )
            return None

        try:
            if intent_name == "turn_on":
                domain = entity_id.split(".")[0]
                await self.hass.services.async_call(
                    domain, "turn_on", {"entity_id": entity_id}
                )
                return f"Ich habe {entity_hint} fuer dich eingeschaltet."

            if intent_name == "turn_off":
                domain = entity_id.split(".")[0]
                await self.hass.services.async_call(
                    domain, "turn_off", {"entity_id": entity_id}
                )
                return f"Ich habe {entity_hint} fuer dich ausgeschaltet."

            if intent_name == "set_brightness":
                # Default brightness change (50%)
                await self.hass.services.async_call(
                    "light", "turn_on",
                    {"entity_id": entity_id, "brightness_pct": 50},
                )
                return f"Ich habe die Helligkeit von {entity_hint} angepasst."

            if intent_name == "set_temperature":
                # Acknowledge but don't change without explicit value
                return None

            if intent_name == "play_music":
                await self.hass.services.async_call(
                    "media_player", "media_play", {"entity_id": entity_id}
                )
                return f"Ich habe die Wiedergabe auf {entity_hint} gestartet."

        except Exception:
            _LOGGER.debug(
                "Intent execution failed for %s on %s",
                intent_name, entity_id, exc_info=True,
            )
        return None

    def _resolve_entity(self, hint: str) -> str | None:
        """Resolve a fuzzy entity hint to an actual HA entity_id."""
        if not hint:
            return None

        hint_lower = hint.lower().replace(" ", "_")
        states = self.hass.states.async_all()

        # 1. Exact entity_id match
        for state in states:
            if state.entity_id.lower() == hint_lower:
                return state.entity_id

        # 2. Entity ID contains the hint
        for state in states:
            if hint_lower in state.entity_id.lower():
                return state.entity_id

        # 3. Friendly name match
        for state in states:
            friendly = (state.attributes.get("friendly_name") or "").lower()
            if hint.lower() in friendly:
                return state.entity_id

        return None

    # ── Conversation Memory ──────────────────────────────────────────

    def _get_history(self, conversation_id: str) -> list[dict[str, str]]:
        """Get conversation history for a given conversation ID."""
        return self._conversation_history.get(conversation_id, [])

    def _add_to_history(
        self,
        conversation_id: str,
        user_text: str,
        assistant_text: str,
    ) -> None:
        """Add a turn (user + assistant) to conversation history."""
        if conversation_id not in self._conversation_history:
            self._conversation_history[conversation_id] = []

        history = self._conversation_history[conversation_id]
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": assistant_text})

        # Trim to last N turns (each turn = 2 messages)
        max_messages = _MAX_HISTORY_TURNS * 2
        if len(history) > max_messages:
            self._conversation_history[conversation_id] = history[-max_messages:]

    # ── Main Processing ──────────────────────────────────────────────

    async def async_process(
        self, user_input: ConversationInput
    ) -> ConversationResult:
        """Process a user utterance via PilotSuite Core."""
        entry_data = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {})
        coordinator = entry_data.get("coordinator")
        conversation_id = normalize_conversation_id(user_input.conversation_id)
        language = user_input.language or self.hass.config.language or "de"

        if coordinator is None:
            return self._error_result(
                language, "PilotSuite coordinator not available.", conversation_id
            )

        # ── Build messages with context and history ───────────────────
        messages: list[dict[str, str]] = []

        # 1. System message with home context
        try:
            home_context = await self._build_home_context()
        except Exception:
            home_context = ""
            _LOGGER.debug("Home context injection failed", exc_info=True)

        system_prompt = "Du bist Styx, ein intelligenter Haus-Assistent."
        if home_context:
            system_prompt = (
                f"Aktueller Hausstatus:\n{home_context}\n\n{system_prompt}"
            )
        messages.append({"role": "system", "content": system_prompt})

        # 2. Conversation history (previous turns)
        history = self._get_history(conversation_id)
        if history:
            messages.extend(history)

        # 3. Current user message
        messages.append({"role": "user", "content": user_input.text})

        # ── Send to Core ─────────────────────────────────────────────
        try:
            result = await coordinator.api.async_chat_completions(
                messages=messages,
                conversation_id=conversation_id,
            )
        except CopilotApiError as err:
            _LOGGER.error("PilotSuite API error: %s", err)
            return self._error_result(
                language,
                "PilotSuite Core ist gerade nicht erreichbar."
                if language.startswith("de")
                else "PilotSuite Core is currently unavailable.",
                conversation_id,
            )
        except TimeoutError:
            _LOGGER.error("PilotSuite conversation request timed out")
            return self._error_result(
                language, "Request to PilotSuite Core timed out.", conversation_id
            )
        except Exception as err:
            _LOGGER.error("PilotSuite conversation request failed: %s", err)
            return self._error_result(
                language, "Could not reach PilotSuite Core.", conversation_id
            )

        reply = result.get("content", "") or ""

        # ── Intent detection and execution ───────────────────────────
        intent_suffix = ""
        try:
            detected_intent, entity_hint = self._detect_intent(user_input.text)
            if detected_intent:
                _LOGGER.debug(
                    "Detected intent=%s, entity_hint=%s",
                    detected_intent, entity_hint,
                )
                action_result = await self._execute_intent(
                    detected_intent, entity_hint
                )
                if action_result:
                    intent_suffix = f"\n\n{action_result}"
        except Exception:
            _LOGGER.debug("Intent detection/execution failed", exc_info=True)

        full_reply = (reply + intent_suffix).strip()

        # ── Update conversation history ──────────────────────────────
        self._add_to_history(conversation_id, user_input.text, full_reply)

        response = intent.IntentResponse(language=language)
        response.async_set_speech(full_reply or "No response from PilotSuite.")
        return ConversationResult(
            response=response,
            conversation_id=conversation_id,
        )

    @staticmethod
    def _error_result(
        language: str,
        message: str,
        conversation_id: str,
    ) -> ConversationResult:
        """Build a ConversationResult for error cases."""
        response = intent.IntentResponse(language=language)
        response.async_set_speech(message)
        return ConversationResult(
            response=response,
            conversation_id=conversation_id,
        )


async def async_setup_conversation(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Register the PilotSuite conversation agent."""
    from homeassistant.components.conversation import async_set_agent

    agent = StyxConversationAgent(hass, entry)
    async_set_agent(hass, entry, agent)
    _LOGGER.info("PilotSuite conversation agent registered")


async def async_unload_conversation(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Unregister the PilotSuite conversation agent."""
    from homeassistant.components.conversation import async_unset_agent

    async_unset_agent(hass, entry)
    _LOGGER.info("PilotSuite conversation agent unregistered")
