"""Metrics collection service with async processing and anomaly detection."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics
from collections import defaultdict, deque

import numpy as np
from sklearn.ensemble import IsolationForest

from reskpoints.models.metrics import AIMetric, AIError, ModelMetrics
from reskpoints.models.enums import MetricType, ErrorSeverity
from reskpoints.infrastructure.database.connection import get_timescale_connection
from reskpoints.infrastructure.cache.redis import get_cache
from reskpoints.core.logging import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Async metrics collector with batch processing and anomaly detection."""
    
    def __init__(self):
        self.batch_buffer: List[AIMetric] = []
        self.error_buffer: List[AIError] = []
        self.max_batch_size = 1000
        self.flush_interval = 30  # seconds
        self.anomaly_detector = AnomalyDetector()
        self._flush_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the metrics collector."""
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("Metrics collector started")
    
    async def stop(self):
        """Stop the metrics collector."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining data
        await self._flush_metrics()
        await self._flush_errors()
        logger.info("Metrics collector stopped")
    
    async def collect_metric(self, metric: AIMetric) -> bool:
        """Collect a single metric."""
        try:
            # Add to batch buffer
            self.batch_buffer.append(metric)
            
            # Check for anomalies in real-time
            await self._check_anomaly(metric)
            
            # Flush if batch is full
            if len(self.batch_buffer) >= self.max_batch_size:
                await self._flush_metrics()
            
            return True
        except Exception as e:
            logger.error(f"Error collecting metric: {e}")
            return False
    
    async def collect_error(self, error: AIError) -> bool:
        """Collect an error event."""
        try:
            # Add to error buffer
            self.error_buffer.append(error)
            
            # Trigger immediate alert for critical errors
            if error.severity == ErrorSeverity.CRITICAL:
                await self._trigger_alert(error)
            
            # Flush if batch is full
            if len(self.error_buffer) >= self.max_batch_size:
                await self._flush_errors()
            
            return True
        except Exception as e:
            logger.error(f"Error collecting error: {e}")
            return False
    
    async def _periodic_flush(self):
        """Periodically flush buffered data."""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_metrics()
                await self._flush_errors()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")
    
    async def _flush_metrics(self):
        """Flush metrics buffer to database."""
        if not self.batch_buffer:
            return
        
        try:
            async with get_timescale_connection() as conn:
                # Prepare batch insert
                values = []
                for metric in self.batch_buffer:
                    values.append((
                        metric.timestamp,
                        metric.metric_type.value,
                        metric.value,
                        metric.unit,
                        metric.provider.value,
                        metric.model_name,
                        metric.model_size.value if metric.model_size else None,
                        metric.endpoint,
                        metric.user_id,
                        metric.project_id,
                        metric.session_id,
                        metric.request_id,
                        metric.tags,
                        metric.metadata,
                    ))
                
                # Batch insert
                await conn.executemany("""
                    INSERT INTO ai_metrics (
                        timestamp, metric_type, value, unit, provider, model_name,
                        model_size, endpoint, user_id, project_id, session_id,
                        request_id, tags, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                """, values)
            
            logger.info(f"Flushed {len(self.batch_buffer)} metrics to database")
            self.batch_buffer.clear()
            
        except Exception as e:
            logger.error(f"Error flushing metrics: {e}")
    
    async def _flush_errors(self):
        """Flush errors buffer to database."""
        if not self.error_buffer:
            return
        
        try:
            async with get_timescale_connection() as conn:
                # Prepare batch insert
                values = []
                for error in self.error_buffer:
                    values.append((
                        error.timestamp,
                        error.severity.value,
                        error.category.value,
                        error.message,
                        error.code,
                        error.details,
                        error.provider.value,
                        error.model_name,
                        error.endpoint,
                        error.user_id,
                        error.project_id,
                        error.session_id,
                        error.request_id,
                        error.stack_trace,
                        error.correlation_id,
                        error.resolved,
                        error.resolution_notes,
                        error.resolved_at,
                        error.tags,
                        error.metadata,
                    ))
                
                # Batch insert
                await conn.executemany("""
                    INSERT INTO ai_errors (
                        timestamp, severity, category, message, code, details,
                        provider, model_name, endpoint, user_id, project_id,
                        session_id, request_id, stack_trace, correlation_id,
                        resolved, resolution_notes, resolved_at, tags, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                """, values)
            
            logger.info(f"Flushed {len(self.error_buffer)} errors to database")
            self.error_buffer.clear()
            
        except Exception as e:
            logger.error(f"Error flushing errors: {e}")
    
    async def _check_anomaly(self, metric: AIMetric):
        """Check if metric represents an anomaly."""
        try:
            is_anomaly = await self.anomaly_detector.detect_anomaly(metric)
            if is_anomaly:
                await self._handle_anomaly(metric)
        except Exception as e:
            logger.error(f"Error checking anomaly: {e}")
    
    async def _handle_anomaly(self, metric: AIMetric):
        """Handle detected anomaly."""
        logger.warning(f"Anomaly detected in {metric.metric_type} for {metric.provider}/{metric.model_name}: {metric.value}")
        
        # Create error event for anomaly
        error = AIError(
            severity=ErrorSeverity.MEDIUM,
            category="metric_anomaly",
            message=f"Anomalous {metric.metric_type} detected: {metric.value} {metric.unit}",
            provider=metric.provider,
            model_name=metric.model_name,
            endpoint=metric.endpoint,
            user_id=metric.user_id,
            project_id=metric.project_id,
            metadata={"anomaly_metric": metric.dict()},
        )
        
        await self.collect_error(error)
    
    async def _trigger_alert(self, error: AIError):
        """Trigger immediate alert for critical errors."""
        logger.critical(f"Critical error alert: {error.message}")
        # TODO: Implement actual alerting (email, Slack, webhook)
    
    async def get_model_metrics(
        self,
        provider: str,
        model_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> ModelMetrics:
        """Get aggregated model metrics."""
        try:
            # Check cache first
            cache = get_cache()
            cache_key = f"model_metrics:{provider}:{model_name}"
            cached_metrics = await cache.get(cache_key)
            if cached_metrics:
                return ModelMetrics(**cached_metrics)
            
            # Default time range if not specified
            if not start_time:
                start_time = datetime.utcnow() - timedelta(hours=24)
            if not end_time:
                end_time = datetime.utcnow()
            
            async with get_timescale_connection() as conn:
                # Query metrics
                metrics_query = """
                    SELECT
                        COUNT(*) as total_requests,
                        COUNT(*) FILTER (WHERE metric_type = 'error_rate' AND value = 0) as successful_requests,
                        COUNT(*) FILTER (WHERE metric_type = 'error_rate' AND value > 0) as failed_requests,
                        AVG(value) FILTER (WHERE metric_type = 'latency') as avg_latency_ms,
                        percentile_cont(0.5) WITHIN GROUP (ORDER BY value) FILTER (WHERE metric_type = 'latency') as p50_latency_ms,
                        percentile_cont(0.95) WITHIN GROUP (ORDER BY value) FILTER (WHERE metric_type = 'latency') as p95_latency_ms,
                        percentile_cont(0.99) WITHIN GROUP (ORDER BY value) FILTER (WHERE metric_type = 'latency') as p99_latency_ms,
                        AVG(value) FILTER (WHERE metric_type = 'throughput') as requests_per_second,
                        AVG(value) FILTER (WHERE metric_type = 'error_rate') as error_rate
                    FROM ai_metrics
                    WHERE provider = $1 AND model_name = $2
                    AND timestamp BETWEEN $3 AND $4
                """
                
                result = await conn.fetchrow(metrics_query, provider, model_name, start_time, end_time)
                
                # Query costs from transactions if available
                cost_query = """
                    SELECT
                        SUM(total_cost) as total_cost,
                        AVG(total_cost) as avg_cost_per_request,
                        SUM(total_tokens) as total_tokens,
                        AVG(total_tokens) as avg_tokens_per_request
                    FROM transactions
                    WHERE provider = $1 AND model_name = $2
                    AND timestamp BETWEEN $3 AND $4
                """
                
                try:
                    cost_result = await conn.fetchrow(cost_query, provider, model_name, start_time, end_time)
                except:
                    cost_result = None
            
            # Build ModelMetrics
            model_metrics = ModelMetrics(
                provider=provider,
                model_name=model_name,
                time_window_start=start_time,
                time_window_end=end_time,
                total_requests=result['total_requests'] or 0,
                successful_requests=result['successful_requests'] or 0,
                failed_requests=result['failed_requests'] or 0,
                avg_latency_ms=float(result['avg_latency_ms']) if result['avg_latency_ms'] else None,
                p50_latency_ms=float(result['p50_latency_ms']) if result['p50_latency_ms'] else None,
                p95_latency_ms=float(result['p95_latency_ms']) if result['p95_latency_ms'] else None,
                p99_latency_ms=float(result['p99_latency_ms']) if result['p99_latency_ms'] else None,
                requests_per_second=float(result['requests_per_second']) if result['requests_per_second'] else None,
                error_rate=float(result['error_rate']) if result['error_rate'] else None,
            )
            
            if cost_result:
                model_metrics.total_cost_usd = cost_result['total_cost']
                model_metrics.avg_cost_per_request = cost_result['avg_cost_per_request']
                model_metrics.total_tokens = cost_result['total_tokens']
                model_metrics.avg_tokens_per_request = cost_result['avg_tokens_per_request']
            
            # Cache the result
            await cache.set(cache_key, model_metrics.dict(), ttl=300)  # 5 minutes
            
            return model_metrics
            
        except Exception as e:
            logger.error(f"Error getting model metrics: {e}")
            # Return empty metrics on error
            return ModelMetrics(
                provider=provider,
                model_name=model_name,
                time_window_start=start_time or datetime.utcnow(),
                time_window_end=end_time or datetime.utcnow(),
            )


class AnomalyDetector:
    """Statistical and ML-based anomaly detection for metrics."""
    
    def __init__(self):
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.isolation_forests: Dict[str, IsolationForest] = {}
        self.thresholds: Dict[str, Dict[str, float]] = {}
        
    async def detect_anomaly(self, metric: AIMetric) -> bool:
        """Detect if a metric value is anomalous."""
        try:
            metric_key = f"{metric.provider}:{metric.model_name}:{metric.metric_type}"
            
            # Statistical anomaly detection first
            if await self._statistical_anomaly(metric_key, metric.value):
                return True
            
            # ML-based anomaly detection for more complex patterns
            if len(self.metric_history[metric_key]) > 50:
                return await self._ml_anomaly(metric_key, metric.value)
            
            return False
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return False
    
    async def _statistical_anomaly(self, metric_key: str, value: float) -> bool:
        """Statistical anomaly detection using moving averages and standard deviation."""
        history = self.metric_history[metric_key]
        
        # Add current value to history
        history.append(value)
        
        # Need sufficient history for statistical analysis
        if len(history) < 10:
            return False
        
        # Calculate statistics
        recent_values = list(history)[-50:]  # Last 50 values
        mean = statistics.mean(recent_values)
        std_dev = statistics.stdev(recent_values) if len(recent_values) > 1 else 0
        
        # Z-score based anomaly detection
        if std_dev > 0:
            z_score = abs(value - mean) / std_dev
            return z_score > 3.0  # 3 standard deviations
        
        return False
    
    async def _ml_anomaly(self, metric_key: str, value: float) -> bool:
        """ML-based anomaly detection using Isolation Forest."""
        try:
            history = list(self.metric_history[metric_key])
            
            # Retrain model periodically
            if metric_key not in self.isolation_forests or len(history) % 100 == 0:
                if len(history) >= 50:
                    X = np.array(history[:-1]).reshape(-1, 1)
                    model = IsolationForest(contamination=0.1, random_state=42)
                    model.fit(X)
                    self.isolation_forests[metric_key] = model
            
            # Predict anomaly
            if metric_key in self.isolation_forests:
                model = self.isolation_forests[metric_key]
                prediction = model.predict([[value]])
                return prediction[0] == -1  # -1 indicates anomaly
            
            return False
            
        except Exception as e:
            logger.error(f"Error in ML anomaly detection: {e}")
            return False


# Global metrics collector instance
metrics_collector = MetricsCollector()


async def start_metrics_collector():
    """Start the global metrics collector."""
    await metrics_collector.start()


async def stop_metrics_collector():
    """Stop the global metrics collector."""
    await metrics_collector.stop()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return metrics_collector