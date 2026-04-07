"""ML Context Module - Provides ML context to neurons."""

import logging
import time

_LOGGER = logging.getLogger(__name__)
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from .ml.patterns import (
    AnomalyDetector,
    HabitPredictor,
    EnergyOptimizer,
    MultiUserLearner,
)
from .ml.training import TrainingPipeline
from .ml.inference import InferenceEngine


class MLContext:
    """
    ML context provider for neurons and other components.
    
    Integrates all ML subsystems and provides a unified
    interface for pattern recognition and prediction.
    """
    
    def __init__(
        self,
        storage_path: str = "/tmp/ml_storage",
        enabled: bool = True,
    ):
        """
        Initialize ML context.
        
        Args:
            storage_path: Path for storing ML data
            enabled: Whether ML context is active
        """
        self.storage_path = Path(storage_path)
        self.enabled = enabled
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize subsystems
        self.anomaly_detector = AnomalyDetector()
        self.habit_predictor = HabitPredictor()
        self.energy_optimizer = EnergyOptimizer()
        self.multi_user_learner = MultiUserLearner()
        
        # Initialize training pipeline
        self.training_pipeline = TrainingPipeline(
            storage_path=str(self.storage_path / "training"),
        )
        
        # Initialize inference engine
        self.inference_engine = InferenceEngine(
            model_path=str(self.storage_path / "training"),
        )
        
        # Device registry
        self.device_registry: Dict[str, Dict] = {}
        
        # Context cache
        self.context_cache: Dict[str, Any] = {}
        self.context_cache_ttl = 300  # 5 minutes
        
        self._is_initialized = False
        
    def initialize(self) -> bool:
        """Initialize ML context and subsystems."""
        if not self.enabled:
            return False
            
        try:
            # Initialize anomaly detector
            self.anomaly_detector.initialize_features(
                ["power_watts", "duration_seconds", "event_rate"]
            )
            
            # Auto-register devices from the existing device registry
            for device_id, info in self.device_registry.items():
                pw = info.get("power_watts")
                dtype = info.get("device_type", "unknown")
                if pw is not None:
                    self.energy_optimizer.register_device(device_id, pw, dtype)

            # Auto-create device groups by room (derived from entity naming)
            room_groups: Dict[str, list] = {}
            for device_id in self.device_registry:
                # Extract room from entity_id (e.g. "light.living_room" → "living_room")
                parts = device_id.split(".", 1)
                if len(parts) == 2:
                    room = parts[1].rsplit("_", 1)[0] if "_" in parts[1] else parts[1]
                    room_groups.setdefault(room, []).append(device_id)
            for room, devices in room_groups.items():
                if len(devices) >= 2:
                    self.energy_optimizer.create_device_group(room, devices)
            
            self._is_initialized = True
            return True
            
        except Exception as e:
            _LOGGER.error("Failed to initialize ML context: %s", e)
            return False
            
    def register_device(
        self,
        device_id: str,
        device_type: str,
        power_watts: Optional[float] = None,
    ) -> None:
        """
        Register a device for ML monitoring.
        
        Args:
            device_id: Device identifier
            device_type: Type of device
            power_watts: Power consumption (if known)
        """
        if not self.enabled:
            return
            
        self.device_registry[device_id] = {
            "device_type": device_type,
            "power_watts": power_watts,
            "registered_at": time.time(),
        }
        
        # Register with energy optimizer
        if power_watts is not None:
            self.energy_optimizer.register_device(
                device_id, power_watts, device_type
            )
            
    def record_event(
        self,
        device_id: str,
        event_type: str,
        context: Dict[str, Any] = None,
    ) -> None:
        """
        Record an event for ML analysis.
        
        Args:
            device_id: Device identifier
            event_type: Type of event
            context: Event context
        """
        if not self.enabled or not self._is_initialized:
            return
            
        if context is None:
            context = {}
            
        # Update anomaly detector
        self.anomaly_detector.update({
            "device_id": device_id,
            "event_type": event_type,
            "timestamp": context.get("timestamp", time.time()),
        })
        
        # Update habit predictor
        self.habit_predictor.observe(
            device_id,
            event_type,
            context.get("timestamp"),
            context,
        )
        
        # Update energy optimizer
        if "power_watts" in context:
            self.energy_optimizer.record_consumption(
                device_id,
                context["power_watts"],
                context.get("duration_seconds", 0),
                context.get("timestamp"),
                context,
            )
            
        # Clear context cache
        self.context_cache.clear()
        
    def record_user_event(
        self,
        user_id: str,
        event_type: str,
        context: Dict[str, Any] = None,
    ) -> None:
        """
        Record a user event for ML analysis.
        
        Args:
            user_id: User identifier
            event_type: Type of event
            context: Event context
        """
        if not self.enabled:
            return
            
        self.multi_user_learner.record_user_event(
            user_id, event_type, context, time.time()
        )
        
    def get_anomaly_status(self) -> Dict[str, Any]:
        """Get current anomaly detection status."""
        if not self._is_initialized:
            return {"status": "not_initialized"}
            
        return {
            "status": "active",
            "summary": self.anomaly_detector.get_anomaly_summary(),
            "features": self.anomaly_detector.feature_names,
        }
        
    def get_habit_prediction(
        self,
        device_id: str,
        event_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get habit prediction for a device event.
        
        Args:
            device_id: Device identifier
            event_type: Event type
            context: Optional context for mood-aware prediction
            
        Returns:
            Habit prediction
        """
        if not self._is_initialized:
            return {"status": "not_initialized"}
            
        return self.habit_predictor.predict(device_id, event_type, context=context)
        
    def get_energy_recommendations(
        self,
        device_id: str,
        current_consumption_wh: float,
    ) -> List[Dict[str, Any]]:
        """
        Get energy optimization recommendations.
        
        Args:
            device_id: Device identifier
            current_consumption_wh: Current consumption
            
        Returns:
            List of recommendations
        """
        if not self._is_initialized:
            return []
            
        return self.energy_optimizer.generate_recommendations(
            device_id, current_consumption_wh
        )
        
    def get_multi_user_summary(self) -> Dict[str, Any]:
        """Get multi-user behavior summary."""
        if not self._is_initialized:
            return {"status": "not_initialized"}
            
        return self.multi_user_learner.get_multi_user_summary()
        
    def _get_device_consumption(self, device_id: str) -> float:
        """
        Get current power consumption for a device.

        Looks up the latest recorded consumption from the energy optimizer's
        history, falling back to the registered power_watts from the device registry.
        """
        # Try to get latest from energy optimizer's history
        try:
            history = getattr(self.energy_optimizer, "energy_history", {})
            records = history.get(device_id, [])
            if records:
                latest = records[-1]
                return float(latest.get("power_watts", 0.0))
        except (AttributeError, TypeError, IndexError):
            pass

        # Fall back to registered power_watts from device profiles
        try:
            profile = self.energy_optimizer.device_profiles.get(device_id, {})
            if profile.get("power_rating_watts"):
                return float(profile["power_rating_watts"])
        except (AttributeError, TypeError):
            pass

        # Last resort: check local device registry
        reg = self.device_registry.get(device_id)
        if reg and reg.get("power_watts"):
            return float(reg["power_watts"])

        return 0.0

    def get_ml_context(
        self,
        device_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get ML context for a device or all devices.
        
        Args:
            device_id: Optional device identifier
            
        Returns:
            ML context dictionary
        """
        if not self._is_initialized:
            return {"status": "not_initialized"}
            
        context = {
            "status": "active",
            "anomaly_status": self.get_anomaly_status(),
            "multi_user_summary": self.get_multi_user_summary(),
            "devices_registered": len(self.device_registry),
            "timestamp": time.time(),
        }
        
        if device_id is not None:
            # Resolve current consumption from device registry or recorded data
            current_wh = self._get_device_consumption(device_id)
            context["device_context"] = {
                "device_id": device_id,
                "is_monitored": device_id in self.device_registry,
                "energy_recommendations": self.get_energy_recommendations(
                    device_id, current_wh
                ),
            }
            
        return context
        
    def train_models(self) -> Dict[str, Any]:
        """Train all ML models using real subsystem data."""
        if not self.enabled or not self._is_initialized:
            return {"status": "not_ready"}

        results = {}

        # ── Anomaly Detector ──────────────────────────────────────────
        if self.anomaly_detector:
            try:
                window = self.anomaly_detector.window
                if len(window) >= 10:
                    # Convert window data to numpy array for fitting
                    import numpy as np
                    feature_names = self.anomaly_detector.feature_names
                    data_rows = []
                    for entry in window:
                        row = [float(entry.get(fn, 0.0)) for fn in feature_names]
                        data_rows.append(row)
                    data_array = np.array(data_rows)
                    self.anomaly_detector.fit(data_array)
                    results["anomaly_detector"] = {
                        "status": "trained",
                        "samples": len(window),
                        "features": feature_names,
                    }
                else:
                    results["anomaly_detector"] = {
                        "status": "insufficient_data",
                        "samples": len(window),
                        "features": self.anomaly_detector.feature_names,
                        "message": f"Need at least 10 samples, have {len(window)}",
                    }
            except Exception as e:
                _LOGGER.warning("Anomaly detector training failed: %s", e)
                results["anomaly_detector"] = {
                    "status": "error",
                    "message": str(e),
                }

        # ── Habit Predictor ───────────────────────────────────────────
        if self.habit_predictor:
            try:
                habit_training_data = []
                for device_id, events in self.habit_predictor.device_patterns.items():
                    for event in events:
                        ts = event.get("timestamp")
                        if ts is None:
                            continue
                        dt = datetime.fromtimestamp(ts)
                        habit_training_data.append({
                            "features": {
                                "hour": dt.hour,
                                "day_of_week": dt.weekday(),
                            },
                            "target": event.get("event_type", "unknown"),
                        })

                if habit_training_data:
                    # Use the training pipeline with the actual anomaly model class
                    # (IsolationForest or fallback) for habit clustering
                    self.training_pipeline.register_model(
                        "habit_predictor",
                        self.anomaly_detector.model.__class__
                        if self.anomaly_detector.model is not None
                        else type("FallbackModel", (), {
                            "__init__": lambda s, **kw: None,
                            "fit": lambda s, X: s,
                        }),
                        ["hour", "day_of_week"],
                    )
                    result = self.training_pipeline.train_model(
                        "habit_predictor", habit_training_data
                    )
                    results["habit_predictor"] = result
                else:
                    results["habit_predictor"] = {
                        "status": "no_data",
                        "message": "Collect more events to enable training",
                    }
            except Exception as e:
                _LOGGER.warning("Habit predictor training failed: %s", e)
                results["habit_predictor"] = {
                    "status": "error",
                    "message": str(e),
                }

        # ── Energy Optimizer ──────────────────────────────────────────
        if self.energy_optimizer:
            try:
                devices_tracked = len(getattr(self.energy_optimizer, "device_profiles", {}))
                savings = self.energy_optimizer.get_savings_summary()
                results["energy_optimizer"] = {
                    "status": "active",
                    "mode": "rule_based_with_stats",
                    "devices_tracked": devices_tracked,
                    "savings_summary": savings,
                    "message": "Energy optimizer uses rule-based recommendations with consumption statistics",
                }
            except Exception as e:
                results["energy_optimizer"] = {
                    "status": "error",
                    "message": str(e),
                }

        return {"status": "training_completed", "results": results}
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get ML context statistics."""
        return {
            "status": "active" if self._is_initialized else "not_initialized",
            "devices_registered": len(self.device_registry),
            "inference_engine_stats": self.inference_engine.get_statistics(),
            "training_pipeline_stats": self.training_pipeline.get_training_status(),
            "timestamp": time.time(),
        }
        
    def reset(self) -> None:
        """Reset ML context."""
        self.anomaly_detector.reset()
        self.habit_predictor.reset()
        self.energy_optimizer.reset()
        self.multi_user_learner.reset()
        self.device_registry.clear()
        self.context_cache.clear()
        self._is_initialized = False


# Global ML context instance
ml_context = MLContext()


def get_ml_context() -> MLContext:
    """Get the global ML context instance."""
    return ml_context


def initialize_ml_context() -> bool:
    """Initialize the global ML context."""
    return ml_context.initialize()
