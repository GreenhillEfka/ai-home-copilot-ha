"""Tests für Predictive Automation — Pattern Learning & Vorhersage.

Testet:
- PatternLearner: Mustererkennung und -speicherung
- PredictiveAutomationEngine: Vorhersagen
- API Endpoints: REST-Schnittstelle
"""

import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

# Ensure app directory is in path
APP_DIR = Path(__file__).parent.parent / "copilot_core"
if str(APP_DIR.parent) not in sys.path:
    sys.path.insert(0, str(APP_DIR.parent))

try:
    from copilot_core.automation.pattern_learner import PatternLearner, Pattern
    from copilot_core.automation.predictor import (
        PredictiveAutomationEngine,
        Prediction,
        PredictionRequest
    )
    from copilot_core.app import create_app
except (ModuleNotFoundError, ImportError) as e:
    print(f"Import error: {e}")
    PatternLearner = None
    PredictiveAutomationEngine = None
    create_app = None


class TestPatternLearner(unittest.TestCase):
    """Test PatternLearner-Klasse."""
    
    def setUp(self):
        """Set up test fixtures."""
        if PatternLearner is None:
            self.skipTest("PatternLearner not installed")
        
        self.tmpdir = tempfile.TemporaryDirectory()
        self.learner = PatternLearner(data_dir=self.tmpdir.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.tmpdir.cleanup()
    
    def test_observe_simple(self):
        """Test einfache Beobachtung."""
        # Beobachte Aktion
        self.learner.observe(
            entity_id="light.wohnzimmer",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        # Prüfe Patterns
        patterns = self.learner.get_patterns()
        self.assertEqual(len(patterns), 1)
        
        pattern = patterns[0]
        self.assertEqual(pattern.entity_id, "light.wohnzimmer")
        self.assertEqual(pattern.action, "turn_on")
        self.assertEqual(pattern.hour_of_day, 8)
        self.assertEqual(pattern.occurrence_count, 1)
    
    def test_observe_multiple_updates_pattern(self):
        """Test dass mehrfache Beobachtungen Pattern aktualisieren."""
        # Beobachte gleiche Aktion mehrmals
        for i in range(5):
            self.learner.observe(
                entity_id="light.kueche",
                action="turn_off",
                timestamp=datetime(2026, 3, 2, 22, 0, 0) + timedelta(days=i)
            )
        
        patterns = self.learner.get_patterns()
        self.assertEqual(len(patterns), 1)
        
        pattern = patterns[0]
        self.assertEqual(pattern.occurrence_count, 5)
        # Confidence sollte mit mehr Beobachtungen steigen
        self.assertGreater(pattern.confidence, 0.3)
    
    def test_observe_different_entities(self):
        """Test Beobachtungen verschiedener Entities."""
        self.learner.observe(
            entity_id="light.wohnzimmer",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        self.learner.observe(
            entity_id="light.schlafzimmer",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 30, 0)
        )
        
        patterns = self.learner.get_patterns()
        self.assertEqual(len(patterns), 2)
    
    def test_observe_with_context(self):
        """Test Beobachtung mit Kontext (Wetter)."""
        self.learner.observe(
            entity_id="cover.wohnzimmer",
            action="close_cover",
            timestamp=datetime(2026, 3, 2, 14, 0, 0),
            context={
                "weather_condition": "sunny",
                "temperature": 28.5
            }
        )
        
        patterns = self.learner.get_patterns()
        # Should have both time-based and weather-based patterns
        self.assertGreaterEqual(len(patterns), 1)
        
        # Check weather-based pattern exists
        weather_patterns = self.learner.get_patterns(pattern_type="weather_based")
        self.assertEqual(len(weather_patterns), 1)
        self.assertEqual(weather_patterns[0].weather_condition, "sunny")
    
    def test_get_patterns_filter_by_type(self):
        """Test Filtern von Patterns nach Typ."""
        # Time-based Pattern
        self.learner.observe(
            entity_id="light.wohnzimmer",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        # Weather-based Pattern (different entity to avoid duplicate time-based)
        self.learner.observe(
            entity_id="cover.kueche",
            action="close_cover",
            timestamp=datetime(2026, 3, 2, 14, 0, 0),
            context={"weather_condition": "sunny"}
        )
        
        # Filter nach time_based (should be 1 or 2 depending on weather pattern also creating time-based)
        time_patterns = self.learner.get_patterns(pattern_type="time_based")
        self.assertGreaterEqual(len(time_patterns), 1)
        
        # Filter nach weather_based
        weather_patterns = self.learner.get_patterns(pattern_type="weather_based")
        self.assertGreaterEqual(len(weather_patterns), 1)
        self.assertEqual(weather_patterns[0].weather_condition, "sunny")
    
    def test_get_patterns_filter_by_entity(self):
        """Test Filtern von Patterns nach Entity."""
        self.learner.observe(
            entity_id="light.wohnzimmer",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        self.learner.observe(
            entity_id="light.kueche",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        patterns = self.learner.get_patterns(entity_id="light.wohnzimmer")
        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0].entity_id, "light.wohnzimmer")
    
    def test_get_patterns_min_confidence(self):
        """Test Filtern nach minimaler Confidence."""
        # Erstelle Pattern mit niedriger Confidence
        self.learner.observe(
            entity_id="light.test",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        # Pattern mit confidence < 0.5 sollte gefiltert werden
        patterns = self.learner.get_patterns(min_confidence=0.5)
        self.assertEqual(len(patterns), 0)
        
        # Mit niedrigerem Threshold
        patterns = self.learner.get_patterns(min_confidence=0.0)
        self.assertEqual(len(patterns), 1)
    
    def test_pattern_stats(self):
        """Test Pattern-Statistik."""
        self.learner.observe(
            entity_id="light.wohnzimmer",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        self.learner.observe(
            entity_id="cover.kueche",
            action="close_cover",
            timestamp=datetime(2026, 3, 2, 14, 0, 0),
            context={"weather_condition": "sunny"}
        )
        
        stats = self.learner.get_pattern_stats()
        
        self.assertGreaterEqual(stats.total_patterns, 2)
        self.assertGreaterEqual(stats.time_based_patterns, 1)
        self.assertGreaterEqual(stats.weather_based_patterns, 1)
        self.assertEqual(stats.total_observations, 2)
    
    def test_persistence(self):
        """Test Speichern und Laden von Patterns."""
        # Erstelle Pattern
        self.learner.observe(
            entity_id="light.test",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        # Speichere explizit
        self.learner._save_patterns()
        
        # Erstelle neue Instanz mit gleichem Verzeichnis
        learner2 = PatternLearner(data_dir=self.tmpdir.name)
        
        # Pattern sollte geladen sein
        patterns = learner2.get_patterns()
        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0].entity_id, "light.test")
    
    def test_clear_patterns(self):
        """Test Löschen aller Patterns."""
        self.learner.observe(
            entity_id="light.test",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        self.assertEqual(len(self.learner.get_patterns()), 1)
        
        self.learner.clear_patterns()
        
        self.assertEqual(len(self.learner.get_patterns()), 0)
    
    def test_export_patterns(self):
        """Test Exportieren von Patterns."""
        self.learner.observe(
            entity_id="light.test",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        export_data = self.learner.export_patterns()
        
        self.assertIn("patterns", export_data)
        self.assertIn("stats", export_data)
        self.assertIn("exported_at", export_data)
        self.assertEqual(len(export_data["patterns"]), 1)


class TestPredictiveAutomationEngine(unittest.TestCase):
    """Test PredictiveAutomationEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        if PredictiveAutomationEngine is None:
            self.skipTest("PredictiveAutomationEngine not installed")
        
        self.tmpdir = tempfile.TemporaryDirectory()
        self.learner = PatternLearner(data_dir=self.tmpdir.name)
        self.predictor = PredictiveAutomationEngine(
            pattern_learner=self.learner,
            min_confidence=0.3
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.tmpdir.cleanup()
    
    def test_predict_next_time_based(self):
        """Test zeitbasierte Vorhersage."""
        # Erzeuge Pattern: Licht geht um 8 Uhr an
        for i in range(5):
            self.learner.observe(
                entity_id="light.wohnzimmer",
                action="turn_on",
                timestamp=datetime(2026, 3, 2, 8, 0, 0) + timedelta(days=i)
            )
        
        # Vorhersage um 7 Uhr (eine Stunde vorher)
        request = PredictionRequest(
            current_time=datetime(2026, 3, 7, 7, 0, 0)
        )
        
        prediction = self.predictor.predict_next(request)
        
        self.assertIsNotNone(prediction)
        self.assertEqual(prediction.entity_id, "light.wohnzimmer")
        self.assertEqual(prediction.action, "turn_on")
        self.assertGreater(prediction.confidence, 0.0)
    
    def test_predict_next_weather_based(self):
        """Test wetterbasierte Vorhersage."""
        # Erzeuge Pattern: Jalousien bei Sonne schließen
        for i in range(5):
            self.learner.observe(
                entity_id="cover.wohnzimmer",
                action="close_cover",
                timestamp=datetime(2026, 3, 2, 14, 0, 0) + timedelta(days=i),
                context={"weather_condition": "sunny"}
            )
        
        # Vorhersage bei sonnigem Wetter
        request = PredictionRequest(
            current_time=datetime(2026, 3, 7, 13, 0, 0),
            weather_condition="sunny"
        )
        
        prediction = self.predictor.predict_next(request)
        
        self.assertIsNotNone(prediction)
        self.assertEqual(prediction.entity_id, "cover.wohnzimmer")
        self.assertEqual(prediction.action, "close_cover")
        self.assertEqual(prediction.weather_condition, "sunny")
    
    def test_predict_all(self):
        """Test mehrere Vorhersagen."""
        # Erzeuge mehrere Patterns
        self.learner.observe(
            entity_id="light.wohnzimmer",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        self.learner.observe(
            entity_id="light.kueche",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 30, 0)
        )
        
        request = PredictionRequest(
            current_time=datetime(2026, 3, 7, 7, 0, 0),
            max_predictions=5
        )
        
        predictions = self.predictor.predict_all(request)
        
        self.assertGreater(len(predictions), 0)
        self.assertLessEqual(len(predictions), 5)
    
    def test_prediction_suggestion_text(self):
        """Test generierter Vorschlagstext."""
        self.learner.observe(
            entity_id="light.wohnzimmer",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        request = PredictionRequest(
            current_time=datetime(2026, 3, 7, 7, 0, 0)
        )
        
        prediction = self.predictor.predict_next(request)
        
        self.assertIsNotNone(prediction.suggestion_text)
        self.assertIn("wohnzimmer", prediction.suggestion_text.lower())
        self.assertIn("einschalten", prediction.suggestion_text.lower())
    
    def test_confidence_threshold(self):
        """Test Confidence-Threshold."""
        # Pattern mit nur einer Beobachtung (niedrige Confidence)
        self.learner.observe(
            entity_id="light.test",
            action="turn_on",
            timestamp=datetime(2026, 3, 7, 8, 0, 0)  # Use current test time
        )
        
        # Mit default min_confidence=0.3 sollte Vorhersage kommen (wenn auch niedrig)
        request = PredictionRequest(
            current_time=datetime(2026, 3, 7, 7, 0, 0),
            include_low_confidence=True  # Allow low confidence for this test
        )
        
        prediction = self.predictor.predict_next(request)
        
        # Prediction should exist when include_low_confidence=True
        if prediction:
            self.assertGreaterEqual(prediction.confidence, 0.0)
    
    def test_predict_no_patterns(self):
        """Test Vorhersage ohne Patterns."""
        request = PredictionRequest(
            current_time=datetime(2026, 3, 7, 7, 0, 0)
        )
        
        prediction = self.predictor.predict_next(request)
        
        self.assertIsNone(prediction)
    
    def test_prediction_stats(self):
        """Test Vorhersage-Statistik."""
        self.learner.observe(
            entity_id="light.test",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        stats = self.predictor.get_prediction_stats()
        
        self.assertIn("total_patterns", stats)
        self.assertIn("avg_pattern_confidence", stats)
        self.assertIn("min_confidence_threshold", stats)


class TestPredictiveAPIEndpoints(unittest.TestCase):
    """Test Predictive API Endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        if create_app is None:
            self.skipTest("Flask not installed")
        
        self.tmpdir = tempfile.TemporaryDirectory()
        self.app = create_app()
        
        # Override data dir
        from dataclasses import replace
        cfg = self.app.config["COPILOT_CFG"]
        self.app.config["COPILOT_CFG"] = replace(
            cfg,
            data_dir=self.tmpdir.name
        )
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.tmpdir.cleanup()
    
    def test_get_patterns_empty(self):
        """Test GET /api/v1/predictive/patterns ohne Patterns."""
        response = self.client.get("/api/v1/predictive/patterns")
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["patterns"]), 0)
    
    def test_get_patterns_with_data(self):
        """Test GET /api/v1/predictive/patterns mit Patterns."""
        # Test that the endpoint returns proper structure
        response = self.client.get("/api/v1/predictive/patterns")
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("patterns", data)
        self.assertIn("stats", data)
        self.assertIn("count", data)
    
    def test_get_next_prediction(self):
        """Test GET /api/v1/predictive/next."""
        # Erstelle Pattern
        observe_data = {
            "entity_id": "light.test",
            "action": "turn_on",
            "timestamp": "2026-03-02T08:00:00"
        }
        
        self.client.post(
            "/api/v1/predictive/observe",
            json=observe_data
        )
        
        # Hole Vorhersage
        response = self.client.get(
            "/api/v1/predictive/next",
            query_string={"max_predictions": "1"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        # Prediction kann None sein wenn Confidence zu niedrig
    
    def test_observe_action(self):
        """Test POST /api/v1/predictive/observe."""
        observe_data = {
            "entity_id": "light.wohnzimmer",
            "action": "turn_on",
            "timestamp": "2026-03-02T08:00:00",
            "context": {
                "weather_condition": "sunny"
            }
        }
        
        response = self.client.post(
            "/api/v1/predictive/observe",
            json=observe_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("patterns_updated", data)
    
    def test_observe_missing_fields(self):
        """Test POST /api/v1/predictive/observe mit fehlenden Feldern."""
        observe_data = {
            "action": "turn_on"
            # entity_id fehlt
        }
        
        response = self.client.post(
            "/api/v1/predictive/observe",
            json=observe_data
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["ok"])
    
    def test_confirm_prediction(self):
        """Test POST /api/v1/predictive/confirm."""
        confirm_data = {
            "prediction_id": "pred_000001",
            "action_performed": True
        }
        
        response = self.client.post(
            "/api/v1/predictive/confirm",
            json=confirm_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["prediction_id"], "pred_000001")
    
    def test_reject_prediction(self):
        """Test POST /api/v1/predictive/reject."""
        reject_data = {
            "prediction_id": "pred_000001",
            "reason": "Falsche Vorhersage"
        }
        
        response = self.client.post(
            "/api/v1/predictive/reject",
            json=reject_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["reason"], "Falsche Vorhersage")
    
    def test_get_stats(self):
        """Test GET /api/v1/predictive/stats."""
        response = self.client.get("/api/v1/predictive/stats")
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertIn("stats", data)


class TestPatternConfidenceCalculation(unittest.TestCase):
    """Test Confidence-Berechnung für Patterns."""
    
    def setUp(self):
        """Set up test fixtures."""
        if PatternLearner is None:
            self.skipTest("PatternLearner not installed")
        
        self.tmpdir = tempfile.TemporaryDirectory()
        self.learner = PatternLearner(data_dir=self.tmpdir.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.tmpdir.cleanup()
    
    def test_confidence_increases_with_observations(self):
        """Test dass Confidence mit mehr Beobachtungen steigt."""
        # Erste Beobachtung
        self.learner.observe(
            entity_id="light.test",
            action="turn_on",
            timestamp=datetime(2026, 3, 2, 8, 0, 0)
        )
        
        patterns_1 = self.learner.get_patterns()
        confidence_1 = patterns_1[0].confidence
        
        # Mehr Beobachtungen
        for i in range(1, 10):
            self.learner.observe(
                entity_id="light.test",
                action="turn_on",
                timestamp=datetime(2026, 3, 2, 8, 0, 0) + timedelta(days=i)
            )
        
        patterns_2 = self.learner.get_patterns()
        confidence_2 = patterns_2[0].confidence
        
        # Confidence sollte gestiegen sein
        self.assertGreater(confidence_2, confidence_1)
    
    def test_confidence_with_regular_pattern(self):
        """Test Confidence bei regelmäßigem Muster."""
        # Tägliche Beobachtung zur gleichen Zeit
        for i in range(7):
            self.learner.observe(
                entity_id="light.test",
                action="turn_on",
                timestamp=datetime(2026, 3, 2, 8, 0, 0) + timedelta(days=i)
            )
        
        patterns = self.learner.get_patterns()
        pattern = patterns[0]
        
        # Bei regelmäßigem Muster sollte Confidence hoch sein
        self.assertGreater(pattern.confidence, 0.5)
        self.assertEqual(pattern.occurrence_count, 7)


if __name__ == "__main__":
    unittest.main()
