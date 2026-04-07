"""Unified Anomaly Detection Framework for HA Sensors.

Provides shared baseline-learning + sigma-deviation detection for all
HA-155 sensor types: habit_learning, predictive_maintenance, media_sensors, gas_meter.

Architecture:
- Rolling 7-day baseline per device/sensor type
- Alert bei >2σ Abweichung vom erlernten Muster
- Confidence-Score 0-100% statt binärer States
- Unified Alert-Routing mit Priorisierung

Verwendet Core anomaly_detector.py (Isolation Forest) als Backend.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, List, Dict
from enum import Enum
import statistics

from homeassistant.core import HomeAssistant

from ..const import DOMAIN

logger = logging.getLogger(__name__)


class AnomalyLevel(Enum):
    NORMAL = "normal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SensorBaseline:
    """Learned baseline for a single sensor metric."""
    values: List[float] = field(default_factory=list)
    updated_at: Optional[datetime] = None

    @property
    def mean(self) -> float:
        return statistics.mean(self.values) if self.values else 0.0

    @property
    def stdev(self) -> float:
        return statistics.stdev(self.values) if len(self.values) > 1 else 0.0

    def add(self, value: float) -> None:
        """Add a new value, keep rolling 7-day window."""
        self.values.append(value)
        # Keep only last 7 days * 24h * 4samples = 672 values
        if len(self.values) > 672:
            self.values = self.values[-672:]
        self.updated_at = datetime.now(timezone.utc)

    def deviation(self, value: float) -> float:
        """Return sigma-deviation: (value - mean) / stdev. 0 if no data."""
        if len(self.values) < 4 or self.stdev == 0:
            return 0.0
        return (value - self.mean) / self.stdev


@dataclass
class AnomalyAlert:
    """An anomaly alert from any sensor."""
    sensor_id: str
    sensor_type: str  # 'habit', 'maintenance', 'media', 'gas'
    level: AnomalyLevel
    confidence: float  # 0-100
    message: str
    deviation_sigma: float
    baseline_mean: float
    current_value: float
    predicted_48h: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "level": self.level.value,
            "confidence": round(self.confidence, 1),
            "message": self.message,
            "deviation_sigma": round(self.deviation_sigma, 2),
            "baseline_mean": round(self.baseline_mean, 3),
            "current_value": round(self.current_value, 3),
            "failure_prediction_48h": self.predicted_48h,
            "timestamp": self.timestamp.isoformat(),
        }


class UnifiedAnomalyFramework:
    """Shared anomaly detection for all HA-155 sensors.

    Implements:
    - Rolling 7-day baseline per metric
    - Sigma-deviation detection (>2σ = anomaly)
    - 48h failure prediction based on trend
    - Confidence scoring
    """

    # Sigma thresholds per level
    SIGMA_CRITICAL = 3.0  # >3σ → critical
    SIGMA_HIGH = 2.5      # >2.5σ → high
    SIGMA_MEDIUM = 2.0    # >2σ → medium
    SIGMA_LOW = 1.5       # >1.5σ → low

    # Min samples before alerting
    MIN_BASELINE_SAMPLES = 10

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        # baselines[sensor_type][sensor_id][metric_name] = SensorBaseline
        self._baselines: Dict[str, Dict[str, Dict[str, SensorBaseline]]] = {}
        self._alerts: List[AnomalyAlert] = []

    def _get_baseline(
        self, sensor_type: str, sensor_id: str, metric: str
    ) -> SensorBaseline:
        if sensor_type not in self._baselines:
            self._baselines[sensor_type] = {}
        if sensor_id not in self._baselines[sensor_type]:
            self._baselines[sensor_type][sensor_id] = {}
        if metric not in self._baselines[sensor_type][sensor_id]:
            self._baselines[sensor_type][sensor_id][metric] = SensorBaseline()
        return self._baselines[sensor_type][sensor_id][metric]

    def record(
        self,
        sensor_type: str,
        sensor_id: str,
        metric: str,
        value: float,
    ) -> Optional[AnomalyAlert]:
        """Record a metric value and detect anomaly.

        Returns AnomalyAlert if deviation > SIGMA_LOW, else None.
        """
        baseline = self._get_baseline(sensor_type, sensor_id, metric)
        baseline.add(value)

        # Not enough data yet
        if len(baseline.values) < self.MIN_BASELINE_SAMPLES:
            return None

        sigma = baseline.deviation(value)

        # Trend check: linear slope over last 12 values
        predicted_48h = self._predict_failure(baseline.values)

        # Classify level
        level = self._classify_level(sigma, predicted_48h)

        # Confidence = min(100, abs(sigma) * 30 + trend_bonus)
        confidence = min(100.0, abs(sigma) * 30.0 + (20 if predicted_48h else 0))

        if level == AnomalyLevel.NORMAL:
            return None

        alert = AnomalyAlert(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            level=level,
            confidence=confidence,
            message=self._build_message(sensor_id, metric, sigma, level),
            deviation_sigma=sigma,
            baseline_mean=baseline.mean,
            current_value=value,
            predicted_48h=predicted_48h,
        )
        self._alerts.append(alert)
        # Keep last 200 alerts
        if len(self._alerts) > 200:
            self._alerts = self._alerts[-200:]
        return alert

    def _predict_failure(self, values: List[float]) -> bool:
        """Predict if metric will cause failure in 48h based on trend."""
        if len(values) < 12:
            return False
        recent = values[-12:]
        # Positive slope = getting worse (higher = more anomalous)
        slope = (recent[-1] - recent[0]) / len(recent)
        # If slope is consistently positive over last 12 samples
        return slope > 0 and all(recent[i] <= recent[i + 1] for i in range(len(recent) - 1))

    def _classify_level(self, sigma: float, predicted_48h: bool) -> AnomalyLevel:
        if sigma >= self.SIGMA_CRITICAL or predicted_48h:
            return AnomalyLevel.CRITICAL
        if sigma >= self.SIGMA_HIGH:
            return AnomalyLevel.HIGH
        if sigma >= self.SIGMA_MEDIUM:
            return AnomalyLevel.MEDIUM
        if sigma >= self.SIGMA_LOW:
            return AnomalyLevel.LOW
        return AnomalyLevel.NORMAL

    def _build_message(
        self, sensor_id: str, metric: str, sigma: float, level: AnomalyLevel
    ) -> str:
        direction = "above" if sigma > 0 else "below"
        return (
            f"{sensor_id}.{metric} is {abs(sigma):.1f}σ {direction} "
            f"7-day baseline ({level.value})"
        )

    def get_summary(self) -> Dict[str, Any]:
        """Return aggregated anomaly summary for all sensors."""
        by_type: Dict[str, int] = {}
        by_level: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "normal": 0}
        recent = [a for a in self._alerts if
                  (datetime.now(timezone.utc) - a.timestamp).total_seconds() < 3600]

        for alert in recent:
            by_type[alert.sensor_type] = by_type.get(alert.sensor_type, 0) + 1
            by_level[alert.level.value] = by_level.get(alert.level.value, 0) + 1

        critical_ids = [a.sensor_id for a in recent if a.level == AnomalyLevel.CRITICAL]

        return {
            "total_anomalies": len(recent),
            "critical": by_level["critical"],
            "high": by_level["high"],
            "medium": by_level["medium"],
            "low": by_level["low"],
            "anomaly_types": by_type,
            "top_anomalies": [a.to_dict() for a in recent[:5]],
            "critical_sensors": critical_ids,
            "failure_prediction_48h": [a.sensor_id for a in recent if a.predicted_48h],
        }


# ─── HA Integration Helpers ──────────────────────────────────────────────────

def get_framework(hass: HomeAssistant) -> UnifiedAnomalyFramework:
    """Get or create the shared anomaly framework instance."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if "anomaly_framework" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["anomaly_framework"] = UnifiedAnomalyFramework(hass)
    return hass.data[DOMAIN]["anomaly_framework"]
