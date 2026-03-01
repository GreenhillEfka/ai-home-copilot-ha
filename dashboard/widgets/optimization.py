"""
Widget Performance Metrics Module
Tracks and reports performance metrics for dashboard widgets
"""
import time
from datetime import datetime
from collections import deque
from typing import Dict, List, Optional

class WidgetPerformanceTracker:
    """Track performance metrics for widgets"""
    
    def __init__(self, max_samples=100):
        self.max_samples = max_samples
        self.widgets = {}
        self.start_time = time.time()
    
    def register_widget(self, widget_name: str):
        """Register a widget for performance tracking"""
        if widget_name not in self.widgets:
            self.widgets[widget_name] = {
                'name': widget_name,
                'update_count': 0,
                'last_update': None,
                'latencies': deque(maxlen=self.max_samples),
                'render_times': deque(maxlen=self.max_samples),
                'data_sizes': deque(maxlen=self.max_samples),
                'errors': 0
            }
    
    def record_update(self, widget_name: str, latency_ms: float, data_size_bytes: int):
        """Record a widget update with performance metrics"""
        if widget_name not in self.widgets:
            self.register_widget(widget_name)
        
        widget = self.widgets[widget_name]
        widget['update_count'] += 1
        widget['last_update'] = datetime.now().isoformat()
        widget['latencies'].append(latency_ms)
        widget['data_sizes'].append(data_size_bytes)
    
    def record_render(self, widget_name: str, render_time_ms: float):
        """Record widget render time"""
        if widget_name not in self.widgets:
            self.register_widget(widget_name)
        
        self.widgets[widget_name]['render_times'].append(render_time_ms)
    
    def record_error(self, widget_name: str):
        """Record a widget error"""
        if widget_name not in self.widgets:
            self.register_widget(widget_name)
        
        self.widgets[widget_name]['errors'] += 1
    
    def get_widget_stats(self, widget_name: str) -> Optional[Dict]:
        """Get statistics for a specific widget"""
        if widget_name not in self.widgets:
            return None
        
        widget = self.widgets[widget_name]
        
        latencies = list(widget['latencies'])
        render_times = list(widget['render_times'])
        data_sizes = list(widget['data_sizes'])
        
        return {
            'name': widget_name,
            'update_count': widget['update_count'],
            'last_update': widget['last_update'],
            'avg_latency_ms': sum(latencies) / len(latencies) if latencies else 0,
            'max_latency_ms': max(latencies) if latencies else 0,
            'min_latency_ms': min(latencies) if latencies else 0,
            'p95_latency_ms': self._percentile(latencies, 95) if latencies else 0,
            'avg_render_time_ms': sum(render_times) / len(render_times) if render_times else 0,
            'avg_data_size_bytes': sum(data_sizes) / len(data_sizes) if data_sizes else 0,
            'error_count': widget['errors']
        }
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all widgets"""
        return {
            'uptime_seconds': time.time() - self.start_time,
            'widget_count': len(self.widgets),
            'widgets': {
                name: self.get_widget_stats(name)
                for name in self.widgets
            },
            'overall': self.get_overall_stats()
        }
    
    def get_overall_stats(self) -> Dict:
        """Get overall dashboard performance statistics"""
        all_latencies = []
        all_render_times = []
        total_updates = 0
        total_errors = 0
        
        for widget in self.widgets.values():
            all_latencies.extend(list(widget['latencies']))
            all_render_times.extend(list(widget['render_times']))
            total_updates += widget['update_count']
            total_errors += widget['errors']
        
        return {
            'total_updates': total_updates,
            'total_errors': total_errors,
            'avg_latency_ms': sum(all_latencies) / len(all_latencies) if all_latencies else 0,
            'avg_render_time_ms': sum(all_render_times) / len(all_render_times) if all_render_times else 0,
            'target_latency_ms': 100,
            'status': 'optimal' if (sum(all_latencies) / len(all_latencies) if all_latencies else 0) < 100 else 'degraded'
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


# Global performance tracker instance
performance_tracker = WidgetPerformanceTracker()


def get_widget_metrics(widget_name: str) -> Dict:
    """Get metrics for a specific widget"""
    stats = performance_tracker.get_widget_stats(widget_name)
    if stats:
        return {
            'status': 'success',
            'metrics': stats
        }
    return {
        'status': 'error',
        'message': f'Widget {widget_name} not found'
    }


def get_all_metrics() -> Dict:
    """Get all performance metrics"""
    return {
        'status': 'success',
        'metrics': performance_tracker.get_all_stats()
    }
