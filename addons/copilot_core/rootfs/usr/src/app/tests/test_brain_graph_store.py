"""Brain Graph Store Tests."""

import tempfile
import unittest
import os
import json

try:
    from copilot_core.brain_graph.store import BrainGraphStore
    from copilot_core.brain_graph.model import GraphNode, GraphEdge
except ModuleNotFoundError:
    BrainGraphStore = None


class TestBrainGraphStore(unittest.TestCase):
    """Test BrainGraphStore persistence and basic operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmpdb = os.path.join(self.tmpdir.name, "graph.db")

    def tearDown(self):
        """Clean up test fixtures."""
        self.tmpdir.cleanup()

    def test_store_init(self):
        """Test store initialization."""
        if BrainGraphStore is None:
            self.skipTest("BrainGraphStore not available")
        store = BrainGraphStore(db_path=self.tmpdb)
        self.assertIsNotNone(store)

    def test_store_persistence_disabled(self):
        """Test store with persistence disabled."""
        if BrainGraphStore is None:
            self.skipTest("BrainGraphStore not available")
        store = BrainGraphStore(db_path=self.tmpdb, persist=False)
        self.assertIsNotNone(store)

    def test_store_save_and_load(self):
        """Test save and load functionality."""
        if BrainGraphStore is None:
            self.skipTest("BrainGraphStore not available")
        store = BrainGraphStore(db_path=self.tmpdb, persist=True)
        
        # Add a node
        node = GraphNode(
            id="test:node1",
            kind="entity",
            label="Test Node",
            updated_at_ms=1234567890,
            score=1.0,
            domain="light",
        )
        store.nodes[node.id] = node
        
        # Add an edge
        edge = GraphEdge(
            id="e:test",
            from_id="test:node1",
            to_id="test:node2",
            type="controls",
            updated_at_ms=1234567890,
            weight=0.5,
        )
        store.edges[edge.id] = edge
        
        # Save
        store.save_best_effort()
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.tmpdb + ".json"))
        
        # Load into new store
        store2 = BrainGraphStore(db_path=self.tmpdb, persist=True)
        self.assertIn("test:node1", store2.nodes)
        self.assertIn("e:test", store2.edges)

    def test_store_load_empty(self):
        """Test loading empty/non-existent store."""
        if BrainGraphStore is None:
            self.skipTest("BrainGraphStore not available")
        # Load from non-existent file - should not crash
        store = BrainGraphStore(db_path="/nonexistent/path.db", persist=True)
        self.assertIsNotNone(store)

    def test_store_max_nodes_edges(self):
        """Test store limits."""
        if BrainGraphStore is None:
            self.skipTest("BrainGraphStore not available")
        store = BrainGraphStore(
            db_path=self.tmpdb,
            max_nodes=10,
            max_edges=20,
        )
        self.assertEqual(store.max_nodes, 10)
        self.assertEqual(store.max_edges, 20)


class TestBrainGraphStoreIntegration(unittest.TestCase):
    """Integration tests for BrainGraphStore."""

    def setUp(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tmpdir.cleanup()

    def test_store_with_service(self):
        """Test BrainGraphStore with BrainGraphService."""
        try:
            from copilot_core.brain_graph.service import BrainGraphService
            from copilot_core.brain_graph.provider import get_graph_service
        except ModuleNotFoundError:
            self.skipTest("BrainGraphService not available")
        
        db_path = os.path.join(self.tmpdir.name, "graph.db")
        store = BrainGraphStore(db_path=db_path)
        svc = BrainGraphService(store)
        
        # Test touch_node
        node = svc.touch_node("test:entity", kind="entity", label="Test Entity")
        self.assertEqual(node.id, "test:entity")
        
        # Test touch_edge
        edge = svc.touch_edge("test:entity", "controls", "test:zone")
        self.assertEqual(edge.from_id, "test:entity")


if __name__ == "__main__":
    unittest.main()
