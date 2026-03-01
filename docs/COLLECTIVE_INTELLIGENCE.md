# Collective Intelligence API Documentation

**Phase 6 Feature** | **Version:** 1.0.0 | **Last Updated:** 2026-03-01

Comprehensive API documentation for the Collective Intelligence (Federated Learning) system enabling privacy-preserving knowledge sharing across multiple home nodes.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [GET /api/v1/federated](#get-apiv1federated)
  - [POST /api/v1/federated/start](#post-apiv1federatedstart)
  - [POST /api/v1/federated/stop](#post-apiv1federatedstop)
  - [POST /api/v1/federated/register](#post-apiv1federatedregister)
  - [POST /api/v1/federated/update](#post-apiv1federatedupdate)
  - [POST /api/v1/federated/round](#post-apiv1federatedround)
  - [POST /api/v1/federated/aggregate](#post-apiv1federatedaggregate)
  - [POST /api/v1/federated/knowledge](#post-apiv1federatedknowledge)
  - [POST /api/v1/federated/knowledge/:id/transfer](#post-apiv1federatedknowledgeidtransfer)
  - [GET /api/v1/federated/rounds](#get-apiv1federatedrounds)
  - [GET /api/v1/federated/models](#get-apiv1federatedmodels)
  - [GET /api/v1/federated/knowledge-base](#get-apiv1federatedknowledge-base)
  - [GET /api/v1/federated/statistics](#get-apiv1federatedstatistics)
  - [POST /api/v1/federated/save](#post-apiv1federatedsave)
  - [POST /api/v1/federated/load](#post-apiv1federatedload)
- [Error Codes](#error-codes)
- [Python SDK Examples](#python-sdk-examples)

---

## Overview

The Collective Intelligence API implements federated learning for home automation systems, enabling multiple nodes to collaboratively learn and share knowledge while preserving privacy.

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Node** | A home automation instance participating in federated learning |
| **Round** | A federated learning iteration with aggregation |
| **Update** | Local model update from a node |
| **Knowledge** | Extracted patterns/rules for transfer |
| **Aggregation** | Combining updates from multiple nodes |
| **Privacy Loss** | Differential privacy budget consumption |

### Features

- 🔒 **Privacy-Preserving:** Differential privacy with configurable epsilon
- 🔄 **Federated Rounds:** Synchronized learning iterations
- 📦 **Knowledge Transfer:** Extract and share specific patterns
- 📊 **Statistics:** Comprehensive monitoring and metrics
- 💾 **Persistence:** Save/load system state

### Default Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_epsilon` | 1.0 | Maximum privacy loss per node |
| `aggregation_method` | "weighted_avg" | Model aggregation strategy |
| `min_participants` | 2 | Minimum nodes for aggregation |
| `knowledge_confidence_threshold` | 0.7 | Minimum confidence for knowledge extraction |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Federated Coordinator                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Round     │  │  Knowledge  │  │  Privacy    │         │
│  │  Manager    │  │   Extractor │  │  Budget     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Home Node   │   │   Home Node   │   │   Home Node   │
│     A         │   │     B         │   │     C         │
│               │   │               │   │               │
│ - Local Model │   │ - Local Model │   │ - Local Model │
│ - Updates     │   │ - Updates     │   │ - Updates     │
│ - Knowledge   │   │ - Knowledge   │   │ - Knowledge   │
└───────────────┘   └───────────────┘   └───────────────┘
```

---

## Authentication

All endpoints require authentication:

```http
X-Auth-Token: your-api-token-here
```

or

```http
Authorization: Bearer your-api-token-here
```

**Authentication Failure:**

```json
{
  "error": "unauthorized",
  "message": "Valid X-Auth-Token or Bearer token required"
}
```

**HTTP Status:** `401 Unauthorized`

---

## Endpoints

### GET /api/v1/federated

Get federated learning system status.

#### Description

Returns the current status of the federated learning system including active nodes, rounds, and privacy budget.

#### Request Format

**Endpoint:** `GET /api/v1/federated`

**Headers:**
```http
X-Auth-Token: your-api-token
```

#### Response Format

**Success Response (200 OK):**

```json
{
  "status": "active",
  "node_id": "home_andreas",
  "registered_nodes": 3,
  "active_round": "round_2026_03_01_001",
  "total_rounds_completed": 47,
  "privacy_budget": {
    "epsilon_used": 0.342,
    "epsilon_remaining": 0.658,
    "max_epsilon": 1.0
  },
  "last_aggregation": "2026-03-01T10:00:00Z",
  "knowledge_items": 156,
  "aggregated_models": 12
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `401` | Unauthorized |
| `503` | Service not initialized |
| `500` | Internal Server Error |

#### Python Code Example

```python
import requests
from typing import Dict, Any


class FederatedLearningClient:
    """Client for Collective Intelligence API."""
    
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            'X-Auth-Token': api_token
        })
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get federated learning system status.
        
        Returns:
            Status dictionary with node count, rounds, privacy budget
        """
        response = self.session.get(
            f'{self.base_url}/api/v1/federated',
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503:
            raise RuntimeError("Federated service not initialized")
        else:
            response.raise_for_status()


# Usage Example
if __name__ == '__main__':
    client = FederatedLearningClient(
        base_url='http://localhost:8123',
        api_token='your-api-token-here'
    )
    
    status = client.get_status()
    
    print("🔮 Federated Learning Status")
    print(f"   Status: {status['status']}")
    print(f"   Registered nodes: {status['registered_nodes']}")
    print(f"   Active round: {status['active_round']}")
    print(f"   Privacy budget: {status['privacy_budget']['epsilon_remaining']:.3f} remaining")
```

---

### POST /api/v1/federated/start

Start the federated learning service.

#### Request Format

**Endpoint:** `POST /api/v1/federated/start`

**Headers:**
```http
X-Auth-Token: your-api-token
```

#### Response Format

```json
{
  "ok": true,
  "message": "Federated service started"
}
```

---

### POST /api/v1/federated/stop

Stop the federated learning service.

#### Response Format

```json
{
  "ok": true,
  "message": "Federated service stopped"
}
```

---

### POST /api/v1/federated/register

Register a new home node for federated learning.

#### Description

Registers a node to participate in federated learning with specified privacy constraints.

#### Request Format

**Endpoint:** `POST /api/v1/federated/register`

**Headers:**
```http
Content-Type: application/json
X-Auth-Token: your-api-token
```

**Body:**
```json
{
  "node_id": "home_andreas",
  "max_epsilon": 1.0
}
```

**Request Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `node_id` | string | ✅ Yes | - | Unique node identifier |
| `max_epsilon` | float | ❌ No | 1.0 | Maximum privacy loss (differential privacy) |

#### Response Format

**Success Response (200 OK):**

```json
{
  "ok": true,
  "node_id": "home_andreas",
  "message": "Node registered"
}
```

#### Python Code Example

```python
def register_node_example(client: FederatedLearningClient):
    """Example: Register a node."""
    
    payload = {
        'node_id': 'home_vacation',
        'max_epsilon': 0.8
    }
    
    response = client.session.post(
        f'{client.base_url}/api/v1/federated/register',
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Node registered: {result['node_id']}")
        print(f"   Max epsilon: {payload['max_epsilon']}")
    else:
        print(f"❌ Failed: {response.status_code}")
```

---

### POST /api/v1/federated/update

Submit a local model update from a node.

#### Description

Submits locally computed model weights and metrics for aggregation.

#### Request Format

**Endpoint:** `POST /api/v1/federated/update`

**Body:**
```json
{
  "node_id": "home_andreas",
  "weights": {
    "layer_1": [0.1, 0.2, 0.3, ...],
    "layer_2": [0.4, 0.5, 0.6, ...]
  },
  "metrics": {
    "accuracy": 0.94,
    "loss": 0.23,
    "samples": 1500
  }
}
```

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `node_id` | string | ✅ Yes | Node identifier |
| `weights` | object | ✅ Yes | Model weights (flattened or structured) |
| `metrics` | object | ❌ No | Training metrics |

#### Response Format

```json
{
  "ok": true,
  "update_id": "update_2026_03_01_001",
  "timestamp": "2026-03-01T14:30:00Z"
}
```

---

### POST /api/v1/federated/round

Start a new federated learning round.

#### Description

Initiates a new federated learning round, collecting updates from registered nodes.

#### Request Format

**Endpoint:** `POST /api/v1/federated/round`

#### Response Format

```json
{
  "ok": true,
  "round_id": "round_2026_03_01_002"
}
```

#### Python Code Example

```python
def start_round_example(client: FederatedLearningClient):
    """Example: Start a federated learning round."""
    
    response = client.session.post(
        f'{client.base_url}/api/v1/federated/round'
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"🔄 Round started: {result['round_id']}")
```

---

### POST /api/v1/federated/aggregate

Execute aggregation for a round.

#### Description

Aggregates model updates from all participating nodes using weighted averaging with differential privacy.

#### Request Format

**Endpoint:** `POST /api/v1/federated/aggregate`

**Body:**
```json
{
  "round_id": "round_2026_03_01_002"
}
```

#### Response Format

```json
{
  "ok": true,
  "model_version": "v2026_03_01_002",
  "participants": 3,
  "metrics": {
    "global_accuracy": 0.96,
    "global_loss": 0.18,
    "convergence": 0.92
  },
  "privacy_loss": 0.023
}
```

#### Python Code Example

```python
def aggregate_round_example(client: FederatedLearningClient, round_id: str):
    """Example: Execute aggregation for a round."""
    
    payload = {'round_id': round_id}
    
    response = client.session.post(
        f'{client.base_url}/api/v1/federated/aggregate',
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Aggregation complete")
        print(f"   Model version: {result['model_version']}")
        print(f"   Participants: {result['participants']}")
        print(f"   Privacy loss: {result['privacy_loss']:.4f}")
```

---

### POST /api/v1/federated/knowledge

Extract knowledge from a node for transfer.

#### Description

Extracts specific knowledge (patterns, rules, embeddings) from a node for potential transfer to other nodes.

#### Request Format

**Endpoint:** `POST /api/v1/federated/knowledge`

**Body:**
```json
{
  "node_id": "home_andreas",
  "knowledge_type": "automation_pattern",
  "payload": {
    "pattern_id": "pattern_001",
    "rule": "IF motion THEN light ON",
    "confidence": 0.89
  },
  "confidence": 0.89
}
```

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `node_id` | string | ✅ Yes | Source node identifier |
| `knowledge_type` | string | ✅ Yes | Type: `automation_pattern`, `embedding`, `rule`, `statistic` |
| `payload` | object | ✅ Yes | Knowledge data |
| `confidence` | float | ❌ No | Confidence score (0.0-1.0) |

#### Response Format

```json
{
  "ok": true,
  "knowledge_id": "know_abc123xyz",
  "knowledge_hash": "sha256:abcd1234..."
}
```

---

### POST /api/v1/federated/knowledge/:id/transfer

Transfer knowledge to another node.

#### Description

Transfers extracted knowledge from one node to a target node.

#### Request Format

**Endpoint:** `POST /api/v1/federated/knowledge/:knowledge_id/transfer`

**Body:**
```json
{
  "target_node_id": "home_vacation"
}
```

#### Response Format

```json
{
  "ok": true,
  "knowledge_id": "know_abc123xyz",
  "target_node_id": "home_vacation"
}
```

#### Python Code Example

```python
def transfer_knowledge_example(client: FederatedLearningClient):
    """Example: Transfer knowledge between nodes."""
    
    # First extract knowledge
    extract_payload = {
        'node_id': 'home_andreas',
        'knowledge_type': 'automation_pattern',
        'payload': {
            'pattern': 'light_on_at_sunset',
            'entities': ['light.wohnzimmer', 'light.kuche']
        },
        'confidence': 0.92
    }
    
    extract_response = client.session.post(
        f'{client.base_url}/api/v1/federated/knowledge',
        json=extract_payload
    )
    
    if extract_response.status_code == 200:
        knowledge_id = extract_response.json()['knowledge_id']
        print(f"✅ Knowledge extracted: {knowledge_id}")
        
        # Transfer to target node
        transfer_payload = {
            'target_node_id': 'home_vacation'
        }
        
        transfer_response = client.session.post(
            f'{client.base_url}/api/v1/federated/knowledge/{knowledge_id}/transfer',
            json=transfer_payload
        )
        
        if transfer_response.status_code == 200:
            print(f"✅ Knowledge transferred to home_vacation")
```

---

### GET /api/v1/federated/rounds

Get history of federated rounds.

#### Response Format

```json
{
  "count": 47,
  "rounds": [
    {
      "round_id": "round_2026_03_01_001",
      "started_at": "2026-03-01T10:00:00Z",
      "completed_at": "2026-03-01T10:05:00Z",
      "participants": 3,
      "model_version": "v2026_03_01_001",
      "metrics": {
        "accuracy": 0.95,
        "loss": 0.21
      },
      "privacy_loss": 0.021
    }
  ]
}
```

---

### GET /api/v1/federated/models

Get all aggregated models.

#### Response Format

```json
{
  "count": 12,
  "models": {
    "v2026_03_01_001": {
      "version": "v2026_03_01_001",
      "created_at": "2026-03-01T10:05:00Z",
      "participants": 3,
      "metrics": {...},
      "size_bytes": 1048576
    }
  }
}
```

---

### GET /api/v1/federated/knowledge-base

Get the knowledge transfer base.

#### Response Format

```json
{
  "count": 156,
  "items": {
    "know_001": {
      "knowledge_id": "know_001",
      "knowledge_type": "automation_pattern",
      "source_node": "home_andreas",
      "confidence": 0.89,
      "transferred_to": ["home_vacation", "home_office"],
      "created_at": "2026-02-28T14:00:00Z"
    }
  }
}
```

---

### GET /api/v1/federated/statistics

Get comprehensive federated learning statistics.

#### Response Format

```json
{
  "system_status": "healthy",
  "uptime_hours": 720,
  "total_nodes": 5,
  "active_nodes": 3,
  "total_rounds": 47,
  "successful_aggregations": 45,
  "failed_aggregations": 2,
  "total_knowledge_items": 156,
  "knowledge_transfers": 89,
  "privacy_budget": {
    "total_epsilon": 1.0,
    "used_epsilon": 0.342,
    "remaining_epsilon": 0.658
  },
  "performance": {
    "avg_round_duration_sec": 45.3,
    "avg_aggregation_time_ms": 234,
    "model_size_avg_bytes": 1048576
  },
  "node_statistics": [
    {
      "node_id": "home_andreas",
      "updates_submitted": 47,
      "knowledge_contributed": 23,
      "last_active": "2026-03-01T14:00:00Z"
    }
  ]
}
```

#### Python Code Example

```python
def get_statistics_example(client: FederatedLearningClient):
    """Example: Get comprehensive statistics."""
    
    response = client.session.get(
        f'{client.base_url}/api/v1/federated/statistics'
    )
    
    if response.status_code == 200:
        stats = response.json()
        print("📊 Federated Learning Statistics")
        print(f"   System: {stats['system_status']}")
        print(f"   Uptime: {stats['uptime_hours']}h")
        print(f"   Active nodes: {stats['active_nodes']}/{stats['total_nodes']}")
        print(f"   Rounds: {stats['total_rounds']} ({stats['successful_aggregations']} successful)")
        print(f"   Knowledge: {stats['total_knowledge_items']} items, {stats['knowledge_transfers']} transfers")
        print(f"   Privacy: {stats['privacy_budget']['remaining_epsilon']:.3f} epsilon remaining")
```

---

### POST /api/v1/federated/save

Save system state to file.

#### Request Format

**Endpoint:** `POST /api/v1/federated/save`

**Body:**
```json
{
  "path": "/config/.copilot/federated_state.json"
}
```

#### Response Format

```json
{
  "ok": true,
  "path": "/config/.copilot/federated_state.json"
}
```

---

### POST /api/v1/federated/load

Load system state from file.

#### Request Format

**Endpoint:** `POST /api/v1/federated/load`

**Body:**
```json
{
  "path": "/config/.copilot/federated_state.json"
}
```

#### Response Format

```json
{
  "ok": true,
  "path": "/config/.copilot/federated_state.json"
}
```

---

## Error Codes

### Standard HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| `200` | OK | Request successful |
| `400` | Bad Request | Invalid request format |
| `401` | Unauthorized | Invalid authentication |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource not found |
| `500` | Internal Server Error | Server error |
| `503` | Service Unavailable | Federated service not initialized |

---

## Python SDK Examples

### Complete Usage Example

```python
#!/usr/bin/env python3
"""
Collective Intelligence API - Complete Usage Examples
"""

import requests
import time
from typing import Dict, Any, List, Optional


class CollectiveIntelligenceClient:
    """Complete client for Collective Intelligence (Federated Learning) API."""
    
    def __init__(self, base_url: str, api_token: str, timeout: int = 60):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.timeout = timeout
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-Auth-Token': api_token
        })
    
    # ==================== System Control ====================
    
    def get_status(self) -> Dict[str, Any]:
        """Get federated learning system status."""
        response = self.session.get(
            f'{self.base_url}/api/v1/federated',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def start_service(self) -> Dict[str, Any]:
        """Start the federated learning service."""
        response = self.session.post(
            f'{self.base_url}/api/v1/federated/start',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def stop_service(self) -> Dict[str, Any]:
        """Stop the federated learning service."""
        response = self.session.post(
            f'{self.base_url}/api/v1/federated/stop',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Node Management ====================
    
    def register_node(
        self,
        node_id: str,
        max_epsilon: float = 1.0
    ) -> Dict[str, Any]:
        """Register a node for federated learning."""
        payload = {
            'node_id': node_id,
            'max_epsilon': max_epsilon
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/federated/register',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def submit_update(
        self,
        node_id: str,
        weights: Dict[str, Any],
        metrics: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Submit a local model update."""
        payload = {
            'node_id': node_id,
            'weights': weights,
            'metrics': metrics or {}
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/federated/update',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Federated Rounds ====================
    
    def start_round(self) -> Dict[str, Any]:
        """Start a new federated learning round."""
        response = self.session.post(
            f'{self.base_url}/api/v1/federated/round',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def aggregate_round(self, round_id: str) -> Dict[str, Any]:
        """Execute aggregation for a round."""
        payload = {'round_id': round_id}
        
        response = self.session.post(
            f'{self.base_url}/api/v1/federated/aggregate',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_round_history(self) -> Dict[str, Any]:
        """Get history of federated rounds."""
        response = self.session.get(
            f'{self.base_url}/api/v1/federated/rounds',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_models(self) -> Dict[str, Any]:
        """Get all aggregated models."""
        response = self.session.get(
            f'{self.base_url}/api/v1/federated/models',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Knowledge Management ====================
    
    def extract_knowledge(
        self,
        node_id: str,
        knowledge_type: str,
        payload: Dict[str, Any],
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """Extract knowledge from a node."""
        payload_data = {
            'node_id': node_id,
            'knowledge_type': knowledge_type,
            'payload': payload,
            'confidence': confidence
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/federated/knowledge',
            json=payload_data,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def transfer_knowledge(
        self,
        knowledge_id: str,
        target_node_id: str
    ) -> Dict[str, Any]:
        """Transfer knowledge to another node."""
        payload = {'target_node_id': target_node_id}
        
        response = self.session.post(
            f'{self.base_url}/api/v1/federated/knowledge/{knowledge_id}/transfer',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_knowledge_base(self) -> Dict[str, Any]:
        """Get the knowledge transfer base."""
        response = self.session.get(
            f'{self.base_url}/api/v1/federated/knowledge-base',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Statistics & Persistence ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        response = self.session.get(
            f'{self.base_url}/api/v1/federated/statistics',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def save_state(self, path: str = None) -> Dict[str, Any]:
        """Save system state to file."""
        payload = {'path': path or '/config/.copilot/federated_state.json'}
        
        response = self.session.post(
            f'{self.base_url}/api/v1/federated/save',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def load_state(self, path: str = None) -> Dict[str, Any]:
        """Load system state from file."""
        payload = {'path': path or '/config/.copilot/federated_state.json'}
        
        response = self.session.post(
            f'{self.base_url}/api/v1/federated/load',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()


# ==================== Example Usage ====================

if __name__ == '__main__':
    BASE_URL = 'http://localhost:8123'
    API_TOKEN = 'your-api-token-here'
    
    client = CollectiveIntelligenceClient(BASE_URL, API_TOKEN)
    
    print("=" * 60)
    print("Collective Intelligence API - Usage Examples")
    print("=" * 60)
    
    # 1. Check system status
    print("\n1. 🔮 System Status")
    print("-" * 40)
    status = client.get_status()
    print(f"Status: {status['status']}")
    print(f"Nodes: {status['registered_nodes']}")
    print(f"Active round: {status['active_round']}")
    
    # 2. Register nodes
    print("\n2. 📝 Register Nodes")
    print("-" * 40)
    
    nodes = [
        ('home_andreas', 1.0),
        ('home_vacation', 0.8),
        ('home_office', 0.9)
    ]
    
    for node_id, epsilon in nodes:
        try:
            result = client.register_node(node_id, max_epsilon=epsilon)
            print(f"✅ Registered: {result['node_id']}")
        except Exception as e:
            print(f"⚠️  {node_id}: {e}")
    
    # 3. Start federated round
    print("\n3. 🔄 Start Federated Round")
    print("-" * 40)
    round_result = client.start_round()
    round_id = round_result['round_id']
    print(f"Round started: {round_id}")
    
    # 4. Simulate node updates
    print("\n4. 📤 Submit Node Updates")
    print("-" * 40)
    
    for node_id, _ in nodes:
        update_result = client.submit_update(
            node_id=node_id,
            weights={'layer_1': [0.1, 0.2, 0.3]},
            metrics={'accuracy': 0.94, 'loss': 0.23}
        )
        print(f"✅ Update from {node_id}: {update_result['update_id']}")
    
    # 5. Execute aggregation
    print("\n5. 🔀 Execute Aggregation")
    print("-" * 40)
    agg_result = client.aggregate_round(round_id)
    print(f"Model version: {agg_result['model_version']}")
    print(f"Participants: {agg_result['participants']}")
    print(f"Privacy loss: {agg_result['privacy_loss']:.4f}")
    
    # 6. Extract and transfer knowledge
    print("\n6. 🧠 Knowledge Transfer")
    print("-" * 40)
    
    knowledge_result = client.extract_knowledge(
        node_id='home_andreas',
        knowledge_type='automation_pattern',
        payload={
            'pattern': 'light_on_at_sunset',
            'entities': ['light.wohnzimmer']
        },
        confidence=0.92
    )
    knowledge_id = knowledge_result['knowledge_id']
    print(f"Knowledge extracted: {knowledge_id}")
    
    transfer_result = client.transfer_knowledge(
        knowledge_id=knowledge_id,
        target_node_id='home_vacation'
    )
    print(f"Knowledge transferred: {transfer_result['ok']}")
    
    # 7. Get statistics
    print("\n7. 📊 Statistics")
    print("-" * 40)
    stats = client.get_statistics()
    print(f"System: {stats['system_status']}")
    print(f"Total rounds: {stats['total_rounds']}")
    print(f"Knowledge items: {stats['total_knowledge_items']}")
    print(f"Privacy remaining: {stats['privacy_budget']['remaining_epsilon']:.3f}")
    
    # 8. Save state
    print("\n8. 💾 Save State")
    print("-" * 40)
    save_result = client.save_state()
    print(f"State saved to: {save_result['path']}")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
```

---

**Documentation Version:** 1.0.0  
**Last Updated:** 2026-03-01  
**Maintained By:** PilotSuite Core Team
