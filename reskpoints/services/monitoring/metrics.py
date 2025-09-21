"""Monitoring and observability services for ReskPoints."""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
import structlog

from reskpoints.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MetricRegistry:
    """Registry for Prometheus metrics."""
    
    # Request metrics
    http_requests_total: Counter = field(default_factory=lambda: Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status_code']
    ))
    
    http_request_duration: Histogram = field(default_factory=lambda: Histogram(
        'http_request_duration_seconds',
        'HTTP request duration',
        ['method', 'endpoint']
    ))
    
    # Business metrics
    metrics_submitted_total: Counter = field(default_factory=lambda: Counter(
        'reskpoints_metrics_submitted_total',
        'Total metrics submitted',
        ['provider', 'model', 'metric_type']
    ))
    
    errors_reported_total: Counter = field(default_factory=lambda: Counter(
        'reskpoints_errors_reported_total',
        'Total errors reported',
        ['provider', 'model', 'severity', 'category']
    ))
    
    cost_tracked_total: Counter = field(default_factory=lambda: Counter(
        'reskpoints_cost_tracked_total',
        'Total cost tracked in USD',
        ['provider', 'model']
    ))
    
    active_users: Gauge = field(default_factory=lambda: Gauge(
        'reskpoints_active_users',
        'Number of active users'
    ))
    
    database_connections: Gauge = field(default_factory=lambda: Gauge(
        'reskpoints_database_connections',
        'Number of database connections',
        ['database_type']
    ))
    
    cache_operations: Counter = field(default_factory=lambda: Counter(
        'reskpoints_cache_operations_total',
        'Total cache operations',
        ['operation', 'result']
    ))
    
    anomalies_detected: Counter = field(default_factory=lambda: Counter(
        'reskpoints_anomalies_detected_total',
        'Total anomalies detected',
        ['detection_method', 'metric_type']
    ))
    
    # System info
    system_info: Info = field(default_factory=lambda: Info(
        'reskpoints_system_info',
        'System information'
    ))


class MonitoringService:
    """Central monitoring and observability service."""
    
    def __init__(self):
        self.metrics = MetricRegistry()
        self.start_time = time.time()
        self.request_latencies = defaultdict(lambda: deque(maxlen=1000))
        self.error_rates = defaultdict(lambda: deque(maxlen=100))
        
        # Initialize system info
        self.metrics.system_info.info({
            'version': '0.1.0',
            'component': 'reskpoints',
            'environment': 'development',
            'start_time': str(datetime.utcnow()),
        })
        
        logger.info("Monitoring service initialized")
    
    # HTTP request monitoring
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        self.metrics.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.metrics.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        # Store latency for analysis
        key = f"{method}:{endpoint}"
        self.request_latencies[key].append(duration)
    
    # Business metrics
    def record_metric_submission(self, provider: str, model: str, metric_type: str):
        """Record metric submission."""
        self.metrics.metrics_submitted_total.labels(
            provider=provider,
            model=model,
            metric_type=metric_type
        ).inc()
        
        logger.debug(f"Recorded metric submission: {provider}/{model}/{metric_type}")
    
    def record_error_report(self, provider: str, model: str, severity: str, category: str):
        """Record error report."""
        self.metrics.errors_reported_total.labels(
            provider=provider,
            model=model,
            severity=severity,
            category=category
        ).inc()
        
        # Track error rate
        key = f"{provider}:{model}"
        self.error_rates[key].append(time.time())
        
        logger.warning(f"Recorded error: {provider}/{model} - {severity}/{category}")
    
    def record_cost_tracking(self, provider: str, model: str, cost_usd: float):
        """Record cost tracking."""
        self.metrics.cost_tracked_total.labels(
            provider=provider,
            model=model
        ).inc(cost_usd)
        
        logger.debug(f"Recorded cost: {provider}/{model} - ${cost_usd:.4f}")
    
    def record_anomaly_detection(self, detection_method: str, metric_type: str):
        """Record anomaly detection."""
        self.metrics.anomalies_detected.labels(
            detection_method=detection_method,
            metric_type=metric_type
        ).inc()
        
        logger.warning(f"Anomaly detected: {detection_method} - {metric_type}")
    
    # System metrics
    def update_active_users(self, count: int):
        """Update active users count."""
        self.metrics.active_users.set(count)
    
    def update_database_connections(self, database_type: str, count: int):
        """Update database connections count."""
        self.metrics.database_connections.labels(database_type=database_type).set(count)
    
    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation."""
        self.metrics.cache_operations.labels(
            operation=operation,
            result=result
        ).inc()
    
    # Health and status
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health metrics."""
        uptime = time.time() - self.start_time
        
        # Calculate average latencies
        avg_latencies = {}
        for endpoint, latencies in self.request_latencies.items():
            if latencies:
                avg_latencies[endpoint] = sum(latencies) / len(latencies)
        
        # Calculate error rates
        current_time = time.time()
        error_rates = {}
        for key, timestamps in self.error_rates.items():
            # Count errors in last 5 minutes
            recent_errors = [t for t in timestamps if current_time - t < 300]
            error_rates[key] = len(recent_errors) / 5  # errors per minute
        
        return {
            "uptime_seconds": uptime,
            "timestamp": datetime.utcnow().isoformat(),
            "average_latencies": avg_latencies,
            "error_rates": error_rates,
            "system_status": "healthy" if uptime > 60 else "starting",
        }
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        return generate_latest().decode('utf-8')


