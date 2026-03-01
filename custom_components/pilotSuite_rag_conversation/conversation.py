"""
PilotSuite RAG Conversation Handler für HomeAssistant

Integriert LLM-Fallback-Chain mit RAG-Kontext-Injektion.
Unterstützt HA-Assist (Sprache + Text).
"""

import asyncio
import logging
from typing import Optional

import aiohttp
import async_timeout
from homeassistant.components import conversation
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .llm_fallback import LLMFallbackChain, FallbackConfig
from .const import (
    CONF_RAG_API_URL,
    DEFAULT_RAG_API_URL,
)

_LOGGER = logging.getLogger(__name__)


class PilotSuiteRAGConversationHandler:
    """
    Conversation Handler mit LLM-Fallback-Chain und RAG-Kontext.
    
    Workflow:
    1. RAG-Suche (lokaler Kontext + optional Web)
    2. RAG-Kontext in Prompt injizieren (vor User-Input)
    3. LLM-Fallback-Chain.generate() für Antwort
    4. History updaten für Kontext
    """

    def __init__(
        self,
        hass: HomeAssistant,
        fallback_chain: LLMFallbackChain,
        rag_api_url: str = DEFAULT_RAG_API_URL,
        use_web_search: bool = False,
    ):
        """Initialize the conversation handler.
        
        Args:
            hass: HomeAssistant instance
            fallback_chain: LLMFallbackChain instance
            rag_api_url: URL der RAG-API
            use_web_search: Ob Web-Suche genutzt werden soll
        """
        self.hass = hass
        self.fallback_chain = fallback_chain
        self.rag_api_url = rag_api_url
        self.use_web_search = use_web_search
        self.history: dict[str, list] = {}  # Session-basiertes History-Tracking
        self._session: Optional[aiohttp.ClientSession] = None

    async def async_init(self):
        """Initialize async session."""
        self._session = aiohttp.ClientSession()

    async def async_cleanup(self):
        """Cleanup resources."""
        if self._session:
            await self._session.close()

    async def async_process(
        self,
        user_input: conversation.ConversationInput,
    ) -> conversation.ConversationResult:
        """
        Verarbeite User-Input mit RAG-Kontext und LLM-Fallback-Chain.
        
        Args:
            user_input: HomeAssistant ConversationInput
            
        Returns:
            ConversationResult mit generierter Antwort
            
        Raises:
            HomeAssistantError: Bei Fehlern in der Verarbeitung
        """
        try:
            # 1. RAG-Suche (lokaler Kontext)
            async with async_timeout.timeout(10):
                rag_results = await self._search_rag(
                    user_input.text,
                    use_web=self.use_web_search,
                )

            # 2. RAG-Kontext in Prompt injizieren (vor User-Input)
            prompt = self._build_prompt_with_rag_context(
                user_input.text,
                rag_results,
            )

            # 3. LLM-Fallback-Chain.generate() nutzen
            response = await self.fallback_chain.generate(prompt)

            # 4. History updaten für Kontext
            self._update_history(user_input.conversation_id, user_input.text, response)

            _LOGGER.info(
                "RAG Conversation processed: query='%s', rag_results=%d items, provider='%s'",
                user_input.text,
                len(rag_results.get("results", [])),
                self.fallback_chain.get_primary_provider(),
            )

            return conversation.ConversationResult(
                response=response,
                conversation_id=user_input.conversation_id,
            )

        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout during RAG search or LLM generation: %s", err)
            raise HomeAssistantError(
                "Zeitüberschreitung bei der Verarbeitung. Bitte versuche es erneut."
            ) from err
        except Exception as err:
            _LOGGER.exception("Error processing conversation: %s", err)
            raise HomeAssistantError(f"Fehler bei der Antwort-Generierung: {err}") from err

    async def _search_rag(self, query: str, use_web: bool = False) -> dict:
        """
        Suche in RAG-API nach kontextuellen Informationen.
        
        Args:
            query: Die Suchanfrage des Users
            use_web: Ob Web-Suche (SearXNG) genutzt werden soll
            
        Returns:
            dict mit Suchergebnissen
        """
        url = f"{self.rag_api_url}/api/rag/search"
        payload = {
            "query": query,
            "use_web": use_web,
        }

        _LOGGER.debug("RAG search request: url=%s, payload=%s", url, payload)

        if not self._session:
            self._session = aiohttp.ClientSession()

        async with self._session.post(url, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                _LOGGER.error(
                    "RAG-API returned error %s: %s",
                    resp.status,
                    text,
                )
                raise HomeAssistantError(
                    f"RAG-API Fehler ({resp.status}): {text}"
                )
            return await resp.json()

    def _build_prompt_with_rag_context(self, query: str, rag_results: dict) -> str:
        """
        Baue Prompt mit injiziertem RAG-Kontext (vor User-Input).
        
        Args:
            query: Die User-Frage
            rag_results: Ergebnisse der RAG-Suche
            
        Returns:
            Formatiertes Prompt mit RAG-Kontext für LLM
        """
        results = rag_results.get("results", [])
        query_type = rag_results.get("query_type", "lokal")
        sources = rag_results.get("sources", {})

        # Kontext aus RAG-Ergebnissen formatieren
        context_parts = []

        if results:
            for i, result in enumerate(results[:5], 1):  # Top 5 Ergebnisse
                source = result.get("source", "unknown")
                content = result.get("content", "")
                score = result.get("score", 0)
                context_parts.append(f"[{i}] {source} (Score: {score:.2f}): {content}")

        context_text = "\n".join(context_parts) if context_parts else "Keine kontextuellen Informationen gefunden."

        # Quellen-Information
        sources_info = []
        if sources.get("bm25"):
            sources_info.append(f"- BM25 (lexikalisch): {len(sources['bm25'])} Treffer")
        if sources.get("semantic"):
            sources_info.append(f"- Semantic (Vektor): {len(sources['semantic'])} Treffer")
        if sources.get("web"):
            sources_info.append(f"- Web (SearXNG): {len(sources['web'])} Treffer")

        sources_text = "\n".join(sources_info) if sources_info else "- Keine Quellen"

        # Prompt mit RAG-Kontext injiziert (vor User-Input)
        prompt = f"""Du bist ein hilfreicher HomeAssistant-Assistent mit Zugriff auf kontextuelle Informationen.

=== KONTEXT AUS RAG-API ===
Query-Typ: {query_type}
Suchquellen:
{sources_text}

Gefundene Informationen:
{context_text}
=== ENDE KONTEXT ===

User-Frage: {query}

Anweisungen:
1. Beantworte die Frage basierend auf dem bereitgestellten Kontext.
2. Wenn der Kontext nicht ausreicht, sage ehrlich, dass du die Information nicht hast.
3. Sei präzise und hilfreich.
4. Bei HA-spezifischen Fragen (States, Geräte, Automationen) priorisiere lokale Quellen.
5. Bei allgemeinen Fragen (Wetter, News) kannst du Web-Quellen nutzen.
6. Antworte in deutscher Sprache, es sei denn, der User fragt auf Englisch.

Antwort:"""

        _LOGGER.debug("Built prompt with %d context items", len(results))
        return prompt

    def _update_history(self, conversation_id: str, user_text: str, assistant_response: str):
        """
        Update conversation history for session tracking.
        
        Args:
            conversation_id: Die Konversations-ID
            user_text: User-Input
            assistant_response: Assistant-Antwort
        """
        if conversation_id not in self.history:
            self.history[conversation_id] = []

        # Limit history to last 10 messages per conversation
        self.history[conversation_id].append(
            {"role": "user", "content": user_text}
        )
        self.history[conversation_id].append(
            {"role": "assistant", "content": assistant_response}
        )
        self.history[conversation_id] = self.history[conversation_id][-20:]
