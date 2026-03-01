"""
ChatHandler für PilotSuite-Styx mit RAG-API Integration.

Verarbeitet Chat-Queries mit kontextuellem Wissen aus:
- Lokalen Datenquellen (HA-States, Dokumente, History)
- Optional: Web-Suche via SearXNG
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests
from requests import RequestException

logger = logging.getLogger(__name__)


class ChatHandler:
    """
    Handler für Chat-Queries mit RAG-Kontext.
    
    Integration:
    - RAG-API für kontextuelle Suche (lokal + optional Web)
    - Ollama für lokale LLM-Inferenz
    - Logging für History und zukünftigen RAG-Kontext
    """
    
    def __init__(self, rag_api_url: str, ollama_url: str):
        """
        Initialisiere ChatHandler.
        
        Args:
            rag_api_url: URL der RAG-API (z.B. http://localhost:8765)
            ollama_url: URL von Ollama (z.B. http://localhost:11434)
        """
        self.rag_api_url = rag_api_url.rstrip("/")
        self.ollama_url = ollama_url.rstrip("/")
        logger.info(
            "ChatHandler initialized (rag_api_url=%s, ollama_url=%s)",
            self.rag_api_url,
            self.ollama_url
        )
    
    def handle_query(
        self,
        query: str,
        user_id: str,
        use_web: bool = False,
        model: str = "qwen3.5:397b-cloud"
    ) -> Dict[str, Any]:
        """
        Verarbeite Chat-Query mit RAG-Kontext.
        
        Args:
            query: User-Frage
            user_id: User-Identifier für History-Logging
            use_web: Web-Suche aktivieren (SearXNG)
            model: Ollama-Modell für Inferenz
        
        Returns:
            Dict mit:
            - response: LLM-Antwort
            - sources: RAG-Sources (für UI-Anzeige)
            - query_type: local|web|hybrid
        """
        logger.info(
            "Handling query (user_id=%s, use_web=%s, query=%s)",
            user_id,
            use_web,
            query[:100] if len(query) > 100 else query
        )
        
        # 1. RAG-Suche (lokal + optional Web)
        rag_results = self._search_rag(query, use_web)
        
        # 2. LLM-Prompt mit RAG-Kontext
        prompt = self._build_prompt(query, rag_results)
        
        # 3. Ollama-Inferenz
        response = self._call_ollama(prompt, model)
        
        # 4. Log für History
        self._log_interaction(user_id, query, response, rag_results)
        
        return {
            "response": response,
            "sources": rag_results.get("sources", []),
            "query_type": rag_results.get("query_type", "local"),
            "context_used": rag_results.get("results", []),
        }
    
    def _search_rag(self, query: str, use_web: bool) -> Dict[str, Any]:
        """
        Suche in RAG-API.
        
        Args:
            query: Suchanfrage
            use_web: Web-Suche via SearXNG aktivieren
        
        Returns:
            RAG-Ergebnisse mit Results, Sources und Query-Type
        """
        search_url = f"{self.rag_api_url}/api/rag/search"
        
        payload = {
            "query": query,
            "use_web": use_web,
            "top_k": 10,
            "include_text": True,
            "include_metadata": True,
        }
        
        logger.debug("RAG search request (url=%s, payload=%s)", search_url, payload)
        
        try:
            resp = requests.post(
                search_url,
                json=payload,
                timeout=30,
            )
            
            if resp.status_code != 200:
                logger.error(
                    "RAG search failed (status=%s, url=%s)",
                    resp.status_code,
                    search_url
                )
                return {
                    "results": [],
                    "sources": [],
                    "query_type": "local",
                    "error": f"RAG API returned status {resp.status_code}",
                }
            
            result = resp.json()
            logger.info(
                "RAG search completed (results_count=%s, query_type=%s)",
                len(result.get("results", [])),
                result.get("query_type", "local")
            )
            return result
                    
        except RequestException as exc:
            logger.exception("RAG search request failed: %s", exc)
            return {
                "results": [],
                "sources": [],
                "query_type": "local",
                "error": str(exc),
            }
        except Exception as exc:
            logger.exception("Unexpected error in RAG search: %s", exc)
            return {
                "results": [],
                "sources": [],
                "query_type": "local",
                "error": str(exc),
            }
    
    def _build_prompt(self, query: str, rag_results: Dict[str, Any]) -> str:
        """
        Baue Prompt mit RAG-Kontext für LLM.
        
        Args:
            query: User-Frage
            rag_results: Ergebnisse der RAG-Suche
        
        Returns:
            Formatierter Prompt für LLM
        """
        results = rag_results.get("results", [])
        query_type = rag_results.get("query_type", "local")
        
        if not results:
            # Kein Kontext verfügbar
            logger.info("No RAG context available, using query-only prompt")
            return f"""Beantworte die folgende Frage hilfreich, präzise und freundlich.
Wenn du unsicher bist oder nicht genug Informationen hast, sage es offen.

Frage: {query}"""
        
        # Kontext aus RAG-Ergebnissen extrahieren
        context_parts = []
        for i, result in enumerate(results, start=1):
            content = result.get("content") or result.get("text", "")
            source = result.get("source", "Unknown")
            score = result.get("score", 0)
            
            if content:
                context_parts.append(
                    f"[Quelle {i}] (Score: {score:.3f}, Quelle: {source})\n{content}"
                )
        
        context = "\n\n".join(context_parts)
        
        logger.info(
            "Built prompt with context (query_type=%s, context_sources=%s)",
            query_type,
            len(context_parts)
        )
        
        return f"""Basierend auf dem folgenden Kontext:

{context}

Beantworte die Frage präzise, hilfreich und freundlich.
- Nutze die Informationen aus dem Kontext, wo relevant
- Zitiere Quellen implizit (z.B. "Laut den Daten...")
- Wenn der Kontext nicht ausreicht, sage es offen
- Sei natürlich und konversationell

Frage: {query}"""
    
    def _call_ollama(
        self,
        prompt: str,
        model: str = "qwen3.5:397b-cloud"
    ) -> str:
        """
        Rufe Ollama für LLM-Inferenz auf.
        
        Args:
            prompt: Prompt für LLM
            model: Ollama-Modell
        
        Returns:
            LLM-Antwort als String
        """
        generate_url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        
        logger.debug(
            "Ollama generate request (model=%s, prompt_length=%s)",
            model,
            len(prompt)
        )
        
        try:
            resp = requests.post(
                generate_url,
                json=payload,
                timeout=60,
            )
            
            if resp.status_code != 200:
                logger.error(
                    "Ollama generate failed (status=%s, model=%s)",
                    resp.status_code,
                    model
                )
                return f"Entschuldigung, ich konnte keine Antwort generieren (Ollama Status: {resp.status_code})."
            
            result = resp.json()
            response_text = result.get("response", "")
            
            logger.info(
                "Ollama generate completed (model=%s, response_length=%s)",
                model,
                len(response_text) if response_text else 0
            )
            return response_text
                    
        except RequestException as exc:
            logger.exception("Ollama request failed: %s", exc)
            return f"Entschuldigung, es gab ein Problem mit der LLM-Verbindung: {exc}"
        except Exception as exc:
            logger.exception("Unexpected error in Ollama call: %s", exc)
            return f"Entschuldigung, ein unerwarteter Fehler ist aufgetreten: {exc}"
    
    def _log_interaction(
        self,
        user_id: str,
        query: str,
        response: str,
        rag_results: Dict[str, Any]
    ) -> None:
        """
        Logge Interaktion für History und zukünftigen RAG-Kontext.
        
        Args:
            user_id: User-Identifier
            query: User-Frage
            response: LLM-Antwort
            rag_results: Verwendete RAG-Ergebnisse
        """
        # TODO: Implementiere persistentes Logging
        # Optionen:
        # 1. SQLite-DB (ähnlich wie BM25-Index)
        # 2. HA Events (für Integration in HA-History)
        # 3. File-based logging (einfach, aber weniger performant)
        
        logger.info(
            "Interaction logged (user_id=%s, query_length=%s, response_length=%s, sources_count=%s)",
            user_id,
            len(query),
            len(response),
            len(rag_results.get("sources", []))
        )
        
        # Placeholder für zukünftige Implementierung
        # self._store_in_history_db(user_id, query, response, rag_results)
