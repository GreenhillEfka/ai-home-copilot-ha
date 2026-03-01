#!/usr/bin/env python3
"""RAG Hybrid Search API Examples.

Demonstrates usage of the PilotSuite RAG Hybrid Search API
for semantic and lexical search with RRF re-ranking.

Requirements:
    - requests library
    - Valid API token from PilotSuite Core

Usage:
    python example_rag_search.py
"""

import requests
import json
from typing import Optional


class RAGSearchExample:
    """Example client for RAG Hybrid Search API."""
    
    def __init__(self, base_url: str = "http://localhost:8909", token: str = None):
        """Initialize RAG search client.
        
        Args:
            base_url: PilotSuite Core API base URL
            token: Authentication token (X-Auth-Token)
        """
        self.base_url = base_url.rstrip('/')
        self.token = token or "your-api-token"
        self.headers = {
            "X-Auth-Token": self.token,
            "Content-Type": "application/json"
        }
        self.api_base = f"{self.base_url}/api/v1/rag"
    
    def search(self, query: str, top_k: int = 10, use_multi_query: bool = False) -> dict:
        """Perform hybrid search.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            use_multi_query: Enable multi-query mode
            
        Returns:
            Search results with scores and metadata
        """
        endpoint = f"{self.api_base}/search"
        payload = {
            "query": query,
            "top_k": top_k,
            "use_multi_query": use_multi_query
        }
        
        response = requests.post(endpoint, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def search_multi(self, queries: list, top_k: int = 10) -> dict:
        """Perform multi-query search.
        
        Args:
            queries: List of query variations
            top_k: Number of results to return
            
        Returns:
            Combined search results
        """
        endpoint = f"{self.api_base}/search/multi"
        payload = {
            "queries": queries,
            "top_k": top_k
        }
        
        response = requests.post(endpoint, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def add_document(self, doc_id: str, content: str, metadata: dict = None) -> dict:
        """Add document to search index.
        
        Args:
            doc_id: Unique document identifier
            content: Document text content
            metadata: Optional metadata dictionary
            
        Returns:
            Indexing result
        """
        endpoint = f"{self.api_base}/documents"
        payload = {
            "doc_id": doc_id,
            "content": content,
            "metadata": metadata or {}
        }
        
        response = requests.post(endpoint, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def delete_document(self, doc_id: str) -> dict:
        """Remove document from index.
        
        Args:
            doc_id: Document identifier to remove
            
        Returns:
            Deletion result
        """
        endpoint = f"{self.api_base}/documents/{doc_id}"
        
        response = requests.delete(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> dict:
        """Get search engine statistics.
        
        Returns:
            Index statistics and configuration
        """
        endpoint = f"{self.api_base}/stats"
        
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()


def example_basic_search(client: RAGSearchExample):
    """Example: Basic hybrid search."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Hybrid Search")
    print("="*60)
    
    query = "living room lighting automation"
    print(f"\nQuery: '{query}'")
    
    results = client.search(query, top_k=5)
    
    print(f"\nFound {results['count']} results in {results['execution_time_ms']:.2f}ms")
    print(f"Query type: {results['query_type']}")
    
    for i, result in enumerate(results['results'], 1):
        print(f"\n{i}. [Score: {result['score']:.4f}]")
        print(f"   BM25: {result['bm25_score']:.4f} | Vector: {result['vector_score']:.4f}")
        print(f"   RRF: {result['rrf_score']:.6f} | Final Rank: {result['final_rank']}")
        print(f"   Content: {result['content'][:150]}...")
        if result.get('metadata'):
            print(f"   Metadata: {json.dumps(result['metadata'], indent=2)}")


def example_multi_query_search(client: RAGSearchExample):
    """Example: Multi-query search with language variations."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Multi-Query Search (Multilingual)")
    print("="*60)
    
    queries = [
        "living room lights",
        "wohnzimmer beleuchtung",
        "lighting automation living room"
    ]
    
    print(f"\nQueries: {queries}")
    
    results = client.search_multi(queries, top_k=5)
    
    print(f"\nFound {results['count']} results in {results['execution_time_ms']:.2f}ms")
    print(f"Queries processed: {results['queries_processed']}")
    
    for i, result in enumerate(results['results'], 1):
        print(f"\n{i}. [Score: {result['score']:.4f}]")
        print(f"   Content: {result['content'][:150]}...")


def example_index_documents(client: RAGSearchExample):
    """Example: Index automation documents."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Index Documents")
    print("="*60)
    
    documents = [
        {
            "doc_id": "automation_living_room_motion",
            "content": "When motion is detected in the living room after sunset, automatically turn on the ceiling lights to 50% brightness for 10 minutes.",
            "metadata": {
                "room": "living_room",
                "type": "automation",
                "trigger": "motion",
                "action": "light_on"
            }
        },
        {
            "doc_id": "automation_bedroom_evening",
            "content": "Evening routine: At 9 PM, dim bedroom lights to 20%, close blinds, and set thermostat to 18 degrees for sleep.",
            "metadata": {
                "room": "bedroom",
                "type": "automation",
                "trigger": "time",
                "action": "evening_routine"
            }
        },
        {
            "doc_id": "automation_kitchen_presence",
            "content": "Kitchen under-cabinet lighting turns on when presence is detected between 6 AM and 11 PM.",
            "metadata": {
                "room": "kitchen",
                "type": "automation",
                "trigger": "presence",
                "action": "light_on"
            }
        }
    ]
    
    for doc in documents:
        result = client.add_document(
            doc_id=doc["doc_id"],
            content=doc["content"],
            metadata=doc["metadata"]
        )
        print(f"Indexed: {doc['doc_id']} ({result.get('tokens', 0)} tokens)")
    
    # Show stats
    stats = client.get_stats()
    print(f"\nIndex Stats:")
    print(f"  Documents: {stats['stats']['num_documents']}")
    print(f"  Terms: {stats['stats']['num_terms']}")
    print(f"  Avg Doc Length: {stats['stats']['avg_doc_length']:.1f}")


def example_filtered_search(client: RAGSearchExample):
    """Example: Search with metadata filters."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Filtered Search")
    print("="*60)
    
    # First index some documents
    example_index_documents(client)
    
    query = "lighting automation"
    filters = {"room": "living_room"}
    
    print(f"\nQuery: '{query}'")
    print(f"Filters: {filters}")
    
    results = client.search(query, top_k=5)
    
    print(f"\nFound {results['count']} results")
    
    for i, result in enumerate(results['results'], 1):
        print(f"\n{i}. [Score: {result['score']:.4f}]")
        print(f"   Room: {result.get('metadata', {}).get('room', 'N/A')}")
        print(f"   Type: {result.get('metadata', {}).get('type', 'N/A')}")
        print(f"   Content: {result['content'][:120]}...")


def example_delete_document(client: RAGSearchExample):
    """Example: Delete document from index."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Delete Document")
    print("="*60)
    
    doc_id = "automation_living_room_motion"
    print(f"Deleting document: {doc_id}")
    
    result = client.delete_document(doc_id)
    print(f"Deleted: {result.get('deleted', False)}")
    
    # Show updated stats
    stats = client.get_stats()
    print(f"Remaining documents: {stats['stats']['num_documents']}")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("PILOTSUITE RAG HYBRID SEARCH API EXAMPLES")
    print("="*60)
    
    # Initialize client
    # Replace with your actual token
    TOKEN = "your-api-token-here"
    client = RAGSearchExample(
        base_url="http://localhost:8909",
        token=TOKEN
    )
    
    try:
        # Run examples
        example_basic_search(client)
        example_multi_query_search(client)
        example_index_documents(client)
        example_filtered_search(client)
        example_delete_document(client)
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60 + "\n")
        
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection error: {e}")
        print("Make sure PilotSuite Core is running on http://localhost:8909")
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP error: {e}")
        print(f"Response: {e.response.text}")
        print("Check your API token and permissions")


if __name__ == "__main__":
    main()
