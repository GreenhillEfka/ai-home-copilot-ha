"""Advanced Analytics — Insights, Trends, Predictions, Reports."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import time
import math

logger = logging.getLogger(__name__)


@dataclass
class Insight:
    """Analytics insight."""
    id: str
    title: str
    description: str
    category: str  # usage, efficiency, anomaly, suggestion
    confidence: float
    data_points: int
    generated_at: float = field(default_factory=lambda: time.time())
    action_items: List[str] = field(default_factory=list)


@dataclass
class Trend:
    """Trend analysis result."""
    metric: str
    direction: str  # increasing, decreasing, stable
    change_percent: float
    period_days: int
    start_value: float
    end_value: float
    forecast_7d: Optional[float] = None


@dataclass
class Report:
    """Analytics report."""
    id: str
    title: str
    period_start: float
    period_end: float
    sections: List[Dict] = field(default_factory=list)
    generated_at: float = field(default_factory=lambda: time.time())


class AdvancedAnalytics:
    """Advanced analytics engine for PilotSuite."""

    def __init__(self):
        self._metrics: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
        self._insights: List[Insight] = []
        self._reports: List[Report] = []
        self._baseline_metrics: Dict[str, float] = {}

    def record_metric(self, metric_name: str, value: float, timestamp: Optional[float] = None):
        """Record a metric data point."""
        ts = timestamp or time.time()
        self._metrics[metric_name].append((ts, value))
        
        # Keep only last 90 days
        cutoff = time.time() - (90 * 24 * 3600)
        self._metrics[metric_name] = [
            (t, v) for t, v in self._metrics[metric_name] if t >= cutoff
        ]

    def set_baseline(self, metric_name: str, value: float):
        """Set baseline for a metric."""
        self._baseline_metrics[metric_name] = value

    def analyze_trends(self, metric_name: str, period_days: int = 30) -> Optional[Trend]:
        """Analyze trends for a metric."""
        if metric_name not in self._metrics:
            return None
        
        data = self._metrics[metric_name]
        if len(data) < 2:
            return None
        
        cutoff = time.time() - (period_days * 24 * 3600)
        recent = [(t, v) for t, v in data if t >= cutoff]
        
        if len(recent) < 2:
            return None
        
        # Calculate trend
        start_value = recent[0][1]
        end_value = recent[-1][1]
        change = end_value - start_value
        change_percent = (change / max(0.001, abs(start_value))) * 100
        
        # Determine direction
        if change_percent > 5:
            direction = "increasing"
        elif change_percent < -5:
            direction = "decreasing"
        else:
            direction = "stable"
        
        # Simple linear forecast
        if len(recent) > 7:
            slope = (end_value - start_value) / len(recent)
            forecast_7d = end_value + (slope * 7)
        else:
            forecast_7d = None
        
        return Trend(
            metric=metric_name,
            direction=direction,
            change_percent=change_percent,
            period_days=period_days,
            start_value=start_value,
            end_value=end_value,
            forecast_7d=forecast_7d,
        )

    def detect_anomalies(self, metric_name: str, std_threshold: float = 2.0) -> List[Dict]:
        """Detect anomalies in metric data."""
        if metric_name not in self._metrics:
            return []
        
        data = [v for _, v in self._metrics[metric_name][-100:]]  # Last 100 points
        if len(data) < 10:
            return []
        
        # Calculate statistics
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        std = math.sqrt(variance)
        
        anomalies = []
        for i, (ts, value) in enumerate(self._metrics[metric_name][-100:]):
            z_score = (value - mean) / max(0.001, std)
            if abs(z_score) > std_threshold:
                anomalies.append({
                    "timestamp": ts,
                    "value": value,
                    "z_score": z_score,
                    "deviation": "high" if abs(z_score) > 3 else "medium",
                })
        
        return anomalies

    def generate_insights(self) -> List[Insight]:
        """Generate analytics insights."""
        insights = []
        
        # Analyze all metrics
        for metric_name in self._metrics:
            trend = self.analyze_trends(metric_name)
            if trend and trend.direction != "stable":
                insights.append(Insight(
                    id=f"insight_{metric_name}_{int(time.time())}",
                    title=f"{metric_name.replace('_', ' ').title()} Trend",
                    description=f"{metric_name} is {trend.direction} by {abs(trend.change_percent):.1f}% over {trend.period_days} days",
                    category="trend",
                    confidence=0.8,
                    data_points=len(self._metrics[metric_name]),
                    action_items=[
                        f"Review {metric_name} configuration",
                        "Consider adjusting thresholds" if trend.direction == "increasing" else "Monitor for further changes",
                    ],
                ))
            
            # Check for anomalies
            anomalies = self.detect_anomalies(metric_name)
            if anomalies:
                insights.append(Insight(
                    id=f"anomaly_{metric_name}_{int(time.time())}",
                    title=f"Anomalies Detected in {metric_name.replace('_', ' ').title()}",
                    description=f"{len(anomalies)} anomalies detected in recent data",
                    category="anomaly",
                    confidence=0.9,
                    data_points=len(anomalies),
                    action_items=[
                        "Investigate root cause",
                        "Review system logs",
                        "Consider alert threshold adjustment",
                    ],
                ))
        
        # Energy efficiency insights
        if "energy_consumption" in self._metrics and "presence" in self._metrics:
            insights.append(Insight(
                id=f"efficiency_{int(time.time())}",
                title="Energy Efficiency Opportunity",
                description="Potential energy savings detected through presence-based optimization",
                category="efficiency",
                confidence=0.75,
                data_points=100,
                action_items=[
                    "Enable presence-based lighting control",
                    "Review HVAC scheduling",
                    "Consider smart plugs for standby devices",
                ],
            ))
        
        self._insights.extend(insights)
        return insights

    def generate_report(self, title: str, period_days: int = 7) -> Report:
        """Generate analytics report."""
        period_end = time.time()
        period_start = period_end - (period_days * 24 * 3600)
        
        sections = []
        
        # Usage summary
        usage_data = {}
        for metric_name in self._metrics:
            trend = self.analyze_trends(metric_name, period_days)
            if trend:
                usage_data[metric_name] = {
                    "trend": trend.direction,
                    "change": trend.change_percent,
                    "current": trend.end_value,
                }
        
        sections.append({
            "title": "Usage Summary",
            "type": "summary",
            "data": usage_data,
        })
        
        # Top insights
        recent_insights = [i for i in self._insights if i.generated_at >= period_start][:5]
        sections.append({
            "title": "Key Insights",
            "type": "insights",
            "data": [{"title": i.title, "description": i.description} for i in recent_insights],
        })
        
        # Anomalies
        all_anomalies = []
        for metric_name in self._metrics:
            anomalies = self.detect_anomalies(metric_name)
            all_anomalies.extend(anomalies)
        
        sections.append({
            "title": "Anomalies",
            "type": "anomalies",
            "data": {"count": len(all_anomalies), "recent": all_anomalies[:10]},
        })
        
        # Forecasts
        forecasts = {}
        for metric_name in self._metrics:
            trend = self.analyze_trends(metric_name, period_days)
            if trend and trend.forecast_7d:
                forecasts[metric_name] = {
                    "current": trend.end_value,
                    "forecast_7d": trend.forecast_7d,
                }
        
        sections.append({
            "title": "7-Day Forecast",
            "type": "forecast",
            "data": forecasts,
        })
        
        report = Report(
            id=f"report_{int(time.time())}",
            title=title,
            period_start=period_start,
            period_end=period_end,
            sections=sections,
        )
        
        self._reports.append(report)
        logger.info(f"Report generated: {title} ({period_days} days)")
        
        return report

    def get_usage_stats(self, metric_name: str, period_days: int = 7) -> Dict[str, Any]:
        """Get usage statistics for a metric."""
        if metric_name not in self._metrics:
            return {}
        
        cutoff = time.time() - (period_days * 24 * 3600)
        data = [v for t, v in self._metrics[metric_name] if t >= cutoff]
        
        if not data:
            return {"count": 0}
        
        return {
            "count": len(data),
            "min": min(data),
            "max": max(data),
            "avg": sum(data) / len(data),
            "current": data[-1] if data else 0,
        }

    def get_insights(self, limit: int = 20, category: Optional[str] = None) -> List[Insight]:
        """Get generated insights."""
        insights = self._insights
        if category:
            insights = [i for i in insights if i.category == category]
        return sorted(insights, key=lambda i: i.generated_at, reverse=True)[:limit]

    def get_reports(self, limit: int = 10) -> List[Report]:
        """Get generated reports."""
        return sorted(self._reports, key=lambda r: r.generated_at, reverse=True)[:limit]

    def export_data(self, metric_names: Optional[List[str]] = None) -> Dict[str, List]:
        """Export metric data for external analysis."""
        if metric_names:
            return {name: self._metrics.get(name, []) for name in metric_names}
        return dict(self._metrics)

    def get_stats(self) -> Dict[str, Any]:
        """Get analytics statistics."""
        return {
            "metrics_tracked": len(self._metrics),
            "total_data_points": sum(len(v) for v in self._metrics.values()),
            "insights_generated": len(self._insights),
            "reports_generated": len(self._reports),
        }


# Global default advanced analytics
default_analytics: Optional[AdvancedAnalytics] = None


def init_advanced_analytics() -> AdvancedAnalytics:
    """Initialize global advanced analytics."""
    global default_analytics
    default_analytics = AdvancedAnalytics()
    return default_analytics