class AlertManager:
    """Alert management service."""
    
    def __init__(self, monitoring_service: MonitoringService):
        self.monitoring = monitoring_service
        self.alert_rules = []
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        
        # Set up default alert rules
        self._setup_default_alerts()
        
        logger.info("Alert manager initialized")
    
    def _setup_default_alerts(self):
        """Set up default alerting rules."""
        self.alert_rules = [
            {
                "name": "high_error_rate",
                "condition": lambda metrics: self._check_error_rate(metrics),
                "severity": "warning",
                "description": "High error rate detected",
            },
            {
                "name": "high_latency",
                "condition": lambda metrics: self._check_latency(metrics),
                "severity": "warning", 
                "description": "High request latency detected",
            },
            {
                "name": "anomaly_burst",
                "condition": lambda metrics: self._check_anomaly_burst(metrics),
                "severity": "critical",
                "description": "High number of anomalies detected",
            },
        ]
    
    def _check_error_rate(self, metrics: Dict[str, Any]) -> bool:
        """Check if error rate is too high."""
        for endpoint, rate in metrics.get("error_rates", {}).items():
            if rate > 10:  # More than 10 errors per minute
                return True
        return False
    
    def _check_latency(self, metrics: Dict[str, Any]) -> bool:
        """Check if latency is too high."""
        for endpoint, latency in metrics.get("average_latencies", {}).items():
            if latency > 5.0:  # More than 5 seconds average
                return True
        return False
    
    def _check_anomaly_burst(self, metrics: Dict[str, Any]) -> bool:
        """Check for anomaly burst."""
        # This would check anomaly detection rate from metrics
        # For now, return False as placeholder
        return False
    
    async def check_alerts(self):
        """Check all alert rules."""
        metrics = self.monitoring.get_system_health()
        
        for rule in self.alert_rules:
            try:
                if rule["condition"](metrics):
                    await self._trigger_alert(rule, metrics)
            except Exception as e:
                logger.error(f"Error checking alert rule {rule['name']}: {e}")
    
    async def _trigger_alert(self, rule: Dict[str, Any], metrics: Dict[str, Any]):
        """Trigger an alert."""
        alert_id = f"{rule['name']}_{int(time.time())}"
        
        alert = {
            "id": alert_id,
            "name": rule["name"],
            "severity": rule["severity"],
            "description": rule["description"],
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "active": True,
        }
        
        # Check if this alert is already active (avoid spam)
        if rule["name"] not in self.active_alerts:
            self.active_alerts[rule["name"]] = alert
            self.alert_history.append(alert)
            
            logger.error(f"ALERT TRIGGERED: {rule['name']} - {rule['description']}")
            
            # TODO: Send to external alerting systems (email, Slack, etc.)
            await self._send_alert_notification(alert)
    
    async def _send_alert_notification(self, alert: Dict[str, Any]):
        """Send alert notification."""
        # For now, just log the alert
        # In production, this would send to email, Slack, PagerDuty, etc.
        logger.critical(f"PRODUCTION ALERT: {alert['description']} (ID: {alert['id']})")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alert history."""
        return list(self.alert_history)[-limit:]


class PerformanceProfiler:
    """Performance profiling service."""
    
    def __init__(self):
        self.profile_data = defaultdict(list)
        self.slow_queries = deque(maxlen=100)
        
    def profile_operation(self, operation_name: str, duration: float, context: Dict[str, Any] = None):
        """Profile an operation."""
        profile_entry = {
            "operation": operation_name,
            "duration": duration,
            "timestamp": time.time(),
            "context": context or {},
        }
        
        self.profile_data[operation_name].append(profile_entry)
        
        # Track slow operations
        if duration > 1.0:  # Operations taking more than 1 second
            self.slow_queries.append(profile_entry)
            logger.warning(f"Slow operation detected: {operation_name} took {duration:.2f}s")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        summary = {}
        
        for operation, entries in self.profile_data.items():
            if entries:
                durations = [e["duration"] for e in entries]
                summary[operation] = {
                    "count": len(entries),
                    "avg_duration": sum(durations) / len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "total_duration": sum(durations),
                }
        
        return {
            "operations": summary,
            "slow_queries": list(self.slow_queries),
            "total_operations": sum(len(entries) for entries in self.profile_data.values()),
        }


# Global monitoring instances
monitoring_service = MonitoringService()
alert_manager = AlertManager(monitoring_service)
performance_profiler = PerformanceProfiler()


def get_monitoring_service() -> MonitoringService:
    """Get the global monitoring service instance."""
    return monitoring_service


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    return alert_manager


def get_performance_profiler() -> PerformanceProfiler:
    """Get the global performance profiler instance."""
    return performance_profiler


# Monitoring task
async def start_monitoring_tasks():
    """Start background monitoring tasks."""
    async def monitoring_loop():
        while True:
            try:
                await alert_manager.check_alerts()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    # Start monitoring task
    asyncio.create_task(monitoring_loop())
    logger.info("Monitoring tasks started")