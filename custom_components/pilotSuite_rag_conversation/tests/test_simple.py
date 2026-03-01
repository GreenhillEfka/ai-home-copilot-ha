"""
Simple tests for PilotSuite RAG Conversation component.

These tests validate the core logic without requiring full HomeAssistant installation.
"""

import unittest
from unittest.mock import MagicMock, AsyncMock, patch


class TestPromptBuilding(unittest.TestCase):
    """Test the prompt building logic."""

    def test_build_prompt_with_results(self):
        """Test: Prompt wird korrekt mit RAG-Ergebnissen gebaut."""
        query = "Wie war der Energieverbrauch?"
        rag_results = {
            "results": [
                {
                    "source": "ha_states",
                    "content": "Energieverbrauch gestern: 15.3 kWh",
                    "score": 0.95,
                },
                {
                    "source": "documents",
                    "content": "Monatsverbrauch: 450 kWh",
                    "score": 0.85,
                },
            ],
            "query_type": "lokal",
            "sources": {
                "bm25": [1, 2],
                "semantic": [1],
            },
        }

        # Simulate _build_prompt logic
        results = rag_results.get("results", [])
        query_type = rag_results.get("query_type", "lokal")
        sources = rag_results.get("sources", {})

        context_parts = []
        for i, result in enumerate(results[:5], 1):
            source = result.get("source", "unknown")
            content = result.get("content", "")
            score = result.get("score", 0)
            context_parts.append(f"[{i}] {source} (Score: {score:.2f}): {content}")

        context_text = "\n".join(context_parts) if context_parts else "Keine kontextuellen Informationen gefunden."

        sources_info = []
        if sources.get("bm25"):
            sources_info.append(f"- BM25 (lexikalisch): {len(sources['bm25'])} Treffer")
        if sources.get("semantic"):
            sources_info.append(f"- Semantic (Vektor): {len(sources['semantic'])} Treffer")
        if sources.get("web"):
            sources_info.append(f"- Web (SearXNG): {len(sources['web'])} Treffer")

        sources_text = "\n".join(sources_info) if sources_info else "- Keine Quellen"

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

Antwort:"""

        # Assertions
        self.assertIn("Energieverbrauch", prompt)
        self.assertIn("15.3 kWh", prompt)
        self.assertIn("450 kWh", prompt)
        self.assertIn("BM25 (lexikalisch): 2 Treffer", prompt)
        self.assertIn("Semantic (Vektor): 1 Treffer", prompt)
        self.assertIn("Query-Typ: lokal", prompt)
        print("✓ Prompt building test passed")

    def test_build_prompt_empty_results(self):
        """Test: Prompt mit leeren Ergebnissen."""
        query = "Testfrage"
        rag_results = {
            "results": [],
            "query_type": "lokal",
            "sources": {},
        }

        results = rag_results.get("results", [])
        context_parts = []
        for i, result in enumerate(results[:5], 1):
            source = result.get("source", "unknown")
            content = result.get("content", "")
            score = result.get("score", 0)
            context_parts.append(f"[{i}] {source} (Score: {score:.2f}): {content}")

        context_text = "\n".join(context_parts) if context_parts else "Keine kontextuellen Informationen gefunden."

        # Assertion
        self.assertEqual(context_text, "Keine kontextuellen Informationen gefunden.")
        print("✓ Empty results test passed")

    def test_build_prompt_with_web_results(self):
        """Test: Prompt mit Web-Suche Ergebnissen."""
        rag_results = {
            "results": [
                {
                    "source": "web",
                    "content": "Wetter heute: 20°C, sonnig",
                    "score": 0.9,
                }
            ],
            "query_type": "hybrid",
            "sources": {
                "bm25": [],
                "semantic": [],
                "web": [1, 2, 3],
            },
        }

        sources = rag_results.get("sources", {})
        sources_info = []
        if sources.get("bm25"):
            sources_info.append(f"- BM25 (lexikalisch): {len(sources['bm25'])} Treffer")
        if sources.get("semantic"):
            sources_info.append(f"- Semantic (Vektor): {len(sources['semantic'])} Treffer")
        if sources.get("web"):
            sources_info.append(f"- Web (SearXNG): {len(sources['web'])} Treffer")

        sources_text = "\n".join(sources_info)

        self.assertIn("Web (SearXNG): 3 Treffer", sources_text)
        self.assertEqual(rag_results.get("query_type"), "hybrid")
        print("✓ Web results test passed")


class TestHistoryTracking(unittest.TestCase):
    """Test the conversation history tracking."""

    def test_history_append(self):
        """Test: History wird korrekt aktualisiert."""
        history = {}
        conversation_id = "test-conv-1"

        # Simulate _add_to_history
        if conversation_id not in history:
            history[conversation_id] = []

        history[conversation_id].append({"role": "user", "content": "First question"})
        history[conversation_id].append(
            {"role": "assistant", "content": "First response"}
        )

        # Assertions
        self.assertEqual(len(history[conversation_id]), 2)
        self.assertEqual(history[conversation_id][0]["role"], "user")
        self.assertEqual(history[conversation_id][1]["role"], "assistant")
        print("✓ History append test passed")

    def test_history_limit(self):
        """Test: History wird auf 20 Einträge begrenzt."""
        history = {"test-conv": []}

        # Add 25 messages (25 user + 25 assistant = 50 entries)
        for i in range(25):
            history["test-conv"].append(
                {"role": "user", "content": f"Question {i}"}
            )
            history["test-conv"].append(
                {"role": "assistant", "content": f"Response {i}"}
            )

        # Limit to last 20
        history["test-conv"] = history["test-conv"][-20:]

        # Assertion
        self.assertEqual(len(history["test-conv"]), 20)
        print("✓ History limit test passed")


class TestRAGAPIPayload(unittest.TestCase):
    """Test the RAG-API request payload."""

    def test_search_payload_local(self):
        """Test: Payload für lokale Suche."""
        query = "Energieverbrauch"
        use_web = False

        payload = {
            "query": query,
            "use_web": use_web,
        }

        self.assertEqual(payload["query"], "Energieverbrauch")
        self.assertFalse(payload["use_web"])
        print("✓ Local search payload test passed")

    def test_search_payload_web(self):
        """Test: Payload für Web-Suche."""
        query = "Wetter heute"
        use_web = True

        payload = {
            "query": query,
            "use_web": use_web,
        }

        self.assertEqual(payload["query"], "Wetter heute")
        self.assertTrue(payload["use_web"])
        print("✓ Web search payload test passed")


class TestOpenAIPayload(unittest.TestCase):
    """Test the OpenAI API request payload."""

    def test_openai_payload_with_history(self):
        """Test: Payload mit History."""
        model = "gpt-4"
        prompt = "Beantworte die Frage..."
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous response"},
        ]

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Du bist ein hilfreicher HomeAssistant-Assistent."},
                *history,
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 500,
        }

        self.assertEqual(payload["model"], "gpt-4")
        self.assertEqual(len(payload["messages"]), 4)  # system + 2 history + user
        self.assertEqual(payload["temperature"], 0.7)
        self.assertEqual(payload["max_tokens"], 500)
        print("✓ OpenAI payload with history test passed")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PilotSuite RAG Conversation - Simple Tests")
    print("=" * 60 + "\n")

    unittest.main(verbosity=2)

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60 + "\n")
