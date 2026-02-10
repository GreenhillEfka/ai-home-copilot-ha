"""
Brain Graph service providing high-level graph operations.
"""

import time
from typing import Dict, List, Optional, Any, Tuple

from .model import GraphNode, GraphEdge, NodeKind, EdgeType
from .store import GraphStore


class BrainGraphService:
    """High-level service for brain graph operations."""
    
    def __init__(
        self, 
        store: Optional[GraphStore] = None,
        node_half_life_hours: float = 24.0,
        edge_half_life_hours: float = 12.0
    ):
        self.store = store or GraphStore()
        self.node_half_life_hours = node_half_life_hours
        self.edge_half_life_hours = edge_half_life_hours
    
    def touch_node(
        self,
        node_id: str,
        delta: float = 1.0,
        label: Optional[str] = None,
        kind: Optional[NodeKind] = None,
        domain: Optional[str] = None,
        meta_patch: Optional[Dict[str, Any]] = None,
        source: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None
    ) -> GraphNode:
        """Touch a node, updating its score and metadata."""
        now_ms = int(time.time() * 1000)
        
        # Get existing node or create new one
        existing_node = self.store.get_node(node_id)
        
        if existing_node:
            # Update existing node
            new_score = max(0.0, existing_node.effective_score(now_ms, self.node_half_life_hours) + delta)
            new_label = label or existing_node.label
            new_kind = kind or existing_node.kind
            new_domain = domain or existing_node.domain
            new_source = source or existing_node.source
            new_tags = tags or existing_node.tags
            
            # Merge meta
            new_meta = existing_node.meta.copy() if existing_node.meta else {}
            if meta_patch:
                new_meta.update(meta_patch)
        else:
            # Create new node  
            if not label or not kind:
                raise ValueError("label and kind are required for new nodes")
                
            new_score = max(0.0, delta)
            new_label = label
            new_kind = kind
            new_domain = domain
            new_source = source
            new_tags = tags
            new_meta = meta_patch or {}
        
        # Create updated node
        updated_node = GraphNode(
            id=node_id,
            kind=new_kind,
            label=new_label,
            updated_at_ms=now_ms,
            score=new_score,
            domain=new_domain,
            source=new_source,
            tags=new_tags,
            meta=new_meta,
        )
        
        # Store the node
        self.store.upsert_node(updated_node)
        
        # Trigger pruning periodically (every ~100 operations)
        import random
        if random.randint(1, 100) == 1:
            self.store.prune_graph(now_ms)
        
        return updated_node
    
    def touch_edge(
        self,
        from_node: str,
        edge_type: EdgeType,
        to_node: str,
        delta: float = 1.0,
        meta_patch: Optional[Dict[str, Any]] = None,
        evidence: Optional[Dict[str, str]] = None
    ) -> GraphEdge:
        """Touch an edge, updating its weight and metadata."""
        now_ms = int(time.time() * 1000)
        
        edge_id = GraphEdge.create_id(from_node, edge_type, to_node)
        
        # Get existing edge or create new one
        existing_edges = self.store.get_edges(from_node=from_node, to_node=to_node, edge_types=[edge_type])
        existing_edge = next((e for e in existing_edges if e.id == edge_id), None)
        
        if existing_edge:
            # Update existing edge
            new_weight = max(0.0, existing_edge.effective_weight(now_ms, self.edge_half_life_hours) + delta)
            new_evidence = evidence or existing_edge.evidence
            
            # Merge meta
            new_meta = existing_edge.meta.copy() if existing_edge.meta else {}
            if meta_patch:
                new_meta.update(meta_patch)
        else:
            # Create new edge
            new_weight = max(0.0, delta)
            new_evidence = evidence
            new_meta = meta_patch or {}
        
        # Create updated edge
        updated_edge = GraphEdge(
            id=edge_id,
            from_node=from_node,
            to_node=to_node,
            edge_type=edge_type,
            updated_at_ms=now_ms,
            weight=new_weight,
            evidence=new_evidence,
            meta=new_meta,
        )
        
        # Store the edge
        self.store.upsert_edge(updated_edge)
        
        return updated_edge
    
    def link(
        self,
        from_node: str,
        edge_type: EdgeType, 
        to_node: str,
        initial_weight: float = 1.0,
        evidence: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> GraphEdge:
        """Create or strengthen a link between nodes."""
        return self.touch_edge(
            from_node=from_node,
            edge_type=edge_type,
            to_node=to_node,
            delta=initial_weight,
            evidence=evidence,
            meta_patch=meta
        )
    
    def get_graph_state(
        self,
        kinds: Optional[List[NodeKind]] = None,
        domains: Optional[List[str]] = None,
        center_node: Optional[str] = None,
        hops: int = 1,
        limit_nodes: Optional[int] = None,
        limit_edges: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get current graph state with optional filtering."""
        now_ms = int(time.time() * 1000)
        
        if center_node:
            # Get neighborhood
            nodes, edges = self.store.get_neighborhood(
                center_node=center_node,
                hops=hops,
                max_nodes=limit_nodes,
                max_edges=limit_edges
            )
        else:
            # Get filtered nodes
            nodes = self.store.get_nodes(
                kinds=kinds,
                domains=domains,
                limit=limit_nodes
            )
            
            # Get edges between these nodes
            node_ids = {node.id for node in nodes}
            all_edges = []
            
            for node in nodes:
                node_edges = self.store.get_edges(from_node=node.id)
                for edge in node_edges:
                    if edge.to_node in node_ids and edge not in all_edges:
                        all_edges.append(edge)
            
            # Apply edge limit
            if limit_edges and len(all_edges) > limit_edges:
                all_edges = sorted(all_edges, key=lambda e: e.effective_weight(now_ms), reverse=True)[:limit_edges]
                
            edges = all_edges
        
        # Convert to serializable format
        return {
            "version": 1,
            "generated_at_ms": now_ms,
            "limits": {
                "nodes_max": self.store.max_nodes,
                "edges_max": self.store.max_edges,
            },
            "nodes": [
                {
                    "id": node.id,
                    "kind": node.kind,
                    "label": node.label,
                    "domain": node.domain,
                    "score": node.effective_score(now_ms, self.node_half_life_hours),
                    "updated_at_ms": node.updated_at_ms,
                    "source": node.source,
                    "tags": node.tags,
                    "meta": node.meta,
                }
                for node in nodes
            ],
            "edges": [
                {
                    "id": edge.id,
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "type": edge.edge_type,
                    "weight": edge.effective_weight(now_ms, self.edge_half_life_hours),
                    "updated_at_ms": edge.updated_at_ms,
                    "evidence": edge.evidence,
                    "meta": edge.meta,
                }
                for edge in edges
            ]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current graph statistics."""
        store_stats = self.store.get_stats()
        
        return {
            **store_stats,
            "config": {
                "node_half_life_hours": self.node_half_life_hours,
                "edge_half_life_hours": self.edge_half_life_hours,
                "node_min_score": self.store.node_min_score,
                "edge_min_weight": self.store.edge_min_weight,
            }
        }
    
    def prune_now(self) -> Dict[str, int]:
        """Manually trigger graph pruning."""
        return self.store.prune_graph()
    
    def process_ha_event(self, event_data: Dict[str, Any]):
        """Process a Home Assistant event and update the graph."""
        # This is a placeholder for event processing logic
        # Will be implemented when we wire the event forwarder
        
        event_type = event_data.get("event_type", "")
        
        if event_type == "state_changed":
            self._process_state_change(event_data)
        elif event_type == "call_service":
            self._process_service_call(event_data)
    
    def _process_state_change(self, event_data: Dict[str, Any]):
        """Process a state change event."""
        # Extract entity info
        entity_id = event_data.get("data", {}).get("entity_id", "")
        if not entity_id:
            return
            
        # Create/update entity node
        domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
        
        self.touch_node(
            node_id=f"ha.entity:{entity_id}",
            kind="entity",
            label=entity_id.split(".")[-1].replace("_", " ").title(),
            domain=domain,
            source={"system": "ha", "name": "state_changed"}
        )
        
        # Extract zone/area info if available
        # This would need HA area registry integration
        
    def _process_service_call(self, event_data: Dict[str, Any]):
        """Process a service call event."""
        service_data = event_data.get("data", {})
        domain = service_data.get("domain", "")
        service = service_data.get("service", "")
        
        if not domain or not service:
            return
            
        # Create/update service node
        service_id = f"{domain}.{service}"
        self.touch_node(
            node_id=f"ha.service:{service_id}",
            kind="concept", 
            label=f"{domain.title()} {service.replace('_', ' ').title()}",
            source={"system": "ha", "name": "call_service"}
        )
        
        # Link to target entities if present
        target_entities = service_data.get("service_data", {}).get("entity_id", [])
        if isinstance(target_entities, str):
            target_entities = [target_entities]
            
        for entity_id in target_entities:
            if isinstance(entity_id, str):
                self.link(
                    from_node=f"ha.service:{service_id}",
                    edge_type="affects",
                    to_node=f"ha.entity:{entity_id}",
                    evidence={"kind": "service_call", "ref": service_id}
                )